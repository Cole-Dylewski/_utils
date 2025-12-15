"""
Integration tests for AWS services using moto.
"""

import json

from aws.s3 import S3Handler
from aws.secrets import SecretHandler
import boto3
import pytest


@pytest.mark.integration
@pytest.mark.aws
class TestAWSIntegration:
    """Integration tests for AWS services."""

    def test_s3_integration_workflow(self, moto_s3):
        """Test complete S3 workflow."""
        s3_client = boto3.client("s3", region_name="us-east-1")
        s3_client.create_bucket(Bucket="test-bucket")

        handler = S3Handler()

        # Upload
        handler.s3_client.put_object(Bucket="test-bucket", Key="test.txt", Body=b"content")

        # List
        keys = handler.s3_find_keys_containing_string("test-bucket", "test")
        assert "test.txt" in keys

        # Get metadata
        metadata = handler.get_s3_file_metadata("test-bucket", "test.txt")
        assert metadata is not None

        # Delete
        result = handler.delete_s3_file("test-bucket", "test.txt")
        assert result is True

    def test_secrets_manager_integration_workflow(self, moto_secretsmanager):
        """Test complete Secrets Manager workflow."""
        handler = SecretHandler()

        # Create secret
        secret_value = {"username": "testuser", "password": "testpass"}
        handler.create_secret("test-secret", secret_value)

        # Check exists
        assert handler.check_secret_exists("test-secret") is True

        # Get secret
        secret = handler.get_secret("test-secret")
        assert secret["username"] == "testuser"

        # Update secret
        updated_value = {"username": "newuser", "password": "newpass"}
        handler.update_secret("test-secret", updated_value)

        # Verify update
        updated_secret = handler.get_secret("test-secret")
        assert updated_secret["username"] == "newuser"
