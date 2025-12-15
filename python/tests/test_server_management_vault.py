"""
Tests for Vault utilities.
"""

from unittest.mock import MagicMock, patch

import pytest
from server_management.vault import VaultHandler


@pytest.mark.unit
@pytest.mark.vault
class TestVaultHandler:
    """Test VaultHandler class."""

    @patch("server_management.vault.hvac.Client")
    def test_vault_handler_initialization(self, mock_hvac):
        """Test VaultHandler initialization."""
        mock_client = MagicMock()
        mock_client.is_authenticated.return_value = True
        mock_hvac.return_value = mock_client

        handler = VaultHandler(vault_addr="http://vault:8200", vault_token="test-token")
        assert handler.vault_addr == "http://vault:8200"
        assert handler.vault_token == "test-token"
        mock_hvac.assert_called_once()

    @patch("server_management.vault.hvac.Client")
    def test_vault_handler_read_secret(self, mock_hvac):
        """Test reading secret from Vault."""
        mock_client = MagicMock()
        mock_client.is_authenticated.return_value = True
        mock_client.secrets.kv.v2.read_secret_version.return_value = {
            "data": {"data": {"key": "value"}}
        }
        mock_hvac.return_value = mock_client

        handler = VaultHandler(vault_addr="http://vault:8200", vault_token="test-token")
        secret = handler.read_secret("test/path")
        assert secret is not None
        assert "key" in secret
        mock_client.secrets.kv.v2.read_secret_version.assert_called_once()

    @patch("server_management.vault.hvac.Client")
    def test_vault_handler_write_secret(self, mock_hvac):
        """Test writing secret to Vault."""
        mock_client = MagicMock()
        mock_client.is_authenticated.return_value = True
        mock_client.secrets.kv.v2.create_or_update_secret.return_value = {}
        mock_hvac.return_value = mock_client

        handler = VaultHandler(vault_addr="http://vault:8200", vault_token="test-token")
        result = handler.write_secret("test/path", {"key": "value"})
        assert result is not None
        mock_client.secrets.kv.v2.create_or_update_secret.assert_called_once()
