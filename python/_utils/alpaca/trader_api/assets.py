# assets.py
import requests
import logging

def list_assets(api_key, api_secret, base_url, api_version, status='active', asset_class='us_equity'):
    url = f"{base_url}/{api_version}/assets"
    headers = {
        'APCA-API-KEY-ID': api_key,
        'APCA-API-SECRET-KEY': api_secret
    }
    params = {
        'status': status,
        'asset_class': asset_class
    }

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        logging.error(f"HTTP error occurred: {http_err}")
    except Exception as err:
        logging.error(f"An error occurred: {err}")
    return None

def get_asset(api_key, api_secret, base_url, api_version, asset_id_or_symbol):
    url = f"{base_url}/{api_version}/assets/{asset_id_or_symbol}"
    headers = {
        'APCA-API-KEY-ID': api_key,
        'APCA-API-SECRET-KEY': api_secret
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        logging.error(f"HTTP error occurred: {http_err}")
    except Exception as err:
        logging.error(f"An error occurred: {err}")
    return None