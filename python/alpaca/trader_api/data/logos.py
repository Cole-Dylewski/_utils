import requests

def get_logo(api_key, api_secret, api_version, symbol):
    url = f"https://data.alpaca.markets/{api_version}/logos/{symbol}"
    headers = {
        "APCA-API-KEY-ID": api_key,
        "APCA-API-SECRET-KEY": api_secret
    }
    response = requests.get(url, headers=headers)
    return response.json()
