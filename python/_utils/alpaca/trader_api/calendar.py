# calendar.py
import logging

import requests


def get_calendar(api_key, api_secret, base_url, api_version, start=None, end=None):
    url = f"{base_url}/{api_version}/calendar"
    headers = {"APCA-API-KEY-ID": api_key, "APCA-API-SECRET-KEY": api_secret}
    params = {"start": start, "end": end}
    params = {key: value for key, value in params.items() if value is not None}

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        logging.exception(f"HTTP error occurred: {http_err}")
    except Exception as err:
        logging.exception(f"An error occurred: {err}")
    return None
