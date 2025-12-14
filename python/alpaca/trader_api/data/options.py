import requests

def get_options_data(api_key, api_secret, api_version, symbol, expiration_date, strike_price, call_put, limit=100):
    url = f"https://data.alpaca.markets/{api_version}/options"
    headers = {
        "APCA-API-KEY-ID": api_key,
        "APCA-API-SECRET-KEY": api_secret
    }
    params = {
        "symbols": symbol,
        "expiration_date": expiration_date,
        "strike_price": strike_price,
        "call_put": call_put,
        "limit": limit
    }
    response = requests.get(url, headers=headers, params=params)
    return response.json()
