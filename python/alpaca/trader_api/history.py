# history.py
import time

import requests


def get_barset(
    api_key,
    api_secret,
    base_url,
    api_version,
    symbols,
    timeframe,
    start,
    end="",
    limit=1000,
    adjustment="raw",
    feed="iex",
    page_token="",
    premium=False,
):
    """
    Get barset data for multiple symbols using the requests library.

    :param api_key: Alpaca API key
    :param api_secret: Alpaca API secret
    :param base_url: Base URL for Alpaca API
    :param api_version: API version (e.g., 'v2')
    :param symbols: List of ticker symbols.
    :param timeframe: The timeframe for the bars ('minute', '5Min', '15Min', 'hour', 'day').
    :param start: The start date in 'YYYY-MM-DD' format.
    :param end: The end date in 'YYYY-MM-DD' format.
    :param limit: The maximum number of bars to return (optional, default is 1000).
    :param adjustment: The adjustment option for the bars ('raw', 'split', 'dividend', 'all').
    :param feed: The data feed to use ('iex', 'sip').
    :param page_token: The token for paginated requests (optional).
    :param premium: Whether the account has premium data access (default: False).
    :return: A tuple with historical bar data and the next page token.
    """
    timeout_delay = 1
    url = f"{base_url}/{api_version}/stocks/bars"
    headers = {"APCA-API-KEY-ID": api_key, "APCA-API-SECRET-KEY": api_secret}
    symbol_str = ",".join(symbols) if isinstance(symbols, list) else symbols
    if not feed or feed is False:
        if premium:
            feed = "sip"
        else:
            feed = "iex"

    params = {
        "symbols": symbol_str,
        "timeframe": timeframe,
        "start": start,
        "end": end,
        "limit": limit,
        "adjustment": adjustment,
        "feed": feed,
        "page_token": page_token,
    }

    try:
        response = requests.get(url, headers=headers, params=params)
        print(response.headers)
        if response.status_code == 200:
            data = response.json()
            # print(data)
            return data.get("bars", {}), data.get("next_page_token", ""), response.headers

        if response.status_code == 429:
            print(
                "Max limit of API calls per minute reached. Delaying extraction to reset request limit."
            )
            time.sleep(timeout_delay)
            return {}, page_token

        if response.status_code == 422:
            print("Invalid parameters.")
            print(response.status_code)
            print(response.content)
            return {}, None

        print(f"Unexpected error: {response.status_code}")
        print(response.content)
        time.sleep(timeout_delay)
        return {}, page_token

    except Exception as e:
        print(f"An error occurred: {e}")
        time.sleep(timeout_delay)
        return {}, page_token
