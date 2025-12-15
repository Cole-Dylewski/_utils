"""
Tests for API utilities.
"""

import json
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

    @patch("aws.secrets.SecretHandler")
    @patch("requests.post")
    def test_aws_api_request_with_secret(self, mock_post, mock_secrets):
        """Test AWS API request with Secrets Manager."""
        from utils.api import aws_api_request

        mock_secret_handler = MagicMock()
        mock_secret_handler.get_secret.return_value = {
            "testclient": json.dumps({"PROD": {"id": "gateway-id", "key": "api-key"}})
        }
        mock_secrets.return_value = mock_secret_handler

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
        mock_post.assert_called_once()

    @patch("requests.post")
    def test_aws_api_request_with_credentials(self, mock_post):
        """Test AWS API request with provided credentials."""
        from utils.api import aws_api_request

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"result": "success"}
        mock_post.return_value = mock_response

        result = aws_api_request(
            functionName="test-function",
            client="testclient",
            gatewayID="gateway-id",
            apiKey="api-key",
            body={"key": "value"},
        )
        assert result is not None
        mock_post.assert_called_once()

    def test_aws_api_request_missing_credentials(self):
        """Test AWS API request raises error when credentials are missing."""
        from utils.api import aws_api_request

        with pytest.raises(ValueError, match="api_creds_secret_name"):
            aws_api_request(functionName="test-function", client="testclient")

    @pytest.mark.asyncio
    async def test_run_async_requests_in_parallel(self):
        """Test running multiple async requests in parallel."""
        from utils.api import run_async_requests_in_parallel

        with patch("utils.api.httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"test": "data"}
            mock_client.return_value.__aenter__.return_value.request.return_value = mock_response

            requests_list = [
                {"method": "GET", "url": "https://example.com/1"},
                {"method": "GET", "url": "https://example.com/2"},
            ]
            responses = await run_async_requests_in_parallel(requests_list)
            assert len(responses) == 2

    @pytest.mark.asyncio
    async def test_run_async_requests_in_sequence(self):
        """Test running multiple async requests in sequence."""
        from utils.api import run_async_requests_in_sequence

        with patch("utils.api.httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"test": "data"}
            mock_client.return_value.__aenter__.return_value.request.return_value = mock_response

            requests_list = [
                {"method": "GET", "url": "https://example.com/1"},
                {"method": "GET", "url": "https://example.com/2"},
            ]
            responses = await run_async_requests_in_sequence(requests_list)
            assert len(responses) == 2

    @pytest.mark.asyncio
    async def test_send_async_request_with_params(self):
        """Test async request with parameters."""
        from utils.api import send_async_request

        with patch("utils.api.httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"test": "data"}
            mock_client.return_value.__aenter__.return_value.request.return_value = mock_response

            response = await send_async_request(
                "GET", "https://example.com", params={"key": "value"}, headers={"X-Test": "test"}
            )
            assert response.status_code == 200

    @patch("utils.api.httpx.Client")
    def test_send_sync_request_with_data(self, mock_client):
        """Test sync request with data."""
        from utils.api import send_sync_request

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_client.return_value.__enter__.return_value.request.return_value = mock_response

        response = send_sync_request("POST", "https://example.com", data={"key": "value"})
        assert response.status_code == 200

    @patch("utils.api.httpx.Client")
    def test_send_sync_request_with_json(self, mock_client):
        """Test sync request with JSON."""
        from utils.api import send_sync_request

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_client.return_value.__enter__.return_value.request.return_value = mock_response

        response = send_sync_request("POST", "https://example.com", json={"key": "value"})
        assert response.status_code == 200

    @patch("utils.api.httpx.Client")
    def test_send_sync_request_with_timeout(self, mock_client):
        """Test sync request with timeout."""
        from utils.api import send_sync_request

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_client.return_value.__enter__.return_value.request.return_value = mock_response

        response = send_sync_request("GET", "https://example.com", timeout=30.0)
        assert response.status_code == 200
