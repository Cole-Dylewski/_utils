import asyncio, httpx, json
from typing import Optional, Dict, Any, Union, List
import requests
from _utils.aws import secrets

# Common request function parameters
def _prepare_request_params(
    method: str,
    url: str,
    params: Optional[Dict[str, Any]] = None,
    data: Optional[Union[Dict[str, Any], str]] = None,
    json: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
    timeout: Optional[float] = None,
    **kwargs
):
    return {
        "method": method,
        "url": url,
        "params": params,
        "data": data,
        "json": json,
        "headers": headers,
        "timeout": timeout,
        **kwargs
    }

# Asynchronous function to send a request
async def send_async_request(
    method: str,
    url: str,
    params: Optional[Dict[str, Any]] = None,
    data: Optional[Union[Dict[str, Any], str]] = None,
    json: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
    timeout: Optional[float] = None,
    **kwargs
) -> httpx.Response:
    request_params = _prepare_request_params(method, url, params, data, json, headers, timeout, **kwargs)
    
    async with httpx.AsyncClient() as client:
        response = await client.request(**request_params)
    return response

# Synchronous function to send a request
def send_sync_request(
    method: str,
    url: str,
    params: Optional[Dict[str, Any]] = None,
    data: Optional[Union[Dict[str, Any], str]] = None,
    json: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
    timeout: Optional[float] = None,
    **kwargs
) -> httpx.Response:
    request_params = _prepare_request_params(method, url, params, data, json, headers, timeout, **kwargs)
    
    with httpx.Client() as client:
        response = client.request(**request_params)
    return response

async def run_async_requests_in_parallel(requests: List[Dict[str, Any]]) -> List[httpx.Response]:
    tasks = [
        send_async_request(**request_args) for request_args in requests
    ]
    # Gather all tasks to run them concurrently
    responses = await asyncio.gather(*tasks, return_exceptions=True)
    return responses

def aws_api_request(
    functionName, #AWS Lambda Func Name
    client, #client name (required)
    invocationType = 'RequestResponse', #RequestResponse or Event
    stage = 'PROD', #PROD
    body = {},
    gatewayID = '',
    apiKey = '',#dictionary
    api_creds_secret_name = ''
):
    

    if (not gatewayID) and (not apiKey):
        if not api_creds_secret_name:
            raise ValueError("api_creds_secret_name parameter is required when gatewayID and apiKey are not provided")
        secret_handler = secrets.SecretHandler()
        api_creds_secret = secret_handler.get_secret(api_creds_secret_name)
        apiCreds = json.loads(api_creds_secret[client.lower()])[stage.upper()]
        # print(apiCreds)
        gatewayID = apiCreds['id']
        apiKey = apiCreds['key']
    # print(apiCreds)
    
    for k,v in apiCreds.items():
        if client.lower() == k.lower():
            creds  = json.loads(v)[stage.upper()]
    # print(creds)
    url = f"https://{gatewayID}.execute-api.us-east-1.amazonaws.com/{stage.upper()}/{client.lower()}"
    # print(url)
    
    body = json.dumps(body)
    
    headers = {
        'FunctionName': functionName,
        'InvocationType': invocationType,
        'x-api-key': apiKey,
        'Content-Type': 'application/json'
    }
    
    # print(url)
    response =  requests.request("POST", url, headers=headers, data=body)
    # print('RESPONSE',response.text)
    return response

async def run_async_requests_in_sequence(requests: List[Dict[str, Any]]) -> List[httpx.Response]:
    responses = []
    
    for request_args in requests:
        try:
            response = await send_async_request(**request_args)
            responses.append(response)
        except Exception as e:
            responses.append(e)  # Capture exceptions to maintain response order
    
    return responses


# %%

def upload_part(bucket_name, object_key, upload_id, part_number, data):
    response = s3_client.upload_part(
        Bucket=bucket_name,
        Key=object_key,
        PartNumber=part_number,
        UploadId=upload_id,
        Body=data
    )
    print('Upload Part', response)
    return response['ETag']

def complete_multipart_upload_sdk(bucket_name, object_key, upload_id, parts):
    # Use boto3's SDK to complete the multipart upload
    print('Parts', parts)
    response = s3_client.complete_multipart_upload(
        Bucket=bucket_name,
        Key=object_key,
        UploadId=upload_id,
        MultipartUpload={'Parts': parts}
    )
    return response

def multipart_upload_to_s3(file_path, bucket_name, folder_path, client):
    
    
    upload_id = initiate_multipart_upload(bucket_name, folder_path , os.path.basename(file_path), client)
    print('upload_id', upload_id)
    chunk_size = 100 * 1024 * 1024  # 100 MB
    object_key = f'{folder_path}/{os.path.basename(file_path)}'
    parts = []

    try:
        with open(file_path, 'rb') as file:
            file_size = os.path.getsize(file_path)
            part_number = 0
            numParts = file_size/chunk_size
            print('# NUMBER OF PARTS:', file_size, chunk_size, file_size/chunk_size, math.ceil(numParts))
            for _ in range(0, file_size, chunk_size):
                # print('_', _)
                part_number += 1
                data = file.read(chunk_size)
                etag = upload_part(bucket_name, object_key, upload_id, part_number, data)
                parts.append({'PartNumber': part_number, 'ETag': etag})
                
            print('TOTAL NUMBER OF PARTS:', part_number)
        response = complete_multipart_upload_sdk(bucket_name, object_key, upload_id, parts)
        if response['ResponseMetadata']['HTTPStatusCode'] == 200:
            print("Multipart upload completed successfully.")
            return True
        else:
            print(f"Failed to complete multipart upload. Status code: {response['ResponseMetadata']['HTTPStatusCode']}")
            return False

    except Exception as e:
        print("An error occurred:", e)
        return False