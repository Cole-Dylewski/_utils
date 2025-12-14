import ast
import datetime as dt
from html import escape
import json
import logging
from typing import Any

from botocore.exceptions import ClientError

from _utils.aws import boto3_session, s3, secrets
from _utils.utils import git, misc, sql, teams

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class GlueHandler:
    """
    Handles AWS Glue operations: create, delete, trigger jobs, and monitor status.
    """

    def __init__(
        self,
        aws_access_key_id=None,
        aws_secret_access_key=None,
        region_name="us-east-1",
        session=None,
    ):
        # logger.info("Initializing GlueHandler...")

        self.region = region_name or "us-east-1"

        # Initialize AWS session
        if session:
            self.session = session
        else:
            self.session = boto3_session.Session(
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key,
                region_name=self.region,
            )

        # logger.info(f"Session initialized in region: {self.region}")

        # Create clients with explicit region and endpoint URL
        self.glue_client = self.session.client(
            "glue",
            region_name=self.region,
            endpoint_url=f"https://glue.{self.region}.amazonaws.com",
        )
        # logger.info("Glue client created")

        self.logs_client = self.session.client("logs", region_name=self.region)
        # logger.info("CloudWatch Logs client created")

        # Lazy initialization for handlers
        self.s3_handler = s3.S3Handler(session=self.session)
        # logger.info("S3 Handler created")

        self.secret_handler = secrets.SecretHandler(session=self.session)
        # logger.info("Secrets Handler created")

        logger.info("GlueHandler initialization complete")

    # -------------------------------------
    # Glue Job Management Methods
    # -------------------------------------
    def get_current_glue_job_metadata(self, job_name: str):
        """
        Retrieves the metadata for the current Glue job.
        The JOB_NAME is automatically passed as an environment variable.
        Returns a dictionary containing the Glue job metadata.
        """
        print("GETTING JOB META DATA FOR", job_name)

        # Extract the job name from the environment variables

        if not job_name:
            raise ValueError(
                "JOB_NAME environment variable not set. Ensure this script runs inside a Glue job."
            )

        try:
            response = self.glue_client.get_job(JobName=job_name)
            return response.get("Job", {})
        except Exception as e:
            print(f"Error retrieving metadata for job '{job_name}': {e}")
            return {}

    def delete_job(self, job_name: str):
        """
        Deletes a Glue job by name.
        """
        try:
            response = self.glue_client.delete_job(JobName=job_name)
            logger.info(f"Job {job_name} deleted successfully: {response}")
        except ClientError as e:
            logger.exception(f"Failed to delete job {job_name}: {e}")
            raise

    def create_glue_job(
        self,
        job_name: str,
        role: str,
        source_control_details: dict | None = None,
        script_location: str = "",
        bucket_name="",
        extra_py_files="",
        additional_python_modules="",
        maxConcurrentRuns=1,
        connection_name="Network connection",
        timeout=2880,
        GlueVersion="5.0",
        WorkerType="G.1X",
        NumberOfWorkers=10,
        maxRetries=0,
        print_file=False,
        github_token_secret_name="",
    ):
        """
        Creates a new Glue job with the specified parameters.

        :param github_token_secret_name: Name of the AWS Secrets Manager secret containing the GitHub token (required if source_control_details is provided).
        """
        if source_control_details is None:
            source_control_details = {}
        logger.info(f"Creating Glue job: {job_name}")

        create_args = {
            "Name": job_name,
            "Role": role,
            "ExecutionProperty": {"MaxConcurrentRuns": maxConcurrentRuns},
            "Command": {"Name": "glueetl", "PythonVersion": "3"},
            "DefaultArguments": {
                "--TempDir": f"s3://{bucket_name}/temp/",
                "--job-language": "python",
                "--extra-py-files": extra_py_files,
                "--additional-python-modules": additional_python_modules,
                "--enable-continuous-cloudwatch-log": "true",
            },
            "MaxRetries": maxRetries,
            "Timeout": timeout,
            "GlueVersion": GlueVersion,
            "WorkerType": WorkerType,
            "NumberOfWorkers": NumberOfWorkers,
        }

        if connection_name:
            create_args["Connections"] = {"Connections": [connection_name]}

        # Source control logic: pulling script from GitHub and uploading to S3
        if source_control_details:
            if not github_token_secret_name:
                raise ValueError(
                    "github_token_secret_name parameter is required when source_control_details is provided"
                )
            github_pat = self.secret_handler.get_secret(github_token_secret_name).get("Token")
            file_contents = git.download_file(
                repository=source_control_details.get("Repository"),
                filepath=source_control_details.get("Folder"),
                branch=source_control_details.get("Branch"),
                token=github_pat,
            )

            if print_file:
                print("FILE PRINTING")
                print(file_contents)

            logger.info(f"Downloaded script from GitHub: {source_control_details}")

            s3_path = (
                f"{source_control_details.get('Repository')}/{source_control_details.get('Folder')}"
            )
            script_location = f"s3://{bucket_name}/{s3_path}"

            self.s3_handler.send_to_s3(data=file_contents, bucket=bucket_name, s3_file_name=s3_path)

        create_args["Command"]["ScriptLocation"] = script_location

        try:
            create_response = self.glue_client.create_job(**create_args)
            logger.info(f"Created Glue job: {create_response['Name']}")
        except ClientError as e:
            logger.exception(f"Failed to create Glue job {job_name}: {e}")
            raise

    def trigger_glue_job(self, job_name: str, job_args: str | dict[str, Any] | None = None) -> str:
        """
        Triggers a Glue job and returns the Job Run ID.
        """
        logger.info(f"Triggering Glue job: {job_name}")

        try:
            if isinstance(job_args, str):
                try:
                    job_args = json.loads(job_args)
                except json.JSONDecodeError as e:
                    logger.exception(f"Invalid JSON string for job_args: {e}")
                    raise ValueError("job_args must be a valid JSON string or a dictionary.")

            # Ensure all job arguments are strings
            if job_args:
                job_args = {
                    k: json.dumps(v) if not isinstance(v, str) else v for k, v in job_args.items()
                }

            response = self.glue_client.start_job_run(JobName=job_name, Arguments=job_args or {})
            job_run_id = response["JobRunId"]
            logger.info(f"Successfully triggered Glue job {job_name}. Job Run ID: {job_run_id}")
            return job_run_id

        except ClientError as e:
            logger.exception(f"Failed to trigger Glue job {job_name}: {e}")
            raise

    async def monitor_glue_job(
        self, job_name: str, job_run_id: str, interval: int = 30
    ) -> dict[str, Any]:
        import asyncio

        """
        Asynchronously monitors a Glue job until completion and returns logs.
        """
        logger.info(f"Monitoring Glue job {job_name} with run ID {job_run_id}")

        while True:
            try:
                response = self.glue_client.get_job_run(JobName=job_name, RunId=job_run_id)
                job_status = response["JobRun"]["JobRunState"]

                logger.info(f"Job {job_name} with Run ID {job_run_id} status: {job_status}")

                if job_status in ["SUCCEEDED", "FAILED", "STOPPED"]:
                    logs = self.get_job_logs(job_name=job_name, job_run_id=job_run_id)

                    return {
                        "JobName": job_name,
                        "JobRunId": job_run_id,
                        "Status": job_status,
                        "Logs": logs,
                    }

                await asyncio.sleep(interval)

            except ClientError as e:
                logger.exception(f"Error checking Glue job status: {e}")
                raise

    # -------------------------------------
    # CloudWatch Logs Helpers
    # -------------------------------------

    def generate_logstream_urls(self, job_name, job_run_id) -> dict:
        """
        Generates CloudWatch Logs console URLs for both output and error log streams for a Glue job run.

        Returns:
            dict: {
                'output': <output_log_url> or None,
                'error': <error_log_url> or None
            }
        """
        try:
            log_stream_name = self.get_logstream_name(job_name, job_run_id)

            if not log_stream_name:
                logger.warning("No log stream found for the given job run.")
                return {"output": None, "error": None}

            base_url = f"https://{self.region}.console.aws.amazon.com/cloudwatch/home?region={self.region}#logsV2:log-groups/log-group"

            output_url = (
                f"{base_url}/$252Faws-glue$252Fjobs$252Foutput/log-events/{log_stream_name}"
            )

            error_url = f"{base_url}/$252Faws-glue$252Fjobs$252Ferror/log-events/{log_stream_name}"

            return {"output": output_url, "error": error_url}

        except Exception as e:
            logger.exception(f"Error generating log stream URLs: {e}")
            return {"output": None, "error": None}

    def get_logstream_name(self, job_name, job_run_id):
        """
        Retrieves the CloudWatch log stream name for the job run.
        """
        try:
            response = self.glue_client.get_job_run(JobName=job_name, RunId=job_run_id)
            return response["JobRun"].get("Id")  # RunId typically doubles as log stream name
        except Exception as e:
            logger.exception(f"Error retrieving log stream name: {e}")
            return None

    def get_job_logs(self, job_name, job_run_id) -> dict:
        """
        Retrieves logs for a Glue job run from CloudWatch Logs.
        """
        log_groups = {"errors": "/aws-glue/jobs/error", "output": "/aws-glue/jobs/output"}
        logs = {}

        for log_type, log_group in log_groups.items():
            log_stream_name = self.get_logstream_name(job_name, job_run_id)

            if not log_stream_name:
                logger.warning(f"No log stream found in {log_group} for job run {job_run_id}.")
                continue

            logger.info(f"Retrieving logs from {log_group}, log stream: {log_stream_name}")

            try:
                events = self.logs_client.get_log_events(
                    logGroupName=log_group, logStreamName=log_stream_name, startFromHead=True
                )

                log_messages = [event["message"].strip() for event in events.get("events", [])]
                logs[log_type] = log_messages

            except Exception as e:
                logger.exception(f"Error retrieving logs from {log_group}: {e}")

        return logs

    def log_job(self, job_meta_data, error=""):
        print("job_meta_data")
        job_meta_data = {k.lower(): v for k, v in job_meta_data.items()}
        for k, v in job_meta_data.items():
            print(k, v)
        job_run_id = job_meta_data["JOB_RUN_ID".lower()]
        job_name = job_meta_data["JOB_NAME".lower()]

        sql_response = sql.run_sql(
            query=f"""select * from glue.logs where job_run_id = '{job_run_id}';""",  # SQL string or list of SQL strings
            queryType="query",  # Type of query: 'query' or 'execute'
            dbname="dev",
            rds="redshift",
        )
        # print('sql_response',sql_response)

        if sql_response.empty:
            if error:
                job_meta_data["job_error"] = json.dumps(error)
            log_insert_stmt = sql.dict_to_insert_stmt(
                data=job_meta_data, schema="glue", table="logs"
            )
            print(log_insert_stmt)
            insert_response = sql.run_sql(
                query=log_insert_stmt,  # SQL string or list of SQL strings
                queryType="execute",  # Type of query: 'query' or 'execute'
                dbname="dev",
                rds="redshift",
            )
            print("insert_response", insert_response)

        else:
            job_end = dt.datetime.now()
            job_start = sql_response.to_dict("records")[0].get("job_start")
            job_uuid = sql_response.to_dict("records")[0].get("uuid")
            job_duration = job_end - job_start
            print("job_start", type(job_start), job_start)

            if error:
                error = json.dumps(error).replace("'", "''") if error else ""

            log_insert_stmt = f"""update glue.logs
    set
        job_end = '{job_end.strftime("%Y-%m-%d %H:%M:%S")}',
        job_duration = '{job_duration}',
        job_completed = {str(not bool(error)).upper()},
        job_error = '{error}',
        error_resolved = false
    where uuid = '{job_uuid}';"""
            # print(log_insert_stmt)

            insert_response = sql.run_sql(
                query=log_insert_stmt,  # SQL string or list of SQL strings
                queryType="execute",  # Type of query: 'query' or 'execute'
                dbname="dev",
                rds="redshift",
            )
            print("insert_response", insert_response)

        if error:
            error_pretty = escape(json.dumps(error, indent=2))
            output_url = job_meta_data.get("output_url".lower(), "")
            error_url = job_meta_data.get("error_url".lower(), "")
            teams.send_teams_notification(
                channel="teams_webhook_errorchannel",
                premsg=f"GLUE JOB {job_name} FAILED",
                postmsg=f"""GLUE JOB ERROR:
            Error:{error_pretty}
            Output URL: {output_url}
            Error URL: {error_url}
            """,
            )

    def process_input(self, argv: dict):
        """
        Splits sys.argv from a Glue job into metadata arguments and input arguments.

        Args:
            argv (list): The sys.argv list from the Glue job.

        Returns:
            Tuple[dict, dict]: A tuple (meta_args, input_args)
                - meta_args: arguments where the key starts with '--'
                - input_args: arguments where the key does NOT start with '--'
        """
        job_meta_data = {"log_id": misc.get_uuid()}
        job_args = {}
        print("ARG TO DICT")
        argv = self.argv_to_dict(argv=argv)
        print("argv")
        for k, v in argv.items():
            print(k, v)

        # print('it',it)
        print("FOR LOOP?")
        for key, value in argv.items():
            print(key)

            if key.startswith("--"):
                print("THIS KEY IS META DATA", key, key[2:].lower(), value)
                if key.lower() in [
                    "--log_id",
                    "--job_id",
                    "--job_run_id",
                    "--job_name",
                    "--tempdir",
                ]:
                    job_meta_data[key[2:].lower()] = value
            else:
                job_args[key] = value

        print("JOB ARGS", job_args)
        print("job_meta_data", job_meta_data)

        print("UPDATES")
        meta_dict = misc.flatten_dict(
            self.get_current_glue_job_metadata(job_name=job_meta_data.get("job_name"))
        )
        print("META DICT", meta_dict)
        job_meta_data.update(
            {
                k.lower(): v
                for k, v in misc.flatten_dict(
                    self.get_current_glue_job_metadata(job_name=job_meta_data.get("job_name"))
                ).items()
            }
        )
        print("here?")
        job_meta_data.update(
            {
                k + "_url": v
                for k, v in self.generate_logstream_urls(
                    job_name=job_meta_data.get("job_name"),
                    job_run_id=job_meta_data.get("job_run_id"),
                ).items()
            }
        )
        job_meta_data["args"] = json.dumps(job_args)
        job_meta_data["job_start"] = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print("idk")
        keys = list(job_meta_data.keys())
        vals = list(job_meta_data.values())
        print("lists complete?")

        normalized_keys = sql.normalize_col_names(keys)
        print("KEYS NORMALIZED!", keys, normalized_keys)
        job_meta_data = {key: vals[i] for i, key in enumerate(sql.normalize_col_names(keys))}

        print("ALL DONE")
        return job_meta_data, job_args

    # Utility function for argument conversion (optional)
    def argv_to_dict(self, argv):
        """
        Converts a list of CLI-style arguments into a dictionary.
        Handles stringified lists/dicts, booleans, ints, and floats.
        """
        # Remove the first script argument if odd number of args
        if len(argv) % 2 != 0:
            argv = argv[1:]

        it = iter(argv)
        result = {}

        for key, value in zip(it, it, strict=False):
            val_lower = value.strip().lower()

            # Convert string booleans
            if val_lower == "true":
                parsed_value = True
            elif val_lower == "false":
                parsed_value = False
            else:
                try:
                    # Safely evaluate lists, dicts, numbers, etc.
                    parsed_value = ast.literal_eval(value)
                except (ValueError, SyntaxError):
                    parsed_value = value  # leave as string if not parseable

            result[key] = parsed_value

        return result
