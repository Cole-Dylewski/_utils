import requests

def get_screener_data(api_key, api_secret, api_version, filter, limit=100):
    url = f"https://data.alpaca.markets/{api_version}/screener"
    headers = {
        "APCA-API-KEY-ID": api_key,
        "APCA-API-SECRET-KEY": api_secret
    }
    params = {
        "filter": filter,
        "limit": limit
    }
    response = requests.get(url, headers=headers, params=params)
    return response.json()
