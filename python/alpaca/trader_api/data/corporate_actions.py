import requests

def get_corporate_actions(api_key, api_secret, api_version, symbol, start, end='', limit=100):
    url = f"https://data.alpaca.markets/{api_version}/corporate_actions"
    headers = {
        "APCA-API-KEY-ID": api_key,
        "APCA-API-SECRET-KEY": api_secret
    }
    params = {
        "symbols": symbol,
        "start": start,
        "end": end,
        "limit": limit
    }
    response = requests.get(url, headers=headers, params=params)
    return response.json()
