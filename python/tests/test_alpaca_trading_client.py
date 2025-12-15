"""
Tests for Alpaca trading client.
"""

from unittest.mock import MagicMock, Mock, patch

from alpaca.trading_client import TraderClient
import pytest


@pytest.mark.alpaca
@pytest.mark.unit
class TestTraderClient:
    """Test TraderClient class."""

    def test_trader_client_initialization(self):
        """Test TraderClient initialization."""
        client = TraderClient(api_key="test-key", api_secret="test-secret")
        assert client.api_key == "test-key"
        assert client.api_secret == "test-secret"
        assert client.base_url == "https://paper-api.alpaca.markets"
        assert client.api_version == "v2"

    def test_trader_client_with_base_url(self):
        """Test TraderClient with custom base URL."""
        client = TraderClient(
            api_key="test-key",
            api_secret="test-secret",
            base_url="https://paper-api.alpaca.markets",
        )
        assert client.api_key == "test-key"
        assert client.api_secret == "test-secret"
        assert client.base_url == "https://paper-api.alpaca.markets"

    @patch("alpaca.trader_api.accounts.get_account")
    def test_get_account(self, mock_get_account):
        """Test getting account information."""
        mock_get_account.return_value = {"id": "test-account"}

        client = TraderClient(api_key="test-key", api_secret="test-secret")
        account = client.get_account()
        assert account is not None
        mock_get_account.assert_called_once_with(
            "test-key", "test-secret", "https://paper-api.alpaca.markets", "v2"
        )

    @patch("alpaca.trader_api.orders.submit_order")
    def test_submit_order(self, mock_submit_order):
        """Test submitting an order."""
        mock_submit_order.return_value = {"id": "test-order-id"}

        client = TraderClient(api_key="test-key", api_secret="test-secret")
        order = client.submit_order(
            symbol="AAPL",
            qty=10,
            side="buy",
            order_type="market",
            time_in_force="gtc",
        )
        assert order is not None
        mock_submit_order.assert_called_once_with(
            "test-key",
            "test-secret",
            "https://paper-api.alpaca.markets",
            "v2",
            "AAPL",
            10,
            "buy",
            "market",
            "gtc",
        )

    @patch("alpaca.trading_client.portfolio.get_positions")
    def test_get_positions(self, mock_get_positions):
        """Test getting positions."""
        mock_get_positions.return_value = []

        client = TraderClient(api_key="test-key", api_secret="test-secret")
        positions = client.get_positions()
        assert isinstance(positions, list)
        mock_get_positions.assert_called_once()

    @patch("alpaca.trading_client.accounts.get_account_configurations")
    def test_get_account_configurations(self, mock_get_config):
        """Test getting account configurations."""
        mock_get_config.return_value = {"pattern_day_trader": False}

        client = TraderClient(api_key="test-key", api_secret="test-secret")
        config = client.get_account_configurations()
        assert config is not None
        mock_get_config.assert_called_once()

    @patch("alpaca.trading_client.orders.cancel_order")
    def test_cancel_order(self, mock_cancel):
        """Test canceling an order."""
        mock_cancel.return_value = {}

        client = TraderClient(api_key="test-key", api_secret="test-secret")
        result = client.cancel_order("test-order-id")
        assert result is not None
        mock_cancel.assert_called_once()
