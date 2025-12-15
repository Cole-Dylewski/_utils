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

    @patch("alpaca.trading_client.TradeAPI")
    def test_trader_client_initialization(self, mock_trade_api):
        """Test TraderClient initialization."""
        mock_api_instance = MagicMock()
        mock_trade_api.return_value = mock_api_instance

        client = TraderClient(api_key="test-key", api_secret="test-secret")
        assert client.api is not None
        mock_trade_api.assert_called_once()

    @patch("alpaca.trading_client.TradeAPI")
    def test_trader_client_with_base_url(self, mock_trade_api):
        """Test TraderClient with custom base URL."""
        mock_api_instance = MagicMock()
        mock_trade_api.return_value = mock_api_instance

        client = TraderClient(
            api_key="test-key",
            api_secret="test-secret",
            base_url="https://paper-api.alpaca.markets",
        )
        assert client.api is not None

    @patch("alpaca.trading_client.TradeAPI")
    def test_get_account(self, mock_trade_api):
        """Test getting account information."""
        mock_api_instance = MagicMock()
        mock_account = MagicMock()
        mock_api_instance.get_account.return_value = mock_account
        mock_trade_api.return_value = mock_api_instance

        client = TraderClient(api_key="test-key", api_secret="test-secret")
        account = client.get_account()
        assert account is not None
        mock_api_instance.get_account.assert_called_once()

    @patch("alpaca.trading_client.TradeAPI")
    def test_submit_order(self, mock_trade_api):
        """Test submitting an order."""
        mock_api_instance = MagicMock()
        mock_order = MagicMock()
        mock_api_instance.submit_order.return_value = mock_order
        mock_trade_api.return_value = mock_api_instance

        client = TraderClient(api_key="test-key", api_secret="test-secret")
        order = client.submit_order(
            symbol="AAPL",
            qty=10,
            side="buy",
            order_type="market",
            time_in_force="gtc",
        )
        assert order is not None
        mock_api_instance.submit_order.assert_called_once()

    @patch("alpaca.trading_client.TradeAPI")
    def test_get_positions(self, mock_trade_api):
        """Test getting positions."""
        mock_api_instance = MagicMock()
        mock_api_instance.list_positions.return_value = []
        mock_trade_api.return_value = mock_api_instance

        client = TraderClient(api_key="test-key", api_secret="test-secret")
        positions = client.get_positions()
        assert isinstance(positions, list)
        mock_api_instance.list_positions.assert_called_once()
