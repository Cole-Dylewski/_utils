import boto3
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError
from botocore.config import Config
from typing import Dict, Any, List, Optional
import logging


import logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
from _utils.aws import boto3_session

class SNSHandler:
    """
    Initialize SecretHandler with AWS session and Secrets Manager client.
    """
    def __init__(
        self, 
        aws_access_key_id=None, 
        aws_secret_access_key=None, 
        region_name=None,
        session=None):
          
            
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
            self.dynamodb_resource = self.session.resource('dynamodb')
            self.dynamodb_client = self.session.client('dynamodb', config=retry_config)
            logger.info("Connected to AWS DynamoDB")
        except ClientError as e:
            logger.error(f"Failed to initialize DynamoDB client: {e}")
            raise
        
        # Initialize Secrets Manager client
        self.secrets_client = self.session.client(
            service_name='sns'
        )
        logger.info("Connected to AWS SNS")