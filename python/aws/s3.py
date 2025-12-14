import os
import io
import json
import boto3
import pandas as pd
from botocore.exceptions import ClientError, NoCredentialsError, PartialCredentialsError
from typing import Union, Optional, Dict, Any, Iterator, List
from io import StringIO

import hashlib
import time, io


# Set up logging
import logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class S3Handler:
    """
    Initialize S3Handler with AWS session and S3 resource/client.
    """
    def __init__(
        self, 
        aws_access_key_id=None, 
        aws_secret_access_key=None, 
        region_name=None,
        session = None):
        
        # Initialize a session with AWS credentials
        
        #get aws boto3 session   
        if session:
            self.session = session
        else:
            from _utils.aws import boto3_session
            self.session = boto3_session.Session(
                aws_access_key_id=aws_access_key_id, 
                aws_secret_access_key=aws_secret_access_key, 
                region_name=region_name)
        self.secret_handler = False

        
        self.s3_resource = self.session.resource('s3')
        self.s3_client = self.session.client('s3')
        logger.info("Connected to AWS S3")
        
#%% META DATA       
    def s3_find_keys_containing_string(self, bucket_name: str, search_string: str) -> List[str]:
        """
        Find keys in an S3 bucket that contain a specific string.

        :param bucket_name: Name of the S3 bucket
        :param search_string: String to search for in the object keys
        :return: List of object keys containing the search string
        """
        matching_keys = []
        continuation_token = None

        try:
            while True:
                if continuation_token:
                    response = self.s3_client.list_objects_v2(Bucket=bucket_name, ContinuationToken=continuation_token)
                else:
                    response = self.s3_client.list_objects_v2(Bucket=bucket_name)

                for content in response.get('Contents', []):
                    key = content['Key']
                    if search_string.lower() in key.lower():
                        matching_keys.append(key)

                if response.get('IsTruncated'):
                    continuation_token = response.get('NextContinuationToken')
                else:
                    break

            logger.info(f"Found {len(matching_keys)} keys containing '{search_string}' in bucket '{bucket_name}'.")
            return matching_keys
        except ClientError as e:
            logger.error(f"ClientError: {e.response['Error']['Message']}")
            return []
        except Exception as e:
            logger.error(f"An error occurred while searching for keys in S3: {e}")
            return []

    def get_s3_file_metadata(self, bucket: str, key: str) -> Dict[str, Any]:
        """
        Checks if a file exists in S3 and returns its metadata including row count if applicable.

        :param bucket: Name of the S3 bucket
        :param key: The S3 object key
        :return: Dictionary containing file metadata or an error message if the file is not found
        """
        metadata: Dict[str, Any] = {}

        try:
            response = self.s3_client.head_object(Bucket=bucket, Key=key)
            size_mb = response['ContentLength'] / (1024 * 1024)

            metadata.update({
                "ResponseMetadata": response.get("ResponseMetadata"),
                "Bucket": bucket,
                "Key": key,
                "SizeMB": round(size_mb, 2),
                "LastModified": response.get("LastModified"),
                "ContentType": response.get("ContentType")
            })

            # Determine if file is probably text-based even if ContentType is binary
            file_ext = os.path.splitext(key)[1].lower()
            is_probably_text = 'text' in metadata["ContentType"] or file_ext in ['.csv', '.txt']

            if is_probably_text:
                obj = self.s3_client.get_object(Bucket=bucket, Key=key)
                body = obj['Body'].read().decode('utf-8')
                try:
                    data = pd.read_csv(StringIO(body))
                    metadata["RowCount"] = len(data)
                except Exception as parse_err:
                    metadata["RowCount"] = f"Failed to parse CSV: {parse_err}"
            else:
                metadata["RowCount"] = "Not applicable (non-text content type)"

        except self.s3_client.exceptions.NoSuchKey:
            metadata = {"Error": f"File '{key}' does not exist in bucket '{bucket}'."}
        except self.s3_client.exceptions.ClientError as e:
            if e.response['Error']['Code'] == '404':
                metadata = {"Error": f"File '{key}' not found in bucket '{bucket}'."}
            else:
                metadata = {"Error": f"ClientError: {e}"}
        except Exception as e:
            metadata = {"Error": f"Unexpected error: {e}"}

        return metadata

       
#%% EXPORT
    def send_to_s3(
        self, 
        data: Union[pd.DataFrame, str, None] = None, 
        bucket: str = '', 
        s3_file_name: str = '', 
        sheet_name: str = 'Sheet1', 
        delimiter: str = '',
        file_path: Optional[str] = None
    ) -> Optional[int]:
        """
        Uploads a DataFrame, string, or local file to an S3 bucket in various formats.

        :param data: The data to be uploaded. Can be a pandas DataFrame or a string.
        :param bucket: The name of the S3 bucket.
        :param s3_file_name: The S3 object name (including path) where the file will be stored.
        :param sheet_name: The name of the Excel sheet, if the file is an Excel file. Defaults to 'Sheet1'.
        :param delimiter: The delimiter for CSV files. Defaults to an empty string, meaning no delimiter is applied.
        :param file_path: Optional path to a local file to upload instead of raw data.
        :return: The HTTP status code from the S3 put_object response, or None if an error occurs.
        """
        try:
            name, ext = os.path.splitext(s3_file_name.lower())

            if file_path:
                with open(file_path, 'rb') as f:
                    content = f.read()
            elif isinstance(data, pd.DataFrame):
                if ext == '.xlsx':
                    buffer = io.BytesIO()
                    with pd.ExcelWriter(buffer) as writer:
                        data.to_excel(writer, sheet_name=sheet_name, index=False)
                    content = buffer.getvalue()
                elif ext == '.json':
                    content = data.to_json(orient='records').encode('utf-8')
                else:
                    buffer = io.StringIO()
                    data.to_csv(buffer, index=False, sep=delimiter or ',')
                    content = buffer.getvalue().encode('utf-8')
            elif isinstance(data, str):
                content = data.encode('utf-8')
            else:
                raise ValueError("Unsupported data type.")

            size_mb = len(content) / (1024 * 1024)
            if size_mb > 250:
                logger.info(f"Data size {size_mb:.2f} MB exceeds 250MB. Using multipart upload.")
                return self.multipart_upload(
                    bucket=bucket,
                    object_key=s3_file_name,
                    data=data if not file_path else None,
                    file_path=file_path,
                    sheet_name=sheet_name,
                    delimiter=delimiter
                )

            response = self.s3_client.put_object(Bucket=bucket, Key=s3_file_name, Body=content)
            status = response.get("ResponseMetadata", {}).get("HTTPStatusCode")
            if status == 200:
                logger.info(f"Successful S3 put_object response. Status - {status}")
            else:
                logger.error(f"Failed S3 put_object response. Status - {status}")
            return status

        except ClientError as e:
            logger.error(f"ClientError: {e.response['Error']['Message']}")
            return None
        except Exception as e:
            logger.error(f"An error occurred: {e}")
            return None

    #Take local path, bucket and folder path, uploads file and returns object key
    def upload_to_s3(self,local_file_path, bucket, s3_folder_path):
        """
        Uploads a file to an S3 bucket.

        Args:
            local_file_path (str): The path to the local file to be uploaded.
            bucket_name (str): The name of the S3 bucket.
            s3_file_path (str): The S3 path where the file will be stored.

        Returns:
            bool: True if file was uploaded, else False.
        """
        
        file_name = os.path.basename(local_file_path)
        s3_file_path = os.path.join(s3_folder_path, file_name)
        
        try:
            # Upload the file
            self.s3_client.upload_file(local_file_path, bucket, s3_file_path)
            print(f"Upload successful: {local_file_path} to s3://{bucket}/{s3_file_path}")
            return s3_file_path
        except FileNotFoundError:
            print("The file was not found.")
            return False
        except NoCredentialsError:
            print("Credentials not available.")
            return False
        except PartialCredentialsError:
            print("Incomplete credentials provided.")
            return False
        except Exception as e:
            print(f"An error occurred: {e}")
            return False

#%% IMPORT 
    def s3_to_df(self, bucket: str, object_key: str, delimiter: str = ',', chunksize: Optional[int] = None) -> Union[pd.DataFrame, Iterator[pd.DataFrame], str]:
            """
            Takes an S3 file and saves it to a DataFrame or an iterator of DataFrames for large files.

            :param bucket: The name of the S3 bucket.
            :param object_key: The S3 object key.
            :param delimiter: The delimiter for CSV files. Defaults to ','.
            :param chunksize: Number of rows per chunk if reading large CSV files. Defaults to None.
            :return: A DataFrame, an iterator of DataFrames for large files, or an error message if the file is not found.
            """
            try:
                metadata = self.s3_client.head_object(Bucket=bucket, Key=object_key)
                obj = self.s3_client.get_object(Bucket=bucket, Key=object_key)
                status = metadata.get("ResponseMetadata", {}).get("HTTPStatusCode")
                file_size_mb = metadata.get("ContentLength", 0) / (10**6)

                logger.info(f"File status: {status}, Size: {file_size_mb} MB")
                
                if status == 200:
                    name, ext = os.path.splitext(object_key.lower())
                    logger.info(f"Processing file: Name = {name}, Extension = {ext}")
                    
                    if ext == '.csv':
                        if not delimiter:
                            delimiter = ','
                        if chunksize:
                            logger.info("Reading large CSV file in chunks.")
                            return pd.read_csv(
                                obj.get("Body"),
                                dtype=str,
                                sep=delimiter,
                                na_filter=False,
                                low_memory=False,
                                chunksize=chunksize
                            )
                        else:
                            return pd.read_csv(
                                obj.get("Body"), 
                                dtype=str, 
                                sep=delimiter,
                                na_filter=False,
                                low_memory=False
                            )
                    elif ext == '.xlsx':
                        logger.info("Reading Excel file.")
                        return pd.read_excel(
                            io=obj.get("Body").read(), 
                            sheet_name=None,  # Load all sheets as a dict of DataFrames
                            dtype=str,
                            na_filter=False,
                            engine='openpyxl'
                        )
                    elif ext == '.xls':
                        logger.info("Reading older Excel file format.")
                        return pd.read_excel(
                            io=obj.get("Body").read(), 
                            sheet_name=None,  # Load all sheets as a dict of DataFrames
                            dtype=str, 
                            na_filter=False,
                            engine='xlrd'
                        )
                    else:
                        logger.error(f"Unsupported file type: {ext}")
                        return 'Unsupported file type'
                else:
                    logger.error('File not found in S3 bucket.')
                    return 'FILE NOT FOUND'
            except ClientError as e:
                logger.error(f"ClientError: {e.response['Error']['Message']}")
                return 'FILE NOT FOUND'
            except Exception as e:
                logger.error(f"An error occurred while reading from S3: {e}")
                return 'FILE NOT FOUND'

    def create_presigned_url(self, 
        bucket_name: str, 
        object_name: str, 
        access_key: str = '', 
        secret_key: str = '', 
        session_token: str = None, 
        secret: str = 'app_creds', 
        expiration: int = 3600 * 24 * 7
    ) -> Optional[str]:
        """
        Generate a presigned URL to share an S3 object using IAM User credentials
        
        :param bucket_name: Name of the S3 bucket
        :param object_name: Name of the S3 object (key)
        :param access_key: AWS IAM User Access Key
        :param secret_key: AWS IAM User Secret Key
        :param session_token: AWS IAM User Session Token (optional, for temporary credentials)
        :param expiration: Time in seconds for the presigned URL to remain valid (default is 1 Week)
        :return: Presigned URL as a string, or None if there are errors
        """

        try:
            if not (access_key and secret_key):
                if not self.secret_handler:
                    from _utils.aws import secrets
                    self.secret_handler = secrets.SecretHandler(session=self.session)
                app_creds = self.secret_handler.get_secret(secret)
                access_key = app_creds['Access key']
                secret_key = app_creds['Secret access key']

            # Create a session using the provided IAM user credentials
            temp_session = boto3.Session(
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                aws_session_token=session_token  # Optional
            )
            
            # Create an S3 client using the session
            temp_s3_client = temp_session.client('s3')

            # Generate the presigned URL for the S3 object
            response = temp_s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': bucket_name, 'Key': object_name},
                ExpiresIn=expiration
            )
            logger.info(f"Presigned URL created for {object_name} in bucket {bucket_name}.")
            return response

        except NoCredentialsError:
            logger.error("Credentials not available.")
            return None
        except Exception as e:
            logger.error(f"An error occurred while generating presigned URL: {e}")
            return None
        
    def read_s3_file(self, bucket: str, object_key: str) -> Optional[str]:
        """
        Reads an S3 file and returns its content as a string.

        :param bucket_name: Name of the S3 bucket.
        :param object_key: Key of the S3 object.
        :return: File content as a string, or None if an error occurs.
        """
        try:
            # Retrieve the S3 object
            obj = self.s3_client.get_object(Bucket=bucket, Key=object_key)
            body = obj['Body'].read().decode('utf-8')
            
            logger.info(f"Successfully read file '{object_key}' from bucket '{bucket}'.")
            return body
        except self.s3_client.exceptions.NoSuchKey:
            logger.error(f"File '{object_key}' does not exist in bucket '{bucket}'.")
            return None
        except ClientError as e:
            logger.error(f"ClientError: {e.response['Error']['Message']}")
            return None
        except Exception as e:
            logger.error(f"An error occurred while reading the S3 file: {e}")
            return None
    
    def delete_s3_file(self, bucket: str, object_key: str) -> bool:
        """
        Deletes a file from an S3 bucket.

        :param bucket: Name of the S3 bucket.
        :param object_key: Key of the S3 object to delete.
        :return: True if the file was deleted successfully, False otherwise.
        """
        try:
            self.s3_client.delete_object(Bucket=bucket, Key=object_key)
            logger.info(f"Successfully deleted file '{object_key}' from bucket '{bucket}'.")
            return True
        except ClientError as e:
            logger.error(f"ClientError: {e.response['Error']['Message']}")
            return False
        except Exception as e:
            logger.error(f"An error occurred while deleting the S3 file: {e}")
            return False
    
    def multipart_upload(
        self,        
        bucket: str,
        object_key: str,
        file_path: Optional[str] = None,
        part_size: int = 100 * 1024 * 1024,
        max_retries: int = 3,
        resume_state_file: str = 'upload_resume_state.json',
        data: Optional[Union[str, pd.DataFrame]] = None,
        sheet_name: str = 'Sheet1',
        delimiter: str = ','
    ) -> None:
        """
        Performs a resumable multipart upload to S3 with retry logic and checksum verification.

        :param file_path: Local file path to upload.
        :param bucket: Target S3 bucket.
        :param object_key: S3 object key.
        :param part_size: Size in bytes for each part. Default 100MB.
        :param max_retries: Max retry attempts for each part. Default 3.
        :param resume_state_file: File path to store upload state for resumption.
        :param data: String or DataFrame to upload instead of reading from file.
        :param sheet_name: Excel sheet name if data is a DataFrame and format is xlsx.
        :param delimiter: CSV delimiter if data is a DataFrame.
        """
        

        def calculate_sha256_bytes(data_bytes):
            hash_sha256 = hashlib.sha256()
            hash_sha256.update(data_bytes)
            return hash_sha256.hexdigest()

        def stream_s3_sha256():
            hash_sha256 = hashlib.sha256()
            response = self.s3_client.get_object(Bucket=bucket, Key=object_key)
            for chunk in iter(lambda: response['Body'].read(4096), b""):
                hash_sha256.update(chunk)
            return hash_sha256.hexdigest()

        def save_state(upload_id, parts):
            with open(resume_state_file, 'w') as f:
                json.dump({'UploadId': upload_id, 'Parts': parts}, f)

        def load_state():
            if os.path.exists(resume_state_file):
                with open(resume_state_file, 'r') as f:
                    return json.load(f)
            return None

        def clear_state():
            if os.path.exists(resume_state_file):
                os.remove(resume_state_file)

        def abort_upload(upload_id):
            try:
                self.s3_client.abort_multipart_upload(Bucket=bucket, Key=object_key, UploadId=upload_id)
                logger.info(f"Aborted multipart upload with UploadId: {upload_id}")
            except Exception as e:
                logger.error(f"Failed to abort upload: {e}")

        try:
            if data is not None:
                if isinstance(data, pd.DataFrame):
                    if object_key.lower().endswith('.xlsx'):
                        buffer = io.BytesIO()
                        with pd.ExcelWriter(buffer) as writer:
                            data.to_excel(writer, sheet_name=sheet_name, index=False)
                        data_bytes = buffer.getvalue()
                    else:
                        buffer = io.StringIO()
                        data.to_csv(buffer, index=False, sep=delimiter)
                        data_bytes = buffer.getvalue().encode('utf-8')
                elif isinstance(data, str):
                    data_bytes = data.encode('utf-8')
                else:
                    raise ValueError("Unsupported data type for upload.")
                total_size = len(data_bytes)
                read_source = io.BytesIO(data_bytes)
                sha256_fn = lambda: calculate_sha256_bytes(data_bytes)
            elif file_path:
                total_size = os.path.getsize(file_path)
                read_source = open(file_path, 'rb')
                sha256_fn = lambda: calculate_sha256_bytes(read_source.read())
                read_source.seek(0)
            else:
                raise ValueError("Either file_path or data must be provided.")

            total_parts = (total_size + part_size - 1) // part_size
            start_time = time.time()

            state = load_state()
            if state:
                upload_id = state['UploadId']
                parts = state['Parts']
                uploaded_parts = {p['PartNumber'] for p in parts}
                logger.info(f"Resuming upload with UploadId: {upload_id}")
            else:
                response = self.s3_client.create_multipart_upload(Bucket=bucket, Key=object_key)
                upload_id = response['UploadId']
                parts = []
                uploaded_parts = set()
                logger.info(f"Started new multipart upload. UploadId: {upload_id}")

            part_number = 1
            while True:
                data_chunk = read_source.read(part_size)
                if not data_chunk:
                    break

                if part_number in uploaded_parts:
                    logger.info(f"Skipping already uploaded part {part_number}")
                    part_number += 1
                    continue

                for attempt in range(1, max_retries + 1):
                    try:
                        part = self.s3_client.upload_part(
                            Body=data_chunk,
                            Bucket=bucket,
                            Key=object_key,
                            UploadId=upload_id,
                            PartNumber=part_number
                        )
                        parts.append({'PartNumber': part_number, 'ETag': part['ETag']})
                        save_state(upload_id, parts)
                        break
                    except Exception as e:
                        logger.warning(f"Attempt {attempt} failed for part {part_number}: {e}")
                        time.sleep(2 * attempt)
                else:
                    logger.error(f"Part {part_number} failed after {max_retries} attempts. Aborting upload.")
                    abort_upload(upload_id)
                    clear_state()
                    raise RuntimeError(f"Upload failed at part {part_number} after {max_retries} attempts.")

                elapsed = time.time() - start_time
                logger.info(f"Uploaded part {part_number} of {total_parts} ({(part_number / total_parts) * 100:.2f}%)")
                part_number += 1

            self.s3_client.complete_multipart_upload(
                Bucket=bucket,
                Key=object_key,
                UploadId=upload_id,
                MultipartUpload={'Parts': parts}
            )
            clear_state()
            logger.info(f"Upload completed successfully in {time.time() - start_time:.2f} seconds.")

            s3_size = self.s3_client.head_object(Bucket=bucket, Key=object_key)['ContentLength']
            logger.info(f"Verifying file size... Local: {total_size} bytes, S3: {s3_size} bytes")
            if total_size != s3_size:
                logger.warning("WARNING: File sizes do not match. Upload may be incomplete.")

            local_sha256 = sha256_fn()
            read_source.seek(0)
            s3_sha256 = stream_s3_sha256()

            logger.info(f"Local SHA256: {local_sha256}")
            logger.info(f"S3 SHA256:    {s3_sha256}")

            if local_sha256 == s3_sha256:
                logger.info("Final SHA256 checksums match. Upload integrity verified.")
                return True
            else:
                logger.error("Final SHA256 checksums do NOT match. Upload may be corrupted.")
                return False
        except (ClientError, ValueError, RuntimeError) as e:
            logger.error(f"Upload failed: {e}")
            if 'upload_id' in locals():
                logger.error("Upload incomplete. You can resume later with the same UploadId.")
            return False


