# accounts.py

import requests
import logging

def create_account(base_url, api_version, headers, account_data):
    """
    Create a new account using the provided account data.
    
    :param base_url: Base URL for the API
    :param api_version: API version to use
    :param headers: Headers including authorization
    :param account_data: Dictionary containing account information
    :return: Response JSON from the API
    """
    url = f"{base_url}/{api_version}/accounts"
    try:
        response = requests.post(url, json=account_data, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as err:
        logging.error(f"HTTP error occurred: {err}")
        return None
    except Exception as err:
        logging.error(f"An error occurred: {err}")
        return None

def get_account(base_url, api_version, headers, account_id):
    """
    Retrieve details of a specific account by its ID.
    
    :param base_url: Base URL for the API
    :param api_version: API version to use
    :param headers: Headers including authorization
    :param account_id: ID of the account to retrieve
    :return: Response JSON from the API
    """
    url = f"{base_url}/{api_version}/accounts/{account_id}"
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as err:
        logging.error(f"HTTP error occurred: {err}")
        return None
    except Exception as err:
        logging.error(f"An error occurred: {err}")
        return None

def update_account(base_url, api_version, headers, account_id, update_data):
    """
    Update the details of a specific account.
    
    :param base_url: Base URL for the API
    :param api_version: API version to use
    :param headers: Headers including authorization
    :param account_id: ID of the account to update
    :param update_data: Dictionary containing updated account information
    :return: Response JSON from the API
    """
    url = f"{base_url}/{api_version}/accounts/{account_id}"
    try:
        response = requests.patch(url, json=update_data, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as err:
        logging.error(f"HTTP error occurred: {err}")
        return None
    except Exception as err:
        logging.error(f"An error occurred: {err}")
        return None

def get_all_accounts(base_url, api_version, headers):
    """
    Retrieve details of all accounts.
    
    :param base_url: Base URL for the API
    :param api_version: API version to use
    :param headers: Headers including authorization
    :return: Response JSON from the API
    """
    url = f"{base_url}/{api_version}/accounts"
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as err:
        logging.error(f"HTTP error occurred: {err}")
        return None
    except Exception as err:
        logging.error(f"An error occurred: {err}")
        return None

def get_account_configuration(base_url, api_version, headers, account_id):
    """
    Retrieve configuration settings for a specific account.
    
    :param base_url: Base URL for the API
    :param api_version: API version to use
    :param headers: Headers including authorization
    :param account_id: ID of the account to retrieve configuration for
    :return: Response JSON from the API
    """
    url = f"{base_url}/{api_version}/accounts/{account_id}/account/configurations"
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as err:
        logging.error(f"HTTP error occurred: {err}")
        return None
    except Exception as err:
        logging.error(f"An error occurred: {err}")
        return None

def update_account_configuration(base_url, api_version, headers, account_id, config_data):
    """
    Update the configuration settings of a specific account.
    
    :param base_url: Base URL for the API
    :param api_version: API version to use
    :param headers: Headers including authorization
    :param account_id: ID of the account to update configuration for
    :param config_data: Dictionary containing updated configuration data
    :return: Response JSON from the API
    """
    url = f"{base_url}/{api_version}/accounts/{account_id}/account/configurations"
    try:
        response = requests.patch(url, json=config_data, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as err:
        logging.error(f"HTTP error occurred: {err}")
        return None
    except Exception as err:
        logging.error(f"An error occurred: {err}")
        return None

def get_account_activities(base_url, api_version, headers, account_id):
    """
    Retrieve account activities.
    
    :param base_url: Base URL for the API
    :param api_version: API version to use
    :param headers: Headers including authorization
    :param account_id: ID of the account to retrieve activities for
    :return: Response JSON from the API
    """
    url = f"{base_url}/{api_version}/accounts/{account_id}/account/activities"
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as err:
        logging.error(f"HTTP error occurred: {err}")
        return None
    except Exception as err:
        logging.error(f"An error occurred: {err}")
        return None

def get_account_activities_by_type(base_url, api_version, headers, account_id, activity_type):
    """
    Retrieve account activities filtered by activity type.
    
    :param base_url: Base URL for the API
    :param api_version: API version to use
    :param headers: Headers including authorization
    :param account_id: ID of the account to retrieve activities for
    :param activity_type: Type of activity to filter by
    :return: Response JSON from the API
    """
    url = f"{base_url}/{api_version}/accounts/{account_id}/account/activities/{activity_type}"
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as err:
        logging.error(f"HTTP error occurred: {err}")
        return None
    except Exception as err:
        logging.error(f"An error occurred: {err}")
        return None

def create_funding_account(base_url, api_version, headers, account_id, funding_data):
    """
    Create a new funding account for a specific account.
    
    :param base_url: Base URL for the API
    :param api_version: API version to use
    :param headers: Headers including authorization
    :param account_id: ID of the account to create the funding account for
    :param funding_data: Dictionary containing funding account information
    :return: Response JSON from the API
    """
    url = f"{base_url}/{api_version}/accounts/{account_id}/ach_relationships"
    try:
        response = requests.post(url, json=funding_data, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as err:
        logging.error(f"HTTP error occurred: {err}")
        return None
    except Exception as err:
        logging.error(f"An error occurred: {err}")
        return None

def get_ach_relationships(base_url, api_version, headers, account_id):
    """
    Retrieve ACH relationships for a specific account.
    
    :param base_url: Base URL for the API
    :param api_version: API version to use
    :param headers: Headers including authorization
    :param account_id: ID of the account to retrieve ACH relationships for
    :return: Response JSON from the API
    """
    url = f"{base_url}/{api_version}/accounts/{account_id}/ach_relationships"
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as err:
        logging.error(f"HTTP error occurred: {err}")
        return None
    except Exception as err:
        logging.error(f"An error occurred: {err}")
        return None

def delete_ach_relationship(base_url, api_version, headers, account_id, ach_relationship_id):
    """
    Delete an ACH relationship for a specific account.
    
    :param base_url: Base URL for the API
    :param api_version: API version to use
    :param headers: Headers including authorization
    :param account_id: ID of the account to delete the ACH relationship from
    :param ach_relationship_id: ID of the ACH relationship to delete
    :return: Response JSON from the API
    """
    url = f"{base_url}/{api_version}/accounts/{account_id}/ach_relationships/{ach_relationship_id}"
    try:
        response = requests.delete(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as err:
        logging.error(f"HTTP error occurred: {err}")
        return None
    except Exception as err:
        logging.error(f"An error occurred: {err}")
        return None

def initiate_ach_transfer(base_url, api_version, headers, account_id, transfer_data):
    """
    Initiate an ACH transfer for a specific account.
    
    :param base_url: Base URL for the API
    :param api_version: API version to use
    :param headers: Headers including authorization
    :param account_id: ID of the account to initiate the ACH transfer for
    :param transfer_data: Dictionary containing ACH transfer information
    :return: Response JSON from the API
    """
    url = f"{base_url}/{api_version}/accounts/{account_id}/ach_transfers"
    try:
        response = requests.post(url, json=transfer_data, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as err:
        logging.error(f"HTTP error occurred: {err}")
        return None
    except Exception as err:
        logging.error(f"An error occurred: {err}")
        return None

def get_ach_transfers(base_url, api_version, headers, account_id):
    """
    Retrieve ACH transfers for a specific account.
    
    :param base_url: Base URL for the API
    :param api_version: API version to use
    :param headers: Headers including authorization
    :param account_id: ID of the account to retrieve ACH transfers for
    :return: Response JSON from the API
    """
    url = f"{base_url}/{api_version}/accounts/{account_id}/ach_transfers"
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as err:
        logging.error(f"HTTP error occurred: {err}")
        return None
    except Exception as err:
        logging.error(f"An error occurred: {err}")
        return None

def cancel_ach_transfer(base_url, api_version, headers, account_id, transfer_id):
    """
    Cancel an ACH transfer for a specific account.
    
    :param base_url: Base URL for the API
    :param api_version: API version to use
    :param headers: Headers including authorization
    :param account_id: ID of the account to cancel the ACH transfer for
    :param transfer_id: ID of the ACH transfer to cancel
    :return: Response JSON from the API
    """
    url = f"{base_url}/{api_version}/accounts/{account_id}/ach_transfers/{transfer_id}"
    try:
        response = requests.delete(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as err:
        logging.error(f"HTTP error occurred: {err}")
        return None
    except Exception as err:
        logging.error(f"An error occurred: {err}")
        return None
