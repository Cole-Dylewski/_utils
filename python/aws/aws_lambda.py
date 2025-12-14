import json
import logging
import os
from typing import Any

import boto3
from botocore.exceptions import ClientError

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Force regional STS resolution
os.environ["AWS_STS_REGIONAL_ENDPOINTS"] = "regional"
print("[GLOBAL] AWS_STS_REGIONAL_ENDPOINTS set to 'regional'")


lambda_client = boto3.client("lambda")
# ========== FUNCTIONAL UTILITIES ==========


def invoke_lambda(
    function_name: str,
    invocation_type: str = "RequestResponse",
    payload: dict[str, Any] | None = None,
    qualifier: str = "$LATEST",
    lambda_client: Any | None = lambda_client,
    region: str = "us-east-1",
):
    if payload is None:
        payload = {}

    print(
        f"[invoke_lambda] Invoking {function_name} with type {invocation_type} and qualifier {qualifier}"
    )
    try:
        response = lambda_client.invoke(
            FunctionName=function_name,
            InvocationType=invocation_type,
            Payload=json.dumps(payload),
            Qualifier=qualifier,
        )
        print("[invoke_lambda] Invocation successful")
        return response
    except ClientError as e:
        print(f"[invoke_lambda] Error: {e.response['Error']['Message']}")
        return None


def context_to_json(context):
    print("[context_to_json] Converting context")
    return {
        "function_name": context.function_name,
        "function_version": context.function_version,
        "invoked_function_arn": context.invoked_function_arn,
        "memory_limit_in_mb": context.memory_limit_in_mb,
        "aws_request_id": context.aws_request_id,
        "log_stream_name": context.log_stream_name,
        "log_group_name": context.log_group_name,
    }


def get_log_link(context):
    print("[get_log_link] Generating log link")
    if isinstance(context, dict):
        region = context["invoked_function_arn"].split(":")[3]
        log_stream_name = (
            context["log_stream_name"]
            .replace("$", "$2524")
            .replace("/", "$252F")
            .replace("[", "$255B")
            .replace("]", "$255D")
        )
        log_group_name = f"$252Faws$252Flambda$252F{context['function_name']}"
    else:
        region = context.invoked_function_arn.split(":")[3]
        log_stream_name = (
            context.log_stream_name.replace("$", "$2524")
            .replace("/", "$252F")
            .replace("[", "$255B")
            .replace("]", "$255D")
        )
        log_group_name = context.log_group_name.replace("/", "$252F")

    return f"https://{region}.console.aws.amazon.com/cloudwatch/home?region={region}#logsV2:log-groups/log-group/{log_group_name}/log-events/{log_stream_name}"


# ========== OPTIONAL HANDLER CLASS ==========


class LambdaHandler:
    def __init__(
        self,
        aws_access_key_id=None,
        aws_secret_access_key=None,
        region_name="us-east-1",
        session=None,
    ):
        print("[INIT] Starting LambdaHandler __init__")
        self.region = region_name or "us-east-1"

        if session:
            print("[INIT] Using provided session object")
            self.session = session
        else:
            print("[INIT] Importing boto3_session from _utils")
            from _utils.aws import boto3_session

            self.session = boto3_session.Session(
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key,
                region_name=self.region,
            )
        print("[INIT] SESSION CREATED")

        env_keys = [key.lower() for key in os.environ]
        if "glue_python_version" in env_keys:
            self.env = "glue"
        elif "aws_lambda_function_version" in env_keys:
            self.env = "lambda"
        else:
            self.env = "local"
        print(f"[INIT] Environment determined: {self.env}")
        if self.env == "lambda":
            print("[INIT] Lambda environment detected")
            print("[INIT] Using default boto3 session")
            self.lambda_client = boto3.client("lambda", region_name=self.region)
        elif session:
            print("[get_lambda_client] Using provided session")
            self.lambda_client = session.client("lambda", region_name=self.region)
        else:
            print("[get_lambda_client] Creating default boto3 client")
            self.lambda_client = boto3.client("lambda", region_name=self.region)
        # get_lambda_client(region=self.region, session=self.session)
        print("[INIT] Lambda client initialized")

    def invoke_lambda(self, *args, **kwargs):
        print("[LambdaHandler] invoke_lambda")
        return invoke_lambda(*args, lambda_client=self.lambda_client, **kwargs)

    def context_to_json(self, context):
        return context_to_json(context)

    def get_log_link(self, context):
        return get_log_link(context)
