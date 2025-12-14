# accounts.py
import requests
import logging

def get_account(api_key, api_secret, base_url, api_version):
    url = f"{base_url}/{api_version}/account"
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

def get_account_configurations(api_key, api_secret, base_url, api_version):
    url = f"{base_url}/{api_version}/account/configurations"
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

def update_account_configurations(api_key, api_secret, base_url, api_version, **configurations):
    url = f"{base_url}/{api_version}/account/configurations"
    headers = {
        'APCA-API-KEY-ID': api_key,
        'APCA-API-SECRET-KEY': api_secret
    }
    data = configurations

    try:
        response = requests.patch(url, headers=headers, json=data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        logging.error(f"HTTP error occurred: {http_err}")
    except Exception as err:
        logging.error(f"An error occurred: {err}")
    return None

def get_account_activities(api_key, api_secret, base_url, api_version, activity_type=None, date=None, until=None, after=None, direction=None, page_size=None, page_token=None):
    url = f"{base_url}/{api_version}/account/activities"
    headers = {
        'APCA-API-KEY-ID': api_key,
        'APCA-API-SECRET-KEY': api_secret
    }
    params = {
        'activity_type': activity_type,
        'date': date,
        'until': until,
        'after': after,
        'direction': direction,
        'page_size': page_size,
        'page_token': page_token
    }
    params = {key: value for key, value in params.items() if value is not None}

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        logging.error(f"HTTP error occurred: {http_err}")
    except Exception as err:
        logging.error(f"An error occurred: {err}")
    return None
