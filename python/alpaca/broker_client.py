# broker_client.py

import logging
import base64
from _utils.alpaca.broker_api import accounts

# Configure logging to display information with timestamps and severity level
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class BrokerClient:
    def __init__(self, api_key, api_secret, base_url=r'https://broker-api.sandbox.alpaca.markets', api_version='v1'):
        """
        Initialize the BrokerClient with API credentials and base URL.
        
        :param api_key: API key provided by Alpaca
        :param api_secret: API secret provided by Alpaca
        :param base_url: Base URL for the Alpaca Broker API
        :param api_version: API version to use (default is 'v1')
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = base_url
        self.api_version = api_version

        # Base64 encode the API key and secret
        credentials = f"{self.api_key}:{self.api_secret}".encode('utf-8')
        encoded_credentials = base64.b64encode(credentials).decode('utf-8')

        # Store the headers with base64-encoded credentials
        self.headers = {
            'Authorization': f"Basic {encoded_credentials}"
        }

    def create_account(self, account_data):
        """
        Create a new account using the provided account data.
        
        :param account_data: Dictionary containing account information
        :return: Response JSON from the API
        """
        return accounts.create_account(self.base_url, self.api_version, self.headers, account_data)

    def get_account(self, account_id):
        """
        Retrieve details of a specific account by its ID.
        
        :param account_id: ID of the account to retrieve
        :return: Response JSON from the API
        """
        return accounts.get_account(self.base_url, self.api_version, self.headers, account_id)

    def update_account(self, account_id, update_data):
        """
        Update the details of a specific account.
        
        :param account_id: ID of the account to update
        :param update_data: Dictionary containing updated account information
        :return: Response JSON from the API
        """
        return accounts.update_account(self.base_url, self.api_version, self.headers, account_id, update_data)

    def get_all_accounts(self):
        """
        Retrieve details of all accounts.
        
        :return: Response JSON from the API
        """
        return accounts.get_all_accounts(self.base_url, self.api_version, self.headers)

    def get_account_configuration(self, account_id):
        """
        Retrieve configuration settings for a specific account.
        
        :param account_id: ID of the account to retrieve configuration for
        :return: Response JSON from the API
        """
        return accounts.get_account_configuration(self.base_url, self.api_version, self.headers, account_id)

    def update_account_configuration(self, account_id, config_data):
        """
        Update the configuration settings of a specific account.
        
        :param account_id: ID of the account to update configuration for
        :param config_data: Dictionary containing updated configuration data
        :return: Response JSON from the API
        """
        return accounts.update_account_configuration(self.base_url, self.api_version, self.headers, account_id, config_data)

    def get_account_activities(self, account_id, activity_type=None):
        """
        Retrieve account activities. Optionally filter by activity type.
        
        :param account_id: ID of the account to retrieve activities for
        :param activity_type: Optional activity type to filter by
        :return: Response JSON from the API
        """
        if activity_type:
            return accounts.get_account_activities_by_type(self.base_url, self.api_version, self.headers, account_id, activity_type)
        else:
            return accounts.get_account_activities(self.base_url, self.api_version, self.headers, account_id)

    def create_funding_account(self, account_id, funding_data):
        """
        Create a new funding account for a specific account.
        
        :param account_id: ID of the account to create the funding account for
        :param funding_data: Dictionary containing funding account information
        :return: Response JSON from the API
        """
        return accounts.create_funding_account(self.base_url, self.api_version, self.headers, account_id, funding_data)

    def get_ach_relationships(self, account_id):
        """
        Retrieve ACH relationships for a specific account.
        
        :param account_id: ID of the account to retrieve ACH relationships for
        :return: Response JSON from the API
        """
        return accounts.get_ach_relationships(self.base_url, self.api_version, self.headers, account_id)

    def delete_ach_relationship(self, account_id, ach_relationship_id):
        """
        Delete an ACH relationship for a specific account.
        
        :param account_id: ID of the account to delete the ACH relationship from
        :param ach_relationship_id: ID of the ACH relationship to delete
        :return: Response JSON from the API
        """
        return accounts.delete_ach_relationship(self.base_url, self.api_version, self.headers, account_id, ach_relationship_id)

    def initiate_ach_transfer(self, account_id, transfer_data):
        """
        Initiate an ACH transfer for a specific account.
        
        :param account_id: ID of the account to initiate the ACH transfer for
        :param transfer_data: Dictionary containing ACH transfer information
        :return: Response JSON from the API
        """
        return accounts.initiate_ach_transfer(self.base_url, self.api_version, self.headers, account_id, transfer_data)

    def get_ach_transfers(self, account_id):
        """
        Retrieve ACH transfers for a specific account.
        
        :param account_id: ID of the account to retrieve ACH transfers for
        :return: Response JSON from the API
        """
        return accounts.get_ach_transfers(self.base_url, self.api_version, self.headers, account_id)

    def cancel_ach_transfer(self, account_id, transfer_id):
        """
        Cancel an ACH transfer for a specific account.
        
        :param account_id: ID of the account to cancel the ACH transfer for
        :param transfer_id: ID of the ACH transfer to cancel
        :return: Response JSON from the API
        """
        return accounts.cancel_ach_transfer(self.base_url, self.api_version, self.headers, account_id, transfer_id)
