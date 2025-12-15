"""
Pytest configuration and shared fixtures.
"""

import os
from typing import Any
from unittest.mock import MagicMock, Mock, patch

import pytest

# Register custom markers to avoid warnings with --strict-markers
# Markers are also defined in pytest.ini and pyproject.toml, but registering here ensures they're available
pytest_plugins = []


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line("markers", "unit: Unit tests (fast, no external dependencies)")
    config.addinivalue_line("markers", "integration: Integration tests (may use mocks)")
    config.addinivalue_line("markers", "slow: Slow running tests")
    config.addinivalue_line("markers", "aws: Tests requiring AWS services")
    config.addinivalue_line("markers", "alpaca: Tests requiring Alpaca API")
    config.addinivalue_line("markers", "vault: Tests requiring Vault")
    config.addinivalue_line("markers", "terraform: Tests requiring Terraform")
    config.addinivalue_line("markers", "ansible: Tests requiring Ansible")
    config.addinivalue_line("markers", "requires_network: Tests requiring network access")
    config.addinivalue_line("markers", "requires_docker: Tests requiring Docker")


# Set test environment variables
os.environ.setdefault("AWS_ACCESS_KEY_ID", "testing")
os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "testing")
os.environ.setdefault("AWS_DEFAULT_REGION", "us-east-1")
os.environ.setdefault("AWS_SECURITY_TOKEN", "testing")
os.environ.setdefault("AWS_SESSION_TOKEN", "testing")


@pytest.fixture(scope="session")
def mock_aws_credentials() -> dict[str, str]:
    """Mock AWS credentials for testing."""
    return {
        "AWS_ACCESS_KEY_ID": "test_access_key",
        "AWS_SECRET_ACCESS_KEY": "test_secret_key",
        "AWS_DEFAULT_REGION": "us-east-1",
    }


@pytest.fixture
def mock_boto3_client(monkeypatch: pytest.MonkeyPatch) -> Mock:
    """Mock boto3 client for AWS service tests."""
    try:
        import boto3
    except ImportError:
        pytest.skip("boto3 not installed - skipping boto3 mock fixture")

    mock_client = MagicMock()

    def mock_boto3_client_func(service_name: str, **kwargs: Any) -> Mock:
        return mock_client

    monkeypatch.setattr("boto3.client", mock_boto3_client_func)
    return mock_client


@pytest.fixture
def moto_s3():
    """Moto S3 mock for integration tests."""
    try:
        from moto import mock_s3

        with mock_s3():
            yield
    except ImportError:
        pytest.skip("moto not installed - skipping S3 mock")


@pytest.fixture
def moto_secretsmanager():
    """Moto Secrets Manager mock for integration tests."""
    try:
        from moto import mock_secretsmanager

        with mock_secretsmanager():
            yield
    except ImportError:
        pytest.skip("moto not installed - skipping Secrets Manager mock")


@pytest.fixture
def moto_dynamodb():
    """Moto DynamoDB mock for integration tests."""
    try:
        from moto import mock_dynamodb

        with mock_dynamodb():
            yield
    except ImportError:
        pytest.skip("moto not installed - skipping DynamoDB mock")


@pytest.fixture
def mock_vault_client(monkeypatch: pytest.MonkeyPatch) -> Mock:
    """Mock Vault client for testing."""
    mock_client = MagicMock()
    mock_client.is_authenticated.return_value = True
    mock_client.secrets.kv.v2.read_secret_version.return_value = {
        "data": {"data": {"test_key": "test_value"}}
    }
    mock_client.secrets.kv.v2.list_secrets.return_value = {"data": {"keys": ["secret1", "secret2"]}}

    def mock_hvac_client(*args: Any, **kwargs: Any) -> Mock:
        return mock_client

    monkeypatch.setattr("hvac.Client", mock_hvac_client)
    return mock_client


@pytest.fixture
def sample_dataframe():
    """Sample pandas DataFrame for testing."""
    try:
        import pandas as pd

        return pd.DataFrame(
            {
                "id": [1, 2, 3],
                "name": ["Alice", "Bob", "Charlie"],
                "age": [25, 30, 35],
            }
        )
    except ImportError:
        pytest.skip("pandas not installed")


@pytest.fixture
def sample_dict_data():
    """Sample dictionary data for testing."""
    return {
        "key1": "value1",
        "key2": 123,
        "key3": {"nested": "data"},
        "key4": [1, 2, 3],
    }


@pytest.fixture
def sample_json_string():
    """Sample JSON string for testing."""
    return '{"key1": "value1", "key2": 123}'


@pytest.fixture
def mock_redis():
    """Mock Redis client for testing."""
    mock_client = MagicMock()
    mock_client.get.return_value = None
    mock_client.set.return_value = True
    mock_client.delete.return_value = 1
    mock_client.exists.return_value = False
    return mock_client


@pytest.fixture(autouse=True)
def reset_logging():
    """Reset logging configuration before each test."""
    import logging

    logging.getLogger().handlers = []
    yield
    logging.getLogger().handlers = []


@pytest.fixture
def temp_file(tmp_path):
    """Create a temporary file for testing."""
    test_file = tmp_path / "test_file.txt"
    test_file.write_text("test content")
    return str(test_file)


@pytest.fixture
def temp_dir(tmp_path):
    """Create a temporary directory for testing."""
    return str(tmp_path)
