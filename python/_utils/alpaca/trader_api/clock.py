# clock.py
import logging

import requests


def get_clock(api_key, api_secret, base_url, api_version):
    url = f"{base_url}/{api_version}/clock"
    headers = {"APCA-API-KEY-ID": api_key, "APCA-API-SECRET-KEY": api_secret}

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        logging.exception(f"HTTP error occurred: {http_err}")
    except Exception as err:
        logging.exception(f"An error occurred: {err}")
    return None
