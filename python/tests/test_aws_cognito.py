"""
Tests for AWS Cognito utilities.
"""

from unittest.mock import MagicMock, patch

from aws.cognito import CognitoHandler
import pytest


@pytest.mark.aws
@pytest.mark.unit
class TestCognitoHandler:
    """Test CognitoHandler class."""

    @patch("aws.boto3_session.Session")
    def test_cognito_handler_initialization_with_credentials(self, mock_session):
        """Test CognitoHandler initialization with provided credentials."""
        mock_session_instance = MagicMock()
        mock_session.return_value = mock_session_instance
        mock_session_instance.client.return_value = MagicMock()

        handler = CognitoHandler(
            cognito_app_client_id="test-client-id",
            cognito_userpool_id="test-pool-id",
            cognito_region="us-east-1",
        )
        assert handler.session is not None
        assert handler.cognito_client is not None
        assert handler.client_id == "test-client-id"
        assert handler.user_pool_id == "test-pool-id"

    @patch("aws.cognito.secrets.SecretHandler")
    @patch("aws.boto3_session.Session")
    def test_cognito_handler_initialization_with_secret(self, mock_session, mock_secrets):
        """Test CognitoHandler initialization with Secrets Manager."""
        mock_secret_handler = MagicMock()
        mock_secret_handler.get_secret.return_value = {
            "COGNITO_APP_CLIENT_ID": "secret-client-id",
            "COGNITO_USERPOOL_ID": "secret-pool-id",
            "COGNITO_REGION": "us-west-2",
        }
        mock_secrets.return_value = mock_secret_handler

        mock_session_instance = MagicMock()
        mock_session.return_value = mock_session_instance
        mock_session_instance.client.return_value = MagicMock()

        handler = CognitoHandler(cognito_creds_secret_name="cognito-secret")
        assert handler.client_id == "secret-client-id"
        assert handler.user_pool_id == "secret-pool-id"
        assert handler.region == "us-west-2"

    @patch("aws.boto3_session.Session")
    def test_cognito_handler_initialization_missing_credentials(self, mock_session):
        """Test CognitoHandler initialization without credentials raises error."""
        with pytest.raises(ValueError, match="cognito_creds_secret_name parameter is required"):
            CognitoHandler()

    @patch("aws.boto3_session.Session")
    def test_authenticate_user(self, mock_session):
        """Test user authentication."""
        mock_session_instance = MagicMock()
        mock_cognito_client = MagicMock()
        mock_cognito_client.initiate_auth.return_value = {
            "AuthenticationResult": {
                "AccessToken": "test-access-token",
                "IdToken": "test-id-token",
                "RefreshToken": "test-refresh-token",
            }
        }
        mock_session_instance.client.return_value = mock_cognito_client
        mock_session.return_value = mock_session_instance

        handler = CognitoHandler(
            cognito_app_client_id="test-client",
            cognito_userpool_id="test-pool",
            cognito_region="us-east-1",
            session=mock_session_instance,
        )
        result = handler.authenticate_user("testuser", "testpass")
        assert "AccessToken" in result or "challenge_name" in result
        mock_cognito_client.initiate_auth.assert_called_once()

    @patch("aws.boto3_session.Session")
    def test_refresh_user_token(self, mock_session):
        """Test token refresh."""
        mock_session_instance = MagicMock()
        mock_cognito_client = MagicMock()
        mock_cognito_client.initiate_auth.return_value = {
            "AuthenticationResult": {
                "AccessToken": "new-access-token",
                "IdToken": "new-id-token",
            }
        }
        mock_session_instance.client.return_value = mock_cognito_client
        mock_session.return_value = mock_session_instance

        handler = CognitoHandler(
            cognito_app_client_id="test-client",
            cognito_userpool_id="test-pool",
            cognito_region="us-east-1",
            session=mock_session_instance,
        )
        result = handler.refresh_user_token("refresh-token")
        assert "AccessToken" in result
        mock_cognito_client.initiate_auth.assert_called_once()
