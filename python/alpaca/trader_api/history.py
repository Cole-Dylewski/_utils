# history.py
import requests, time
import logging

def get_barset(self, symbols, timeframe, start, end = '', limit=1000, adjustment='raw', feed=False, page_token=''):
        timeout_delay = 1
        """
        Get barset data for multiple symbols using the requests library.

        :param symbols: List of ticker symbols.
        :param timeframe: The timeframe for the bars ('minute', '5Min', '15Min', 'hour', 'day').
        :param start: The start date in 'YYYY-MM-DD' format.
        :param end: The end date in 'YYYY-MM-DD' format.
        :param limit: The maximum number of bars to return (optional, default is 1000).
        :param adjustment: The adjustment option for the bars ('raw', 'split', 'dividend', 'all').
        :param feed: The data feed to use ('iex', 'sip').
        :param page_token: The token for paginated requests (optional).
        :return: A tuple with historical bar data and the next page token.
        """
        url = f"https://data.alpaca.markets/{self.api_version}/stocks/bars"
        headers = {
            "APCA-API-KEY-ID": self.api_key,
            "APCA-API-SECRET-KEY": self.api_secret
        }
        symbol_str = ','.join(symbols)
        if not feed:
            if self.premium:
                feed = 'sip'
            else:
                feed = 'iex'
        params = {
            "symbols": symbol_str,
            "timeframe": timeframe,
            "start": start,
            "end": end,
            "limit": limit,
            "adjustment": adjustment,
            "feed": feed,
            'page_token': page_token
        }

        try:
            response = requests.get(url, headers=headers, params=params)
            print(response.headers)
            if response.status_code == 200:
                data = response.json()
                # print(data)
                return data.get('bars', {}), data.get('next_page_token', ''), response.headers
            
            elif response.status_code == 429:
                print("Max limit of API calls per minute reached. Delaying extraction to reset request limit.")
                time.sleep(timeout_delay)
                return {}, page_token
            
            elif response.status_code == 422:
                print("Invalid parameters.")
                print(response.status_code)
                print(response.content)
                return {}, None
            
            else:
                print(f"Unexpected error: {response.status_code}")
                print(response.content)
                time.sleep(timeout_delay)
                return {}, page_token

        except Exception as e:
            print(f"An error occurred: {e}")
            time.sleep(timeout_delay)
            return {}, page_token