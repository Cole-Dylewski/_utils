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
