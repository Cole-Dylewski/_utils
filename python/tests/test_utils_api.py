"""
Tests for API utilities.
"""

from unittest.mock import MagicMock, patch

import pytest
from utils import api


@pytest.mark.unit
class TestAPIUtils:
    """Test API utility functions."""

    def test_api_import(self):
        """Test that api module can be imported."""
        assert api is not None

    @pytest.mark.asyncio
    async def test_send_async_request(self):
        """Test async API request."""
        from utils.api import send_async_request

        # Mock httpx.AsyncClient
        with patch("utils.api.httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"test": "data"}
            mock_client.return_value.__aenter__.return_value.request.return_value = mock_response

            response = await send_async_request("GET", "https://example.com")
            assert response.status_code == 200

    @patch("utils.api.httpx.Client")
    def test_send_sync_request(self, mock_client):
        """Test sync API request."""
        from utils.api import send_sync_request

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_client.return_value.__enter__.return_value.request.return_value = mock_response

        response = send_sync_request("GET", "https://example.com")
        assert response.status_code == 200

    @patch("utils.api.secrets.SecretHandler")
    def test_aws_api_request_with_secret(self, mock_secrets):
        """Test AWS API request with Secrets Manager."""
        from utils.api import aws_api_request

        mock_secret_handler = MagicMock()
        mock_secret_handler.get_secret.return_value = {
            "testclient": json.dumps({"PROD": {"id": "gateway-id", "key": "api-key"}})
        }
        mock_secrets.return_value = mock_secret_handler

        with patch("utils.api.requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"result": "success"}
            mock_post.return_value = mock_response

            result = aws_api_request(
                functionName="test-function",
                client="testclient",
                api_creds_secret_name="api-secret",
            )
            assert result is not None
