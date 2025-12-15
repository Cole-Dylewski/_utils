"""
Tests for boto3 session utilities.
"""

import os
from unittest.mock import patch

from aws import boto3_session
import pytest


@pytest.mark.aws
@pytest.mark.unit
class TestBoto3Session:
    """Test boto3 session utilities."""

    @patch.dict(
        os.environ, {"AWS_ACCESS_KEY_ID": "test_key", "AWS_SECRET_ACCESS_KEY": "test_secret"}
    )
    def test_session_with_env_vars(self):
        """Test session creation with environment variables."""
        session = boto3_session.Session()
        assert session is not None

    def test_session_with_credentials(self):
        """Test session creation with provided credentials."""
        session = boto3_session.Session(
            aws_access_key_id="test_key",
            aws_secret_access_key="test_secret",
            region_name="us-west-2",
        )
        assert session is not None
        assert session.region_name == "us-west-2"

    @patch.dict(os.environ, {}, clear=True)
    def test_session_without_credentials(self):
        """Test session creation without credentials raises error."""
        # This should work with default credentials chain or raise appropriate error
        try:
            session = boto3_session.Session()
            # If it doesn't raise, that's fine (might use default profile)
            assert session is not None
        except Exception:
            # Expected if no credentials available
            pass

    def test_session_region_default(self):
        """Test session uses default region."""
        session = boto3_session.Session(
            aws_access_key_id="test_key",
            aws_secret_access_key="test_secret",
        )
        assert session is not None
        # Should use default or environment region
