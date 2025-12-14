# crypto.py
import requests
import logging

def list_crypto_assets(api_key, api_secret, base_url, api_version, status='active', asset_class='crypto'):
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

def submit_crypto_order(api_key, api_secret, base_url, api_version, symbol, qty, side, order_type, time_in_force, limit_price=None, stop_price=None, client_order_id=None):
    url = f"{base_url}/{api_version}/orders"
    headers = {
        'APCA-API-KEY-ID': api_key,
        'APCA-API-SECRET-KEY': api_secret
    }
    order_data = {
        'symbol': symbol,
        'qty': qty,
        'side': side,
        'type': order_type,
        'time_in_force': time_in_force,
        'client_order_id': client_order_id,
        'asset_class': 'crypto'
    }

    if limit_price:
        order_data['limit_price'] = limit_price
    if stop_price:
        order_data['stop_price'] = stop_price

    try:
        response = requests.post(url, headers=headers, json=order_data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        logging.error(f"HTTP error occurred: {http_err}")
    except Exception as err:
        logging.error(f"An error occurred: {err}")
    return None
