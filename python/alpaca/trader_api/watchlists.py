# watchlists.py
import requests
import logging

def create_watchlist(api_key, api_secret, base_url, api_version, name, symbols):
    url = f"{base_url}/{api_version}/watchlists"
    headers = {
        'APCA-API-KEY-ID': api_key,
        'APCA-API-SECRET-KEY': api_secret
    }
    data = {
        'name': name,
        'symbols': symbols
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        logging.error(f"HTTP error occurred: {http_err}")
    except Exception as err:
        logging.error(f"An error occurred: {err}")
    return None

def get_watchlist(api_key, api_secret, base_url, api_version, watchlist_id):
    url = f"{base_url}/{api_version}/watchlists/{watchlist_id}"
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

def update_watchlist(api_key, api_secret, base_url, api_version, watchlist_id, symbols):
    url = f"{base_url}/{api_version}/watchlists/{watchlist_id}"
    headers = {
        'APCA-API-KEY-ID': api_key,
        'APCA-API-SECRET-KEY': api_secret
    }
    data = {
        'symbols': symbols
    }

    try:
        response = requests.put(url, headers=headers, json=data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        logging.error(f"HTTP error occurred: {http_err}")
    except Exception as err:
        logging.error(f"An error occurred: {err}")
    return None

def delete_watchlist(api_key, api_secret, base_url, api_version, watchlist_id):
    url = f"{base_url}/{api_version}/watchlists/{watchlist_id}"
    headers = {
        'APCA-API-KEY-ID': api_key,
        'APCA-API-SECRET-KEY': api_secret
    }

    try:
        response = requests.delete(url, headers=headers)
        response.raise_for_status()
        return response.status_code == 204
    except requests.exceptions.HTTPError as http_err:
        logging.error(f"HTTP error occurred: {http_err}")
    except Exception as err:
        logging.error(f"An error occurred: {err}")
    return False
