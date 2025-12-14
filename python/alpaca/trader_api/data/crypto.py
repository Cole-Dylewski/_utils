import requests

def get_crypto_data(api_key, api_secret, api_version, symbol, timeframe, start, end='', limit=1000, adjustment='raw', feed='sip'):
    url = f"https://data.alpaca.markets/{api_version}/crypto/bars"
    headers = {
        "APCA-API-KEY-ID": api_key,
        "APCA-API-SECRET-KEY": api_secret
    }
    params = {
        "symbols": symbol,
        "timeframe": timeframe,
        "start": start,
        "end": end,
        "limit": limit,
        "adjustment": adjustment,
        "feed": feed
    }
    response = requests.get(url, headers=headers, params=params)
    return response.json()
