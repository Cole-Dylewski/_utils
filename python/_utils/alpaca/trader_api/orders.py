# orders.py
import requests
import logging

def submit_order(api_key, api_secret, base_url, api_version, symbol, qty, side, order_type, time_in_force, limit_price=None, stop_price=None, client_order_id=None):
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
        'time_in_force': time_in_force
    }
    if limit_price:
        order_data['limit_price'] = limit_price
    if stop_price:
        order_data['stop_price'] = stop_price
    if client_order_id:
        order_data['client_order_id'] = client_order_id

    try:
        response = requests.post(url, headers=headers, json=order_data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        logging.error(f"HTTP error occurred: {http_err}")
    except Exception as err:
        logging.error(f"An error occurred: {err}")
    return None

def list_orders(api_key, api_secret, base_url, api_version, status='open', limit=50, after=None, until=None, direction='desc'):
    url = f"{base_url}/{api_version}/orders"
    headers = {
        'APCA-API-KEY-ID': api_key,
        'APCA-API-SECRET-KEY': api_secret
    }
    params = {
        'status': status,
        'limit': limit,
        'after': after,
        'until': until,
        'direction': direction
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

def get_order(api_key, api_secret, base_url, api_version, order_id):
    url = f"{base_url}/{api_version}/orders/{order_id}"
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

def replace_order(api_key, api_secret, base_url, api_version, order_id, qty=None, limit_price=None, stop_price=None, time_in_force=None):
    url = f"{base_url}/{api_version}/orders/{order_id}"
    headers = {
        'APCA-API-KEY-ID': api_key,
        'APCA-API-SECRET-KEY': api_secret
    }
    order_data = {}
    if qty:
        order_data['qty'] = qty
    if limit_price:
        order_data['limit_price'] = limit_price
    if stop_price:
        order_data['stop_price'] = stop_price
    if time_in_force:
        order_data['time_in_force'] = time_in_force

    try:
        response = requests.patch(url, headers=headers, json=order_data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        logging.error(f"HTTP error occurred: {http_err}")
    except Exception as err:
        logging.error(f"An error occurred: {err}")
    return None

def cancel_order(api_key, api_secret, base_url, api_version, order_id):
    url = f"{base_url}/{api_version}/orders/{order_id}"
    headers = {
        'APCA-API-KEY-ID': api_key,
        'APCA-API-SECRET-KEY': api_secret
    }

    try:
        response = requests.delete(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        logging.error(f"HTTP error occurred: {http_err}")
    except Exception as err:
        logging.error(f"An error occurred: {err}")
    return None
