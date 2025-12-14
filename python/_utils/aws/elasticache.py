import boto3
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError
from botocore.config import Config
from typing import Dict, Any, List, Optional
import logging

import random
import string

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Retry configuration for Elasticache operations
retry_config = Config(retries={"max_attempts": 5, "mode": "standard"})

class ElasticacheHandler:
    """
    Elasticache with AWS session management, error handling, and logging.
    """
    def __init__(
        self, 
        aws_access_key_id=None, 
        aws_secret_access_key=None, 
        region_name=None,
        session = None
    ):
        try:
            #get aws boto3 session   
            if session:
                self.session = session
            else:
                from _utils.aws import boto3_session
                self.session = boto3_session.Session(
                    aws_access_key_id=aws_access_key_id, 
                    aws_secret_access_key=aws_secret_access_key, 
                    region_name=region_name)

            self.elasticache_client = self.session.client('elasticache', config=retry_config)
            self.logs_client = self.session.client('logs')
            logger.info("Connected to AWS Elasticache")
        except ClientError as e:
            logger.error(f"Failed to initialize Elasticache client: {e}")
            raise
        
    def generate_redis_auth_token(self, length=32):
        """
        Generate a random authentication token for an AWS ElastiCache Redis instance.
        
        :param length: Length of the token, must be between 16 and 128. Default is 32.
        :return: A randomly generated auth token as a string.
        :raises ValueError: If the length is not within the valid range.
        """
        if not (16 <= length <= 128):
            raise ValueError("Token length must be between 16 and 128 characters.")
        
        # Define allowed printable ASCII characters, excluding restricted ones
        restricted_chars = {' ', '"', '/', '@', '\\'}
        allowed_chars = ''.join(
            c for c in string.printable
            if c not in restricted_chars and c.isprintable()
        )
        
        # Generate the token
        token = ''.join(random.choices(allowed_chars, k=length))
        return token