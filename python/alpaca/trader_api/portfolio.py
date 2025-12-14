# portfolio.py
import requests
import logging

def get_positions(api_key, api_secret, base_url, api_version):
    url = f"{base_url}/{api_version}/positions"
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

def get_portfolio_history(api_key, api_secret, base_url, api_version, period=None, timeframe=None, date_end=None, extended_hours=False):
    url = f"{base_url}/{api_version}/account/portfolio/history"
    headers = {
        'APCA-API-KEY-ID': api_key,
        'APCA-API-SECRET-KEY': api_secret
    }
    params = {
        'period': period,
        'timeframe': timeframe,
        'date_end': date_end,
        'extended_hours': extended_hours
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
