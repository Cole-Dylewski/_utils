"""
Tests for app deployment utilities.
"""

import pytest
from server_management.app_deployment import (
    AppDeploymentConfig,
    Credentials,
    EnvironmentType,
    ServerConfig,
    VaultConfig,
)


@pytest.mark.unit
class TestAppDeploymentConfig:
    """Test AppDeploymentConfig classes."""

    def test_server_config_initialization(self):
        """Test ServerConfig initialization."""
        config = ServerConfig(host="test-host", user="testuser")
        assert config.host == "test-host"
        assert config.user == "testuser"
        assert config.port == 22

    def test_server_config_missing_host(self):
        """Test ServerConfig with missing host raises error."""
        with pytest.raises(ValueError, match="host is required"):
            ServerConfig(host="", user="testuser")

    def test_server_config_missing_user(self):
        """Test ServerConfig with missing user raises error."""
        with pytest.raises(ValueError, match="user is required"):
            ServerConfig(host="test-host", user="")

    def test_vault_config_initialization(self):
        """Test VaultConfig initialization."""
        config = VaultConfig(vault_addr="http://vault:8200")
        assert config.vault_addr == "http://vault:8200"
        assert config.base_path == "ipsa"

    def test_vault_config_missing_addr(self):
        """Test VaultConfig with missing address raises error."""
        with pytest.raises(ValueError, match="vault_addr is required"):
            VaultConfig(vault_addr="")

    def test_credentials_initialization(self):
        """Test Credentials initialization."""
        creds = Credentials(database_password="testpass")
        assert creds.database_password == "testpass"
        assert isinstance(creds.api_keys, dict)
        assert isinstance(creds.secrets, dict)

    def test_environment_type_enum(self):
        """Test EnvironmentType enum."""
        assert EnvironmentType.DEMO.value == "demo"
        assert EnvironmentType.STAGING.value == "staging"
        assert EnvironmentType.PROD.value == "prod"
        assert EnvironmentType.DEV.value == "dev"
