import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

from _utils.alpaca.trader_api import (
    accounts,
    assets,
    calendar,
    clock,
    data,
    history,
    orders,
    portfolio,
    watchlists,
)


class TraderClient:
    def __init__(
        self,
        api_key,
        api_secret,
        base_url=r"https://paper-api.alpaca.markets",
        api_version="v2",
        premium=False,
        printVerbose=False,
    ):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = base_url
        self.api_version = api_version
        self.premium = premium
        self.printVerbose = printVerbose

    # Account related methods
    def get_account(self):
        try:
            return accounts.get_account(
                self.api_key, self.api_secret, self.base_url, self.api_version
            )
        except Exception as e:
            logging.exception(f"An error occurred: {e}")

    def get_account_configurations(self):
        try:
            return accounts.get_account_configurations(
                self.api_key, self.api_secret, self.base_url, self.api_version
            )
        except Exception as e:
            logging.exception(f"An error occurred: {e}")

    def get_account_activities(self):
        try:
            return accounts.get_account_activities(
                self.api_key, self.api_secret, self.base_url, self.api_version
            )
        except Exception as e:
            logging.exception(f"An error occurred: {e}")

    # Asset related methods
    def get_assets(self, status="active"):
        try:
            return assets.list_assets(
                self.api_key, self.api_secret, self.base_url, self.api_version, status
            )
        except Exception as e:
            logging.exception(f"An error occurred: {e}")

    # Order related methods
    def submit_order(self, symbol, qty, side, order_type, time_in_force):
        try:
            return orders.submit_order(
                self.api_key,
                self.api_secret,
                self.base_url,
                self.api_version,
                symbol,
                qty,
                side,
                order_type,
                time_in_force,
            )
        except Exception as e:
            logging.exception(f"An error occurred: {e}")

    def get_order(self, order_id):
        try:
            return orders.get_order(
                self.api_key, self.api_secret, self.base_url, self.api_version, order_id
            )
        except Exception as e:
            logging.exception(f"An error occurred: {e}")

    def list_orders(self):
        try:
            return orders.list_orders(
                self.api_key, self.api_secret, self.base_url, self.api_version
            )
        except Exception as e:
            logging.exception(f"An error occurred: {e}")

    def cancel_order(self, order_id):
        try:
            return orders.cancel_order(
                self.api_key, self.api_secret, self.base_url, self.api_version, order_id
            )
        except Exception as e:
            logging.exception(f"An error occurred: {e}")

    # Portfolio related methods
    def get_positions(self):
        try:
            return portfolio.get_positions(
                self.api_key, self.api_secret, self.base_url, self.api_version
            )
        except Exception as e:
            logging.exception(f"An error occurred: {e}")

    def get_portfolio_history(
        self, period=None, timeframe=None, date_end=None, extended_hours=False
    ):
        try:
            return portfolio.get_portfolio_history(
                self.api_key,
                self.api_secret,
                self.base_url,
                self.api_version,
                period,
                timeframe,
                date_end,
                extended_hours,
            )
        except Exception as e:
            logging.exception(f"An error occurred: {e}")

    # Watchlist related methods
    def get_watchlists(self):
        """Get all watchlists by listing them from the API."""
        try:
            # Note: Alpaca API doesn't have a direct "list all watchlists" endpoint
            # This would need to be implemented differently or removed
            # For now, we'll use get_watchlist with a known ID or implement a workaround
            logging.warning(
                "get_watchlists() is not directly supported by Alpaca API. Consider using get_watchlist() with specific watchlist IDs."
            )
            return
        except Exception as e:
            logging.exception(f"An error occurred: {e}")

    def get_watchlist(self, watchlist_id):
        try:
            return watchlists.get_watchlist(
                self.api_key, self.api_secret, self.base_url, self.api_version, watchlist_id
            )
        except Exception as e:
            logging.exception(f"An error occurred: {e}")

    def create_watchlist(self, name, symbols):
        try:
            return watchlists.create_watchlist(
                self.api_key, self.api_secret, self.base_url, self.api_version, name, symbols
            )
        except Exception as e:
            logging.exception(f"An error occurred: {e}")

    def update_watchlist(self, watchlist_id, symbols):
        try:
            return watchlists.update_watchlist(
                self.api_key,
                self.api_secret,
                self.base_url,
                self.api_version,
                watchlist_id,
                symbols,
            )
        except Exception as e:
            logging.exception(f"An error occurred: {e}")

    def delete_watchlist(self, watchlist_id):
        try:
            return watchlists.delete_watchlist(
                self.api_key, self.api_secret, self.base_url, self.api_version, watchlist_id
            )
        except Exception as e:
            logging.exception(f"An error occurred: {e}")

    # Calendar related methods
    def get_calendar(self, start, end=""):
        try:
            return calendar.get_calendar(
                self.api_key, self.api_secret, self.base_url, self.api_version, start, end
            )
        except Exception as e:
            logging.exception(f"An error occurred: {e}")

    # Clock related methods
    def get_clock(self):
        try:
            return clock.get_clock(self.api_key, self.api_secret, self.base_url, self.api_version)
        except Exception as e:
            logging.exception(f"An error occurred: {e}")

    # Crypto related methods
    def get_crypto_bars(
        self,
        symbols,
        timeframe,
        start,
        end="",
        limit=1000,
        adjustment="raw",
        feed="sip",
        page_token="",
    ):
        try:
            # Convert symbols to string if it's a list
            symbol_str = ",".join(symbols) if isinstance(symbols, list) else symbols
            return data.crypto.get_crypto_data(
                self.api_key,
                self.api_secret,
                self.api_version,
                symbol_str,
                timeframe,
                start,
                end,
                limit,
                adjustment,
                feed,
            )
        except Exception as e:
            logging.exception(f"An error occurred: {e}")

    def get_crypto_funding(self, symbol, start, end="", limit=1000):
        """
        Get crypto funding rates.
        Note: This function is not yet implemented in the crypto module.
        """
        try:
            logging.warning("get_crypto_funding() is not yet implemented in the crypto module.")
            return
        except Exception as e:
            logging.exception(f"An error occurred: {e}")

    # History related methods
    def get_barset(
        self,
        symbols,
        timeframe,
        start,
        end="",
        limit=1000,
        adjustment="raw",
        feed=False,
        page_token="",
    ):
        try:
            return history.get_barset(
                self.api_key,
                self.api_secret,
                self.base_url,
                self.api_version,
                symbols,
                timeframe,
                start,
                end,
                limit,
                adjustment,
                feed,
                page_token,
                self.premium,
            )
        except Exception as e:
            logging.exception(f"An error occurred: {e}")

    # Data related methods
    def get_stock_data(
        self, symbol, timeframe, start, end="", limit=1000, adjustment="raw", feed=False
    ):
        try:
            return data.stocks.get_stock_data(
                self.api_key,
                self.api_secret,
                self.api_version,
                symbol,
                timeframe,
                start,
                end,
                limit,
                adjustment,
                feed,
            )
        except Exception as e:
            logging.exception(f"An error occurred: {e}")

    def get_crypto_data(
        self, symbol, timeframe, start, end="", limit=1000, adjustment="raw", feed=False
    ):
        try:
            return data.crypto.get_crypto_data(
                self.api_key,
                self.api_secret,
                self.api_version,
                symbol,
                timeframe,
                start,
                end,
                limit,
                adjustment,
                feed,
            )
        except Exception as e:
            logging.exception(f"An error occurred: {e}")

    def get_forex_data(
        self, symbol, timeframe, start, end="", limit=1000, adjustment="raw", feed=False
    ):
        try:
            return data.forex.get_forex_data(
                self.api_key,
                self.api_secret,
                self.api_version,
                symbol,
                timeframe,
                start,
                end,
                limit,
                adjustment,
                feed,
            )
        except Exception as e:
            logging.exception(f"An error occurred: {e}")

    def get_logo(self, symbol):
        try:
            return data.logos.get_logo(self.api_key, self.api_secret, self.api_version, symbol)
        except Exception as e:
            logging.exception(f"An error occurred: {e}")

    def get_screener_data(self, filter, limit=100):
        try:
            return data.screener.get_screener_data(
                self.api_key, self.api_secret, self.api_version, filter, limit
            )
        except Exception as e:
            logging.exception(f"An error occurred: {e}")

    def get_news(self, symbol, start, end="", limit=100):
        try:
            return data.news.get_news(
                self.api_key, self.api_secret, self.api_version, symbol, start, end, limit
            )
        except Exception as e:
            logging.exception(f"An error occurred: {e}")

    def get_corporate_actions(self, symbol, start, end="", limit=100):
        try:
            return data.corporate_actions.get_corporate_actions(
                self.api_key, self.api_secret, self.api_version, symbol, start, end, limit
            )
        except Exception as e:
            logging.exception(f"An error occurred: {e}")

    def get_options_data(self, symbol, expiration_date, strike_price, call_put, limit=100):
        try:
            return data.options.get_options_data(
                self.api_key,
                self.api_secret,
                self.api_version,
                symbol,
                expiration_date,
                strike_price,
                call_put,
                limit,
            )
        except Exception as e:
            logging.exception(f"An error occurred: {e}")


def main():
    # Replace these with your actual Alpaca API credentials
    API_KEY = "your_api_key"
    API_SECRET = "your_api_secret"
    BASE_URL = "https://paper-api.alpaca.markets"  # or the live URL for live trading
    API_VERSION = "v2"

    # Initialize the Alpaca client
    client = TraderClient(API_KEY, API_SECRET, BASE_URL, API_VERSION)

    # Example usage of various methods

    # Get account details
    try:
        account_info = client.get_account()
        print("Account Info:", account_info)
    except Exception as e:
        print(f"Failed to get account info: {e}")

    # Get account configurations
    try:
        account_configurations = client.get_account_configurations()
        print("Account Configurations:", account_configurations)
    except Exception as e:
        print(f"Failed to get account configurations: {e}")

    # Get account activities
    try:
        account_activities = client.get_account_activities()
        print("Account Activities:", account_activities)
    except Exception as e:
        print(f"Failed to get account activities: {e}")

    # Get assets
    try:
        active_assets = client.get_assets(status="active")
        print("Active Assets:", active_assets)
    except Exception as e:
        print(f"Failed to get assets: {e}")

    # Submit an order
    try:
        order = client.submit_order(
            symbol="AAPL", qty=1, side="buy", order_type="market", time_in_force="gtc"
        )
        print("Order Submitted:", order)
    except Exception as e:
        print(f"Failed to submit order: {e}")

    # Get positions
    try:
        positions = client.get_positions()
        print("Positions:", positions)
    except Exception as e:
        print(f"Failed to get positions: {e}")

    # Manage watchlists
    try:
        watchlists = client.get_watchlists()
        print("Watchlists:", watchlists)
    except Exception as e:
        print(f"Failed to get watchlists: {e}")

    # Example of creating a watchlist
    try:
        new_watchlist = client.create_watchlist(name="My Watchlist", symbols=["AAPL", "TSLA"])
        print("New Watchlist Created:", new_watchlist)
    except Exception as e:
        print(f"Failed to create watchlist: {e}")

    # Example of updating a watchlist (note: name parameter removed)
    try:
        updated_watchlist = client.update_watchlist(
            watchlist_id="watchlist-id", symbols=["AAPL", "TSLA", "MSFT"]
        )
        print("Watchlist Updated:", updated_watchlist)
    except Exception as e:
        print(f"Failed to update watchlist: {e}")

    # Get calendar events
    try:
        calendar_events = client.get_calendar(start="2023-01-01", end="2023-01-31")
        print("Calendar Events:", calendar_events)
    except Exception as e:
        print(f"Failed to get calendar events: {e}")

    # Get clock information
    try:
        clock_info = client.get_clock()
        print("Market Clock:", clock_info)
    except Exception as e:
        print(f"Failed to get clock info: {e}")

    # Get stock data
    try:
        stock_data = client.get_stock_data(
            symbol="AAPL", timeframe="day", start="2023-01-01", end="2023-01-31"
        )
        print("Stock Data:", stock_data)
    except Exception as e:
        print(f"Failed to get stock data: {e}")

    # Get crypto data
    try:
        crypto_data = client.get_crypto_data(
            symbol="BTCUSD", timeframe="day", start="2023-01-01", end="2023-01-31"
        )
        print("Crypto Data:", crypto_data)
    except Exception as e:
        print(f"Failed to get crypto data: {e}")

    # Get forex data
    try:
        forex_data = client.get_forex_data(
            symbol="EURUSD", timeframe="day", start="2023-01-01", end="2023-01-31"
        )
        print("Forex Data:", forex_data)
    except Exception as e:
        print(f"Failed to get forex data: {e}")

    # Get company logo
    try:
        logo = client.get_logo(symbol="AAPL")
        print("Company Logo URL:", logo)
    except Exception as e:
        print(f"Failed to get company logo: {e}")

    # Get news
    try:
        news = client.get_news(symbol="AAPL", start="2023-01-01", end="2023-01-31")
        print("News:", news)
    except Exception as e:
        print(f"Failed to get news: {e}")

    # Get corporate actions
    try:
        corporate_actions = client.get_corporate_actions(
            symbol="AAPL", start="2023-01-01", end="2023-01-31"
        )
        print("Corporate Actions:", corporate_actions)
    except Exception as e:
        print(f"Failed to get corporate actions: {e}")

    # Get options data
    try:
        options_data = client.get_options_data(
            symbol="AAPL", expiration_date="2023-08-16", strike_price=150, call_put="call"
        )
        print("Options Data:", options_data)
    except Exception as e:
        print(f"Failed to get options data: {e}")


if __name__ == "__main__":
    main()
