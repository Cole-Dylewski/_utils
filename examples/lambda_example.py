"""
AWS Lambda example using _utils.

Demonstrates Lambda function with AWS integrations and error handling.
"""

import json
from typing import Any

from _utils.aws import s3, secrets
from _utils.aws.aws_lambda import LambdaHandler
from _utils.exceptions import AWSConnectionError, AWSOperationError
from _utils.utils.logger import get_logger

# Initialize logger
logger = get_logger(__name__, use_json=True)


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    AWS Lambda handler function.

    Args:
        event: Lambda event data
        context: Lambda context

    Returns:
        Response dictionary
    """
    try:
        logger.info("Lambda function invoked", extra={"function_name": context.function_name})

        # Example: Get secret from AWS Secrets Manager
        secret_name = event.get("secret_name")
        if secret_name:
            try:
                secret_value = secrets.get_secret(secret_name)
                logger.info("Secret retrieved", extra={"secret_name": secret_name})
            except AWSOperationError as e:
                logger.exception("Failed to retrieve secret", extra={"error": str(e)})
                return {
                    "statusCode": 500,
                    "body": json.dumps({"error": f"Secret retrieval failed: {e}"}),
                }

        # Example: S3 operation
        bucket = event.get("bucket")
        key = event.get("key")
        if bucket and key:
            try:
                handler = s3.S3Handler()
                # Perform S3 operation
                logger.info("S3 operation completed", extra={"bucket": bucket, "key": key})
            except AWSConnectionError as e:
                logger.exception("S3 connection failed", extra={"error": str(e)})
                return {
                    "statusCode": 503,
                    "body": json.dumps({"error": f"S3 connection failed: {e}"}),
                }

        return {
            "statusCode": 200,
            "body": json.dumps({"message": "Lambda function executed successfully"}),
        }

    except Exception as e:
        logger.exception("Lambda function error", extra={"error": str(e)})
        return {
            "statusCode": 500,
            "body": json.dumps({"error": f"Internal error: {e}"}),
        }


# Example usage with LambdaHandler
def example_lambda_handler() -> None:
    """Example of using LambdaHandler utility."""
    handler = LambdaHandler()

    # Invoke another Lambda function
    response = handler.invoke_lambda(
        function_name="my-function",
        payload={"key": "value"},
    )

    logger.info("Lambda invoked", extra={"response": response})
