"""
Tests for Alpaca trader API modules.
"""

from unittest.mock import MagicMock, patch

from alpaca.trader_api import (
    accounts,
    assets,
    calendar,
    clock,
    crypto,
    history,
    orders,
    portfolio,
    watchlists,
)
from alpaca.trader_api.data import (
    corporate_actions,
    forex,
    logos,
    news,
    options,
    screener,
    stocks,
)
from alpaca.trader_api.data import (
    crypto as data_crypto,
)
import pytest
import requests


@pytest.mark.alpaca
@pytest.mark.unit
class TestAlpacaTraderAPI:
    """Test Alpaca trader API functions."""

    @patch("alpaca.trader_api.accounts.requests.get")
    def test_get_account(self, mock_get):
        """Test getting account information."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"account_number": "123456"}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = accounts.get_account("key", "secret", "https://api.alpaca.markets", "v2")
        assert result is not None
        assert "account_number" in result
        mock_get.assert_called_once()

    @patch("alpaca.trader_api.accounts.requests.get")
    def test_get_account_configurations(self, mock_get):
        """Test getting account configurations."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"pattern_day_trader": False}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = accounts.get_account_configurations(
            "key", "secret", "https://api.alpaca.markets", "v2"
        )
        assert result is not None
        mock_get.assert_called_once()

    @patch("alpaca.trader_api.accounts.requests.patch")
    def test_update_account_configurations(self, mock_patch):
        """Test updating account configurations."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"pattern_day_trader": True}
        mock_response.raise_for_status.return_value = None
        mock_patch.return_value = mock_response

        result = accounts.update_account_configurations(
            "key", "secret", "https://api.alpaca.markets", "v2", pattern_day_trader=True
        )
        assert result is not None
        mock_patch.assert_called_once()

    @patch("alpaca.trader_api.accounts.requests.get")
    def test_get_account_http_error(self, mock_get):
        """Test get_account with HTTP error."""
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("404 Not Found")
        mock_get.return_value = mock_response

        result = accounts.get_account("key", "secret", "https://api.alpaca.markets", "v2")
        assert result is None

    @patch("alpaca.trader_api.accounts.requests.get")
    def test_get_account_activities(self, mock_get):
        """Test getting account activities."""
        mock_response = MagicMock()
        mock_response.json.return_value = [{"id": "1", "activity_type": "FILL"}]
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = accounts.get_account_activities(
            "key", "secret", "https://api.alpaca.markets", "v2", activity_type="FILL"
        )
        assert result is not None
        mock_get.assert_called_once()


@pytest.mark.alpaca
@pytest.mark.unit
class TestAlpacaOrders:
    """Test Alpaca orders API."""

    @patch("alpaca.trader_api.orders.requests.post")
    def test_submit_order(self, mock_post):
        """Test submitting an order."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"id": "order123", "status": "new"}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        result = orders.submit_order(
            "key",
            "secret",
            "https://api.alpaca.markets",
            "v2",
            "AAPL",
            10,
            "buy",
            "market",
            "day",
        )
        assert result is not None
        assert result["id"] == "order123"
        mock_post.assert_called_once()

    @patch("alpaca.trader_api.orders.requests.post")
    def test_submit_order_with_limit_price(self, mock_post):
        """Test submitting an order with limit price."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"id": "order123", "status": "new"}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        result = orders.submit_order(
            "key",
            "secret",
            "https://api.alpaca.markets",
            "v2",
            "AAPL",
            10,
            "buy",
            "limit",
            "day",
            limit_price=150.0,
        )
        assert result is not None
        mock_post.assert_called_once()

    @patch("alpaca.trader_api.orders.requests.post")
    def test_submit_order_http_error(self, mock_post):
        """Test submit_order with HTTP error."""
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            "400 Bad Request"
        )
        mock_post.return_value = mock_response

        result = orders.submit_order(
            "key",
            "secret",
            "https://api.alpaca.markets",
            "v2",
            "AAPL",
            10,
            "buy",
            "market",
            "day",
        )
        assert result is None

    @patch("alpaca.trader_api.orders.requests.get")
    def test_list_orders(self, mock_get):
        """Test listing orders."""
        mock_response = MagicMock()
        mock_response.json.return_value = [{"id": "order1"}, {"id": "order2"}]
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = orders.list_orders("key", "secret", "https://api.alpaca.markets", "v2")
        assert result is not None
        assert len(result) == 2
        mock_get.assert_called_once()

    @patch("alpaca.trader_api.orders.requests.get")
    def test_get_order(self, mock_get):
        """Test getting a specific order."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"id": "order123", "symbol": "AAPL"}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = orders.get_order("key", "secret", "https://api.alpaca.markets", "v2", "order123")
        assert result is not None
        assert result["id"] == "order123"
        mock_get.assert_called_once()

    @patch("alpaca.trader_api.orders.requests.patch")
    def test_replace_order(self, mock_patch):
        """Test replacing an order."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"id": "order123", "qty": 20}
        mock_response.raise_for_status.return_value = None
        mock_patch.return_value = mock_response

        result = orders.replace_order(
            "key", "secret", "https://api.alpaca.markets", "v2", "order123", qty=20
        )
        assert result is not None
        assert result["qty"] == 20
        mock_patch.assert_called_once()

    @patch("alpaca.trader_api.orders.requests.delete")
    def test_cancel_order(self, mock_delete):
        """Test canceling an order."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"id": "order123", "status": "canceled"}
        mock_response.raise_for_status.return_value = None
        mock_delete.return_value = mock_response

        result = orders.cancel_order(
            "key", "secret", "https://api.alpaca.markets", "v2", "order123"
        )
        assert result is not None
        assert result["status"] == "canceled"
        mock_delete.assert_called_once()


@pytest.mark.alpaca
@pytest.mark.unit
class TestAlpacaPortfolio:
    """Test Alpaca portfolio API."""

    @patch("alpaca.trader_api.portfolio.requests.get")
    def test_get_positions(self, mock_get):
        """Test getting positions."""
        mock_response = MagicMock()
        mock_response.json.return_value = [{"symbol": "AAPL", "qty": 10}]
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = portfolio.get_positions("key", "secret", "https://api.alpaca.markets", "v2")
        assert result is not None
        assert len(result) == 1
        mock_get.assert_called_once()

    @patch("alpaca.trader_api.portfolio.requests.get")
    def test_get_positions_http_error(self, mock_get):
        """Test get_positions with HTTP error."""
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("500 Error")
        mock_get.return_value = mock_response

        result = portfolio.get_positions("key", "secret", "https://api.alpaca.markets", "v2")
        assert result is None

    @patch("alpaca.trader_api.portfolio.requests.get")
    def test_get_portfolio_history(self, mock_get):
        """Test getting portfolio history."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"equity": [1000, 1100, 1200]}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = portfolio.get_portfolio_history(
            "key", "secret", "https://api.alpaca.markets", "v2", period="1M"
        )
        assert result is not None
        assert "equity" in result
        mock_get.assert_called_once()


@pytest.mark.alpaca
@pytest.mark.unit
class TestAlpacaWatchlists:
    """Test Alpaca watchlists API."""

    @patch("alpaca.trader_api.watchlists.requests.post")
    def test_create_watchlist(self, mock_post):
        """Test creating a watchlist."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"id": "watchlist123", "name": "My Watchlist"}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        result = watchlists.create_watchlist(
            "key", "secret", "https://api.alpaca.markets", "v2", "My Watchlist", ["AAPL", "MSFT"]
        )
        assert result is not None
        assert result["name"] == "My Watchlist"
        mock_post.assert_called_once()

    @patch("alpaca.trader_api.watchlists.requests.get")
    def test_get_watchlist(self, mock_get):
        """Test getting a watchlist."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"id": "watchlist123", "symbols": ["AAPL"]}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = watchlists.get_watchlist(
            "key", "secret", "https://api.alpaca.markets", "v2", "watchlist123"
        )
        assert result is not None
        assert result["id"] == "watchlist123"
        mock_get.assert_called_once()

    @patch("alpaca.trader_api.watchlists.requests.put")
    def test_update_watchlist(self, mock_put):
        """Test updating a watchlist."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"id": "watchlist123", "symbols": ["AAPL", "MSFT"]}
        mock_response.raise_for_status.return_value = None
        mock_put.return_value = mock_response

        result = watchlists.update_watchlist(
            "key", "secret", "https://api.alpaca.markets", "v2", "watchlist123", ["AAPL", "MSFT"]
        )
        assert result is not None
        assert len(result["symbols"]) == 2
        mock_put.assert_called_once()

    @patch("alpaca.trader_api.watchlists.requests.delete")
    def test_delete_watchlist(self, mock_delete):
        """Test deleting a watchlist."""
        mock_response = MagicMock()
        mock_response.status_code = 204
        mock_response.raise_for_status.return_value = None
        mock_delete.return_value = mock_response

        result = watchlists.delete_watchlist(
            "key", "secret", "https://api.alpaca.markets", "v2", "watchlist123"
        )
        assert result is True
        mock_delete.assert_called_once()

    @patch("alpaca.trader_api.watchlists.requests.delete")
    def test_delete_watchlist_error(self, mock_delete):
        """Test deleting a watchlist with error."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("404 Not Found")
        mock_delete.return_value = mock_response

        result = watchlists.delete_watchlist(
            "key", "secret", "https://api.alpaca.markets", "v2", "watchlist123"
        )
        assert result is False


@pytest.mark.alpaca
@pytest.mark.unit
class TestAlpacaAssets:
    """Test Alpaca assets API."""

    @patch("alpaca.trader_api.assets.requests.get")
    def test_list_assets(self, mock_get):
        """Test listing assets."""
        mock_response = MagicMock()
        mock_response.json.return_value = [{"symbol": "AAPL", "status": "active"}]
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = assets.list_assets("key", "secret", "https://api.alpaca.markets", "v2")
        assert result is not None
        assert len(result) == 1
        mock_get.assert_called_once()

    @patch("alpaca.trader_api.assets.requests.get")
    def test_get_asset(self, mock_get):
        """Test getting a specific asset."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"symbol": "AAPL", "name": "Apple Inc."}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = assets.get_asset("key", "secret", "https://api.alpaca.markets", "v2", "AAPL")
        assert result is not None
        assert result["symbol"] == "AAPL"
        mock_get.assert_called_once()

    @patch("alpaca.trader_api.assets.requests.get")
    def test_get_asset_http_error(self, mock_get):
        """Test get_asset with HTTP error."""
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("404 Not Found")
        mock_get.return_value = mock_response

        result = assets.get_asset("key", "secret", "https://api.alpaca.markets", "v2", "INVALID")
        assert result is None


@pytest.mark.alpaca
@pytest.mark.unit
class TestAlpacaCalendar:
    """Test Alpaca calendar API."""

    @patch("alpaca.trader_api.calendar.requests.get")
    def test_get_calendar(self, mock_get):
        """Test getting calendar."""
        mock_response = MagicMock()
        mock_response.json.return_value = [{"date": "2024-01-01", "open": "09:30"}]
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = calendar.get_calendar("key", "secret", "https://api.alpaca.markets", "v2")
        assert result is not None
        mock_get.assert_called_once()

    @patch("alpaca.trader_api.calendar.requests.get")
    def test_get_calendar_with_dates(self, mock_get):
        """Test getting calendar with date range."""
        mock_response = MagicMock()
        mock_response.json.return_value = [{"date": "2024-01-01"}]
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = calendar.get_calendar(
            "key",
            "secret",
            "https://api.alpaca.markets",
            "v2",
            start="2024-01-01",
            end="2024-01-31",
        )
        assert result is not None
        mock_get.assert_called_once()


@pytest.mark.alpaca
@pytest.mark.unit
class TestAlpacaClock:
    """Test Alpaca clock API."""

    @patch("alpaca.trader_api.clock.requests.get")
    def test_get_clock(self, mock_get):
        """Test getting clock."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"is_open": True, "timestamp": "2024-01-01T09:30:00Z"}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = clock.get_clock("key", "secret", "https://api.alpaca.markets", "v2")
        assert result is not None
        assert result["is_open"] is True
        mock_get.assert_called_once()

    @patch("alpaca.trader_api.clock.requests.get")
    def test_get_clock_http_error(self, mock_get):
        """Test get_clock with HTTP error."""
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("500 Error")
        mock_get.return_value = mock_response

        result = clock.get_clock("key", "secret", "https://api.alpaca.markets", "v2")
        assert result is None


@pytest.mark.alpaca
@pytest.mark.unit
class TestAlpacaCrypto:
    """Test Alpaca crypto API."""

    @patch("alpaca.trader_api.crypto.requests.get")
    def test_list_crypto_assets(self, mock_get):
        """Test listing crypto assets."""
        mock_response = MagicMock()
        mock_response.json.return_value = [{"symbol": "BTCUSD", "status": "active"}]
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = crypto.list_crypto_assets("key", "secret", "https://api.alpaca.markets", "v2")
        assert result is not None
        assert len(result) == 1
        mock_get.assert_called_once()

    @patch("alpaca.trader_api.crypto.requests.post")
    def test_submit_crypto_order(self, mock_post):
        """Test submitting a crypto order."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"id": "crypto_order123", "status": "new"}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        result = crypto.submit_crypto_order(
            "key",
            "secret",
            "https://api.alpaca.markets",
            "v2",
            "BTCUSD",
            0.1,
            "buy",
            "market",
            "day",
        )
        assert result is not None
        assert result["id"] == "crypto_order123"
        mock_post.assert_called_once()


@pytest.mark.alpaca
@pytest.mark.unit
class TestAlpacaHistory:
    """Test Alpaca history API."""

    @patch("alpaca.trader_api.history.requests.get")
    def test_get_barset(self, mock_get):
        """Test getting barset."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"bars": {"AAPL": []}, "next_page_token": ""}
        mock_response.headers = {}
        mock_get.return_value = mock_response

        result = history.get_barset(
            "key",
            "secret",
            "https://api.alpaca.markets",
            "v2",
            ["AAPL"],
            "1Day",
            "2024-01-01",
        )
        assert result is not None
        assert isinstance(result, tuple)
        mock_get.assert_called_once()

    @patch("alpaca.trader_api.history.requests.get")
    def test_get_barset_rate_limit(self, mock_get):
        """Test get_barset with rate limit."""
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_get.return_value = mock_response

        result = history.get_barset(
            "key",
            "secret",
            "https://api.alpaca.markets",
            "v2",
            ["AAPL"],
            "1Day",
            "2024-01-01",
        )
        assert result is not None
        assert isinstance(result, tuple)


@pytest.mark.alpaca
@pytest.mark.unit
class TestAlpacaDataStocks:
    """Test Alpaca stocks data API."""

    @patch("alpaca.trader_api.data.stocks.requests.get")
    def test_get_stock_data(self, mock_get):
        """Test getting stock data."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"bars": []}
        mock_get.return_value = mock_response

        result = stocks.get_stock_data(
            "key", "secret", "v2", "AAPL", "1Day", "2024-01-01", "2024-01-31"
        )
        assert result is not None
        mock_get.assert_called_once()


@pytest.mark.alpaca
@pytest.mark.unit
class TestAlpacaDataCrypto:
    """Test Alpaca crypto data API."""

    @patch("alpaca.trader_api.data.crypto.requests.get")
    def test_get_crypto_data(self, mock_get):
        """Test getting crypto data."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"bars": []}
        mock_get.return_value = mock_response

        result = data_crypto.get_crypto_data(
            "key", "secret", "v2", "BTCUSD", "1Day", "2024-01-01", "2024-01-31"
        )
        assert result is not None
        mock_get.assert_called_once()


@pytest.mark.alpaca
@pytest.mark.unit
class TestAlpacaDataNews:
    """Test Alpaca news data API."""

    @patch("alpaca.trader_api.data.news.requests.get")
    def test_get_news(self, mock_get):
        """Test getting news."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"news": []}
        mock_get.return_value = mock_response

        result = news.get_news("key", "secret", "v2", "AAPL", "2024-01-01", "2024-01-31")
        assert result is not None
        mock_get.assert_called_once()


@pytest.mark.alpaca
@pytest.mark.unit
class TestAlpacaDataOptions:
    """Test Alpaca options data API."""

    @patch("alpaca.trader_api.data.options.requests.get")
    def test_get_options_data(self, mock_get):
        """Test getting options data."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"options": []}
        mock_get.return_value = mock_response

        result = options.get_options_data(
            "key", "secret", "v2", "AAPL", "2024-01-31", 150.0, "call"
        )
        assert result is not None
        mock_get.assert_called_once()


@pytest.mark.alpaca
@pytest.mark.unit
class TestAlpacaDataOther:
    """Test other Alpaca data APIs."""

    @patch("alpaca.trader_api.data.forex.requests.get")
    def test_get_forex_data(self, mock_get):
        """Test getting forex data."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"bars": []}
        mock_get.return_value = mock_response

        result = forex.get_forex_data(
            "key", "secret", "v2", "EURUSD", "1Day", "2024-01-01", "2024-01-31"
        )
        assert result is not None
        mock_get.assert_called_once()

    @patch("alpaca.trader_api.data.logos.requests.get")
    def test_get_logo(self, mock_get):
        """Test getting logo."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"logo": "https://example.com/logo.png"}
        mock_get.return_value = mock_response

        result = logos.get_logo("key", "secret", "v2", "AAPL")
        assert result is not None
        mock_get.assert_called_once()

    @patch("alpaca.trader_api.data.corporate_actions.requests.get")
    def test_get_corporate_actions(self, mock_get):
        """Test getting corporate actions."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"corporate_actions": []}
        mock_get.return_value = mock_response

        result = corporate_actions.get_corporate_actions(
            "key", "secret", "v2", "AAPL", "2024-01-01", "2024-01-31"
        )
        assert result is not None
        mock_get.assert_called_once()

    @patch("alpaca.trader_api.data.screener.requests.get")
    def test_get_screener_data(self, mock_get):
        """Test getting screener data."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"results": []}
        mock_get.return_value = mock_response

        result = screener.get_screener_data("key", "secret", "v2", {"market_cap": ">1000000"})
        assert result is not None
        mock_get.assert_called_once()
