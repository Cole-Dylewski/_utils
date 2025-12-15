"""
Vault integration utilities.
"""

import logging
from typing import Any

try:
    import hvac
except ImportError:
    hvac = None

logger = logging.getLogger(__name__)


class VaultHandler:
    """Handler for HashiCorp Vault operations."""

    def __init__(self, vault_addr: str, vault_token: str | None = None):
        """
        Initialize Vault handler.

        :param vault_addr: Vault server address
        :param vault_token: Vault authentication token
        """
        if hvac is None:
            raise ImportError(
                "hvac is required for Vault operations. Install it with: pip install hvac"
            )

        self.vault_addr = vault_addr
        self.vault_token = vault_token
        self.client = hvac.Client(url=vault_addr, token=vault_token)

    def read_secret(self, path: str) -> dict[str, Any] | None:
        """
        Read secret from Vault.

        :param path: Secret path
        :return: Secret data or None
        """
        try:
            response = self.client.secrets.kv.v2.read_secret_version(path=path)
            return response.get("data", {}).get("data")
        except Exception:
            logger.exception("Error reading secret from Vault")
            return None

    def write_secret(self, path: str, data: dict[str, Any]) -> bool:
        """
        Write secret to Vault.

        :param path: Secret path
        :param data: Secret data
        :return: True if successful, False otherwise
        """
        try:
            self.client.secrets.kv.v2.create_or_update_secret(path=path, secret=data)
            return True
        except Exception:
            logger.exception("Error writing secret to Vault")
            return False
