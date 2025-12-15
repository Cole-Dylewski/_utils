"""
Tests for Alpaca broker API modules.
"""

from unittest.mock import MagicMock, patch

from alpaca.broker_api import accounts
import pytest


@pytest.mark.alpaca
@pytest.mark.unit
class TestAlpacaBrokerAPI:
    """Test Alpaca broker API functions."""

    @patch("alpaca.broker_api.accounts.requests.post")
    def test_create_account(self, mock_post):
        """Test creating broker account."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"id": "test-account-id"}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        headers = {"Authorization": "Basic test"}
        account_data = {"contact": {"email_address": "test@example.com"}}
        result = accounts.create_account("https://api.alpaca.markets", "v1", headers, account_data)
        assert result is not None
        assert "id" in result
        mock_post.assert_called_once()

    @patch("alpaca.broker_api.accounts.requests.get")
    def test_get_account(self, mock_get):
        """Test getting broker account."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"id": "test-account-id", "status": "active"}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        headers = {"Authorization": "Basic test"}
        result = accounts.get_account(
            "https://api.alpaca.markets", "v1", headers, "test-account-id"
        )
        assert result is not None
        assert "id" in result
        mock_get.assert_called_once()

    @patch("alpaca.broker_api.accounts.requests.patch")
    def test_update_account(self, mock_patch):
        """Test updating broker account."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"id": "test-account-id", "status": "updated"}
        mock_response.raise_for_status.return_value = None
        mock_patch.return_value = mock_response

        headers = {"Authorization": "Basic test"}
        update_data = {"status": "updated"}
        result = accounts.update_account(
            "https://api.alpaca.markets", "v1", headers, "test-account-id", update_data
        )
        assert result is not None
        mock_patch.assert_called_once()

    @patch("alpaca.broker_api.accounts.requests.get")
    def test_get_account_http_error(self, mock_get):
        """Test get_account with HTTP error."""
        import requests as requests_lib

        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests_lib.exceptions.HTTPError(
            "404 Not Found"
        )
        mock_get.return_value = mock_response

        headers = {"Authorization": "Basic test"}
        result = accounts.get_account(
            "https://api.alpaca.markets", "v1", headers, "test-account-id"
        )
        assert result is None
