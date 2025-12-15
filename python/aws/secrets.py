import json
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
        session=None,
    ):
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

        # Initialize Secrets Manager client
        self.secrets_client = self.session.client(service_name="secretsmanager")
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
            logger.exception(f"Error checking if secret {secret_name} exists: {e!s}")
            raise

    def get_secret(self, secret_name, region_name="us-east-1"):
        """
        Retrieve a secret from AWS Secrets Manager.

        :param secret_name: Name of the secret to retrieve
        :param region_name: AWS region of the secret
        :return: A dictionary containing the secret and its ARN
        """
        # Get the secret value
        get_secret_value_response = self.secrets_client.get_secret_value(SecretId=secret_name)
        # Load secret string into a dictionary
        secret = json.loads(get_secret_value_response["SecretString"])
        # Add ARN to the returned secret dictionary
        secret["ARN"] = get_secret_value_response["ARN"]
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

            params = {"Name": secret_name, "SecretString": secret_string}

            if description:
                params["Description"] = description

            # Create the secret
            response = self.secrets_client.create_secret(**params)

            logger.info(f"Secret {secret_name} created successfully.")
            return response

        except Exception as e:
            logger.exception(f"Failed to create secret {secret_name}: {e!s}")
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
            SecretId=secret_name, SecretString=updated_secret_string
        )
        logger.info(f"Secret {secret_name} updated")
        return response


# CLI functionality
if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="AWS Secrets Manager CLI - Manage secrets")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Get command
    get_parser = subparsers.add_parser("get", help="Get secret value")
    get_parser.add_argument("secret_name", help="Secret name")
    get_parser.add_argument("--key", help="Get specific key from JSON secret")
    get_parser.add_argument("--region", help="AWS region")

    # Set command
    set_parser = subparsers.add_parser("set", help="Set secret value")
    set_parser.add_argument("secret_name", help="Secret name")
    set_parser.add_argument("value", help="Secret value (JSON string or plain text)")
    set_parser.add_argument("--region", help="AWS region")

    # Check command
    check_parser = subparsers.add_parser("check", help="Check if secret exists")
    check_parser.add_argument("secret_name", help="Secret name")
    check_parser.add_argument("--region", help="AWS region")

    # List command
    list_parser = subparsers.add_parser("list", help="List all secrets")
    list_parser.add_argument("--region", help="AWS region")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    try:
        handler = (
            SecretHandler(region_name=args.region)
            if hasattr(args, "region") and args.region
            else SecretHandler()
        )

        if args.command == "get":
            secret = handler.get_secret(args.secret_name)
            if args.key:
                if isinstance(secret, dict) and args.key in secret:
                    print(secret[args.key])
                else:
                    print(f"Key '{args.key}' not found in secret", file=sys.stderr)
                    sys.exit(1)
            else:
                print(json.dumps(secret, indent=2))

        elif args.command == "set":
            try:
                # Try to parse as JSON
                value = json.loads(args.value)
            except json.JSONDecodeError:
                # If not JSON, treat as plain string
                value = args.value
            handler.update_secret(args.secret_name, value)
            print(f"Secret {args.secret_name} updated")

        elif args.command == "check":
            exists = handler.check_secret_exists(args.secret_name)
            print(f"Secret {args.secret_name} {'exists' if exists else 'does not exist'}")
            sys.exit(0 if exists else 1)

        elif args.command == "list":
            # Note: This requires implementing list_secrets method or using boto3 directly
            print("List command not yet implemented. Use AWS CLI: aws secretsmanager list-secrets")

    except Exception as e:
        logger.exception(f"Secret operation failed: {e}")
        sys.exit(1)
