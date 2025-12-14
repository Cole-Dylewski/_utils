"""
Pytest configuration and shared fixtures.
"""

from typing import Any
from unittest.mock import MagicMock, Mock

import pytest


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


@pytest.fixture(autouse=True)
def reset_logging():
    """Reset logging configuration before each test."""
    import logging

    logging.getLogger().handlers = []
    yield
    logging.getLogger().handlers = []
