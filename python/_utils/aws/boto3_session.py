import json
import os
import boto3
import logging
from botocore.exceptions import BotoCoreError, NoCredentialsError

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def Session(
        aws_access_key_id=None, 
        aws_secret_access_key=None, 
        region_name=None):
    """
    Initialize boto3 with AWS session, with enhanced error handling and logging.
    """

    # Fetching credentials from arguments, environment variables, or defaults
    args = {
        "aws_access_key_id": aws_access_key_id or os.getenv('AWS_ACCESS_KEY_ID'),
        "aws_secret_access_key": aws_secret_access_key or os.getenv('AWS_SECRET_ACCESS_KEY'),
        "region_name": region_name or os.getenv('AWS_REGION', 'us-east-1')
    }

    try:
        session = boto3.Session(
            aws_access_key_id=args["aws_access_key_id"],
            aws_secret_access_key=args["aws_secret_access_key"],
            region_name=args["region_name"]
        )
        logger.info("BOTO3 SESSION CONNECTED")
        return session
    except NoCredentialsError:
        logger.error("AWS credentials not found. Ensure they are set as environment variables or passed as arguments.")
        raise
    except BotoCoreError as e:
        logger.error(f"Failed to initialize boto3 session: {e}")
        raise
