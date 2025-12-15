import logging

from botocore.config import Config
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Retry configuration for SNS operations
retry_config = Config(retries={"max_attempts": 5, "mode": "standard"})


class SNSHandler:
    """
    Initialize SecretHandler with AWS session and Secrets Manager client.
    """

    def __init__(
        self, aws_access_key_id=None, aws_secret_access_key=None, region_name=None, session=None
    ):
        try:
            # get aws boto3 session
            if session:
                self.session = session
            else:
                from aws import boto3_session

                self.session = boto3_session.Session(
                    aws_access_key_id=aws_access_key_id,
                    aws_secret_access_key=aws_secret_access_key,
                    region_name=region_name,
                )
            self.sns_client = self.session.client("sns", config=retry_config)
            logger.info("Connected to AWS SNS")
        except ClientError as e:
            logger.exception(f"Failed to initialize SNS client: {e}")
            raise
