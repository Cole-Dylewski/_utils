import json
import os
import boto3


import logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class SecretHandler:
    """
    Initialize SecretHandler with AWS session and Secrets Manager client.
    """
    def __init__(
        self, 
        aws_access_key_id=None, 
        aws_secret_access_key=None, 
        region_name=None,
        session = None,):
          
            
        #get aws boto3 session   
        if session:
            self.session = session
        else:
            from _utils.aws import boto3_session
            self.session = boto3_session.Session(
                aws_access_key_id=aws_access_key_id, 
                aws_secret_access_key=aws_secret_access_key, 
                region_name=region_name)
        
        
        # Initialize Secrets Manager client
        self.secrets_client = self.session.client(
            service_name='secretsmanager'
        )
        logger.info("Connected to AWS Secrets Manager")
    
    
    def check_secret_exists(self, secret_name):
        """
        Check if a secret exists in AWS Secrets Manager.

        :param secret_name: Name of the secret to check
        :return: True if secret exists, False otherwise
        """
        try:
            self.secrets_client.describe_secret(SecretId=secret_name)
            logger.info(f"Secret {secret_name} exists")
            return True
        except self.secrets_client.exceptions.ResourceNotFoundException:
            logger.info(f"Secret {secret_name} does not exist")
            return False
        except Exception as e:
            logger.error(f"Error checking if secret {secret_name} exists: {str(e)}")
            raise
        
    def get_secret(self, secret_name, region_name="us-east-1"):
        """
        Retrieve a secret from AWS Secrets Manager.

        :param secret_name: Name of the secret to retrieve
        :param region_name: AWS region of the secret
        :return: A dictionary containing the secret and its ARN
        """
        # Get the secret value
        get_secret_value_response = self.secrets_client.get_secret_value(
            SecretId=secret_name
        )
        # Load secret string into a dictionary
        secret = json.loads(get_secret_value_response['SecretString'])
        # Add ARN to the returned secret dictionary
        secret['ARN'] = get_secret_value_response['ARN']
        logger.info(f"Secret {secret_name} retrieved")
        return secret
    
    def create_secret(self, secret_name, secret_value, description=None):
        """
        Create a new secret in AWS Secrets Manager.

        :param secret_name: Name of the new secret
        :param secret_value: A dictionary of the secret values to store
        :param description: Optional description for the secret
        :return: Response from create_secret API
        """
        if self.check_secret_exists(secret_name):
            logger.warning(f"Secret {secret_name} already exists. Cannot create.")
            raise Exception(f"Secret {secret_name} already exists.")

        try:
            # Convert the secret_value dict into a JSON string
            secret_string = json.dumps(secret_value)

            params = {
                'Name': secret_name,
                'SecretString': secret_string
            }

            if description:
                params['Description'] = description

            # Create the secret
            response = self.secrets_client.create_secret(**params)

            logger.info(f"Secret {secret_name} created successfully.")
            return response

        except Exception as e:
            logger.error(f"Failed to create secret {secret_name}: {str(e)}")
            raise

    def update_secret(self, secret_name, updated_secret_value, region_name="us-east-1"):
        """
        Update the secret value in AWS Secrets Manager.

        :param secret_name: Name of the secret to update
        :param updated_secret_value: A dictionary containing the updated secret values
        :param region_name: AWS region of the secret
        :return: Response from the update_secret API call
        """
        # Convert the updated secret value to a JSON string
        updated_secret_string = json.dumps(updated_secret_value)

        # Update the secret
        response = self.secrets_client.update_secret(
            SecretId=secret_name,
            SecretString=updated_secret_string
        )
        logger.info(f"Secret {secret_name} updated")
        return response
