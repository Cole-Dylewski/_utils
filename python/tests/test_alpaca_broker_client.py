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

    @patch("alpaca.broker_client.BrokerAPI")
    def test_broker_client_initialization(self, mock_broker_api):
        """Test BrokerClient initialization."""
        mock_api_instance = MagicMock()
        mock_broker_api.return_value = mock_api_instance

        client = BrokerClient(api_key="test-key", api_secret="test-secret")
        assert client.api is not None
        mock_broker_api.assert_called_once()

    @patch("alpaca.broker_client.BrokerAPI")
    def test_broker_client_with_base_url(self, mock_broker_api):
        """Test BrokerClient with custom base URL."""
        mock_api_instance = MagicMock()
        mock_broker_api.return_value = mock_api_instance

        client = BrokerClient(
            api_key="test-key",
            api_secret="test-secret",
            base_url="https://broker-api.sandbox.alpaca.markets",
        )
        assert client.api is not None

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
