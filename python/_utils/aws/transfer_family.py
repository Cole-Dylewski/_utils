import logging
import time
from typing import Any

from botocore.exceptions import ClientError

from _utils.aws import boto3_session, s3, secrets

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
"""
WORK TO DO:
UPDATE CREATE USER TO VALIDATE IF CLIENT S3 FOLDER EXISTS, AND THEN CREATE IF IT DOESNT AND PLACE INTO
"""


class TransferServerException(Exception):
    """Custom exception for AWS Transfer Family server errors."""

    def __init__(self, server_id, message="Transfer Family Server operation failed."):
        self.server_id = server_id
        self.message = f"Server {server_id}: {message}"
        super().__init__(self.message)


class TransferFamilyHandler:
    """
    Handles AWS Transfer Family SFTP Server operations:
    create, delete, manage servers and users, etc.
    """

    def __init__(
        self,
        aws_access_key_id=None,
        aws_secret_access_key=None,
        region_name="us-east-1",
        session=None,
    ):
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

        logger.info(f"TransferFamilyHandler initialized in region: {self.region}")

        # Create Transfer Family client
        self.transfer_client = self.session.client(
            "transfer",
            region_name=self.region,
            endpoint_url=f"https://transfer.{self.region}.amazonaws.com",
        )

        # Optional other handlers
        self.s3_handler = s3.S3Handler(session=self.session)
        self.secret_handler = secrets.SecretHandler(session=self.session)

    # -------------------------------------
    # Transfer Server Management
    # -------------------------------------

    def create_server(
        self,
        endpoint_type: str = "PUBLIC",
        identity_provider_type: str = "SERVICE_MANAGED",
        protocols: list[str] | None = None,
        logging_role: str | None = None,
        tags: list[dict[str, str]] | None = None,
        endpoint_details: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Creates a new Transfer Family SFTP Server.
        """
        logger.info(f"Creating Transfer Family server with endpoint type: {endpoint_type}")

        params = {"EndpointType": endpoint_type, "IdentityProviderType": identity_provider_type}

        if protocols:
            params["Protocols"] = protocols

        if logging_role:
            params["LoggingRole"] = logging_role

        if tags:
            params["Tags"] = tags

        if endpoint_details:
            params["EndpointDetails"] = endpoint_details

        try:
            response = self.transfer_client.create_server(**params)
            server_id = response.get("ServerId")
            logger.info(f"Transfer Family server created successfully: {server_id}")
            return response
        except ClientError as e:
            logger.exception(f"Failed to create Transfer Family server: {e}")
            raise

    def delete_server(self, server_id: str):
        """
        Deletes a Transfer Family server.
        """
        logger.info(f"Deleting Transfer Family server: {server_id}")

        try:
            response = self.transfer_client.delete_server(ServerId=server_id)
            logger.info(f"Transfer Family server {server_id} deleted successfully")
            return response
        except ClientError as e:
            logger.exception(f"Failed to delete server {server_id}: {e}")
            raise

    def describe_server(self, server_id: str) -> dict[str, Any]:
        """
        Describes a Transfer Family server.
        """
        logger.info(f"Describing Transfer Family server: {server_id}")

        try:
            response = self.transfer_client.describe_server(ServerId=server_id)
            logger.info(f"Server description retrieved for: {server_id}")
            return response
        except ClientError as e:
            logger.exception(f"Failed to describe server {server_id}: {e}")
            raise

    def list_servers(self) -> list[dict[str, Any]]:
        """
        Lists all Transfer Family servers in the account.
        """
        logger.info("Listing all Transfer Family servers")

        try:
            response = self.transfer_client.list_servers()
            servers = response.get("Servers", [])
            logger.info(f"Found {len(servers)} Transfer Family servers")
            return servers
        except ClientError as e:
            logger.exception(f"Failed to list Transfer Family servers: {e}")
            raise

    def update_server(
        self,
        server_id: str,
        endpoint_type: str | None = None,
        logging_role: str | None = None,
        protocols: list[str] | None = None,
    ):
        """
        Updates an existing Transfer Family server.
        """
        logger.info(f"Updating Transfer Family server: {server_id}")

        update_params = {"ServerId": server_id}

        if endpoint_type:
            update_params["EndpointType"] = endpoint_type

        if logging_role:
            update_params["LoggingRole"] = logging_role

        if protocols:
            update_params["Protocols"] = protocols

        try:
            response = self.transfer_client.update_server(**update_params)
            logger.info(f"Transfer Family server {server_id} updated successfully")
            return response
        except ClientError as e:
            logger.exception(f"Failed to update Transfer Family server {server_id}: {e}")
            raise

    # -------------------------------------
    # Transfer User Management
    # -------------------------------------

    def create_user(
        self,
        user_name: str,
        server_id: str,
        role: str,
        client_name: str | None = None,
        bucket_name: str = "",
        ssh_key_pair: dict[str, str] | None = None,
        tags: list[dict[str, str]] | None = None,
    ):
        """
        Creates a Transfer Family user locked to their S3 subfolder but with '/' as their visible root.

        Steps:
        1. Ensure S3 prefix s3://{bucket_name}/Incoming/{client_name}/ exists.
        2. Generate SSH keypair if not provided.
        3. Create Transfer Family user with HomeDirectoryType=LOGICAL mapped to that folder.
        4. Return API response and private key for secure delivery.
        """
        logger.info(f"Creating Transfer Family user {user_name} on server {server_id}")

        # If no client_name given, default to username
        if not client_name:
            client_name = user_name

        # S3 folder path
        s3_prefix = f"Incoming/{client_name}/"
        s3_full_path = f"/{bucket_name}/{s3_prefix}"  # AWS logical mapping target

        # Step 1: Ensure S3 folder exists
        if not self.s3_handler.check_prefix_exists(bucket_name, s3_prefix):
            logger.info(f"S3 folder missing, creating: s3://{bucket_name}/{s3_prefix}")
            self.s3_handler.send_to_s3(
                data=f"Auto-created placeholder for {client_name}",
                bucket=bucket_name,
                s3_file_name=f"{s3_prefix}{client_name}_placeholder.txt",
            )

        # Step 2: Generate SSH keys if not passed in
        if ssh_key_pair is None:
            from _utils.utils import cryptography

            logger.info(f"Generating SSH keypair for client {client_name}")
            ssh_key_pair = cryptography.gen_rsa_keys(
                key_size=2048,
                key_format="ssh",
                region_name=self.region,
                secret_name=f"{client_name}_sftp_key",
                save_location="s3",
                client=client_name,
            )
        public_key = ssh_key_pair["public_key"]
        private_key = ssh_key_pair["private_key"]

        # Step 3: Build create_user params with LOGICAL mapping
        params = {
            "ServerId": server_id,
            "UserName": user_name,
            "Role": role,
            "SshPublicKeyBody": public_key,
            "HomeDirectoryType": "LOGICAL",
            "HomeDirectoryMappings": [
                {
                    "Entry": "/",  # user sees root
                    "Target": s3_full_path,  # actually maps to their S3 folder
                }
            ],
        }

        if tags:
            params["Tags"] = tags

        # Step 4: Create the Transfer Family user
        try:
            response = self.transfer_client.create_user(**params)
            logger.info(f"User {user_name} created with root mapped to {s3_full_path}")
        except ClientError as e:
            if "UserAlreadyExists" in str(e):
                logger.warning(f"User {user_name} already exists on {server_id}")
            else:
                logger.exception(f"Failed to create Transfer Family user {user_name}: {e}")
                raise

        # Return response & private key
        return {
            "transfer_user_response": response,
            "sftp_username": user_name,
            "mapped_s3_path": s3_full_path,
            "public_key": public_key,
            "private_key": private_key,
        }

    def delete_user(self, server_id: str, user_name: str):
        """
        Deletes a user from a Transfer Family server.
        """
        logger.info(f"Deleting user {user_name} from server {server_id}")

        try:
            response = self.transfer_client.delete_user(ServerId=server_id, UserName=user_name)
            logger.info(f"User {user_name} deleted successfully from server {server_id}")
            return response
        except ClientError as e:
            logger.exception(f"Failed to delete user {user_name} from server {server_id}: {e}")
            raise

    def describe_user(self, server_id: str, user_name: str) -> dict[str, Any]:
        """
        Describes a user on a Transfer Family server.
        """
        logger.info(f"Describing user {user_name} on server {server_id}")

        try:
            response = self.transfer_client.describe_user(ServerId=server_id, UserName=user_name)
            logger.info(f"User description retrieved for {user_name} on server {server_id}")
            return response
        except ClientError as e:
            logger.exception(f"Failed to describe user {user_name} on server {server_id}: {e}")
            raise

    def list_users(self, server_id: str) -> list[dict[str, Any]]:
        """
        Lists all users on a Transfer Family server.
        """
        logger.info(f"Listing users on Transfer Family server: {server_id}")

        try:
            response = self.transfer_client.list_users(ServerId=server_id)
            users = response.get("Users", [])
            logger.info(f"Found {len(users)} users on server {server_id}")
            return users
        except ClientError as e:
            logger.exception(f"Failed to list users on server {server_id}: {e}")
            raise

    # -------------------------------------
    # Monitoring and Helper Methods
    # -------------------------------------

    def wait_for_server_state(
        self,
        server_id: str,
        desired_state: str = "ONLINE",
        wait_interval: int = 15,
        timeout: int = 600,
    ):
        """
        Waits for a Transfer Family server to reach a desired state.
        """
        logger.info(f"Waiting for server {server_id} to reach state {desired_state}")

        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                response = self.describe_server(server_id)
                state = response["Server"]["State"]
                logger.info(f"Current state of server {server_id}: {state}")

                if state == desired_state:
                    logger.info(f"Server {server_id} reached state {desired_state}")
                    return response

                time.sleep(wait_interval)
            except ClientError as e:
                logger.exception(f"Error while waiting for server {server_id} state: {e}")
                raise

        raise TransferServerException(
            server_id, message=f"Timed out waiting for server to reach state {desired_state}"
        )

    def reset_password(self, server_id: str, user_name: str, new_ssh_public_key_body: str):
        """
        Resets a user's password by replacing their SSH public key with a new one.

        Steps:
        1. List existing SSH keys for the user.
        2. Delete all existing SSH keys.
        3. Import the new SSH public key.
        """
        logger.info(f"Resetting SSH key for user {user_name} on server {server_id}")

        try:
            # Step 1: List all existing SSH keys
            response = self.transfer_client.list_ssh_public_keys(
                ServerId=server_id, UserName=user_name
            )
            existing_keys = response.get("SshPublicKeys", [])
            logger.info(
                f"Found {len(existing_keys)} existing SSH public key(s) for user {user_name}"
            )

            # Step 2: Delete all existing SSH keys
            for key in existing_keys:
                ssh_key_id = key["SshPublicKeyId"]
                logger.info(f"Deleting existing SSH key {ssh_key_id} for user {user_name}")
                self.transfer_client.delete_ssh_public_key(
                    ServerId=server_id, UserName=user_name, SshPublicKeyId=ssh_key_id
                )

            # Step 3: Import the new SSH public key
            logger.info(f"Importing new SSH public key for user {user_name}")
            import_response = self.transfer_client.import_ssh_public_key(
                ServerId=server_id, UserName=user_name, SshPublicKeyBody=new_ssh_public_key_body
            )

            logger.info(f"SSH public key reset successfully for user {user_name}")
            return import_response

        except ClientError as e:
            logger.exception(
                f"Failed to reset SSH public key for user {user_name} on server {server_id}: {e}"
            )
            raise
