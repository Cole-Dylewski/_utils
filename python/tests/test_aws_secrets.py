"""
Tests for AWS Secrets Manager utilities.
"""

from unittest.mock import MagicMock, patch

from aws.secrets import SecretHandler
import pytest


@pytest.mark.aws
@pytest.mark.unit
class TestSecretHandler:
    """Test SecretHandler class."""

    @patch("aws.secrets.boto3_session.Session")
    def test_secret_handler_initialization(self, mock_session):
        """Test SecretHandler initialization."""
        mock_session_instance = MagicMock()
        mock_session.return_value = mock_session_instance
        mock_session_instance.client.return_value = MagicMock()

        handler = SecretHandler()
        assert handler.session is not None
        assert handler.secrets_client is not None

    @patch("aws.secrets.boto3_session.Session")
    def test_secret_handler_with_session(self, mock_session):
        """Test SecretHandler with provided session."""
        mock_session_obj = MagicMock()
        mock_session_obj.client.return_value = MagicMock()

        handler = SecretHandler(session=mock_session_obj)
        assert handler.session == mock_session_obj

    @pytest.mark.integration
    def test_check_secret_exists(self, moto_secretsmanager):
        """Test checking if secret exists."""
        import boto3

        secrets_client = boto3.client("secretsmanager", region_name="us-east-1")
        secrets_client.create_secret(Name="test-secret", SecretString='{"key": "value"}')

        handler = SecretHandler()
        assert handler.check_secret_exists("test-secret") is True
        assert handler.check_secret_exists("non-existent-secret") is False

    @pytest.mark.integration
    def test_get_secret(self, moto_secretsmanager):
        """Test getting secret value."""
        import boto3

        secrets_client = boto3.client("secretsmanager", region_name="us-east-1")
        secret_value = '{"username": "testuser", "password": "testpass"}'
        secrets_client.create_secret(Name="test-secret", SecretString=secret_value)

        handler = SecretHandler()
        secret = handler.get_secret("test-secret")
        assert secret["username"] == "testuser"
        assert secret["password"] == "testpass"
        assert "ARN" in secret

    @pytest.mark.integration
    def test_create_secret(self, moto_secretsmanager):
        """Test creating a new secret."""
        handler = SecretHandler()
        secret_value = {"username": "newuser", "password": "newpass"}
        response = handler.create_secret("new-secret", secret_value, description="Test secret")
        assert response is not None

        # Verify secret exists
        assert handler.check_secret_exists("new-secret") is True

    @pytest.mark.integration
    def test_update_secret(self, moto_secretsmanager):
        """Test updating secret value."""
        import boto3

        secrets_client = boto3.client("secretsmanager", region_name="us-east-1")
        secrets_client.create_secret(Name="test-secret", SecretString='{"key": "old_value"}')

        handler = SecretHandler()
        updated_value = {"key": "new_value"}
        response = handler.update_secret("test-secret", updated_value)
        assert response is not None

        # Verify secret was updated
        secret = handler.get_secret("test-secret")
        assert secret["key"] == "new_value"

    @pytest.mark.integration
    def test_create_secret_already_exists(self, moto_secretsmanager):
        """Test creating secret that already exists raises error."""
        import boto3

        secrets_client = boto3.client("secretsmanager", region_name="us-east-1")
        secrets_client.create_secret(Name="existing-secret", SecretString='{"key": "value"}')

        handler = SecretHandler()
        with pytest.raises(Exception, match="already exists"):
            handler.create_secret("existing-secret", {"key": "value"})
