"""
Tests for Alpaca broker client.
"""

from unittest.mock import MagicMock, patch

from alpaca.broker_client import BrokerClient
import pytest


@pytest.mark.alpaca
@pytest.mark.unit
class TestBrokerClient:
    """Test BrokerClient class."""

    def test_broker_client_initialization(self):
        """Test BrokerClient initialization."""
        client = BrokerClient(api_key="test-key", api_secret="test-secret")
        assert client.api_key == "test-key"
        assert client.api_secret == "test-secret"
        assert client.base_url == "https://broker-api.sandbox.alpaca.markets"
        assert "Authorization" in client.headers

    def test_broker_client_with_base_url(self):
        """Test BrokerClient with custom base URL."""
        client = BrokerClient(
            api_key="test-key",
            api_secret="test-secret",
            base_url="https://broker-api.sandbox.alpaca.markets",
        )
        assert client.api_key == "test-key"
        assert client.api_secret == "test-secret"
        assert client.base_url == "https://broker-api.sandbox.alpaca.markets"
        assert "Authorization" in client.headers

    @patch("alpaca.broker_client.accounts.create_account")
    def test_create_account(self, mock_create):
        """Test creating broker account."""
        mock_create.return_value = {"id": "test-account-id"}

        client = BrokerClient(api_key="test-key", api_secret="test-secret")
        account_data = {"contact": {"email_address": "test@example.com"}}
        result = client.create_account(account_data)
        assert result is not None
        mock_create.assert_called_once()

    @patch("alpaca.broker_client.accounts.get_account")
    def test_get_account(self, mock_get):
        """Test getting broker account."""
        mock_get.return_value = {"id": "test-account-id"}

        client = BrokerClient(api_key="test-key", api_secret="test-secret")
        account = client.get_account("test-account-id")
        assert account is not None
        mock_get.assert_called_once()
