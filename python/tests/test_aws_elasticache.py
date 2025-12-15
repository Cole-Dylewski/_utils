"""
Tests for AWS ElastiCache utilities.
"""

from unittest.mock import MagicMock, patch

from aws.elasticache import ElastiCacheHandler
import pytest


@pytest.mark.aws
@pytest.mark.unit
class TestElastiCacheHandler:
    """Test ElastiCacheHandler class."""

    @patch("aws.elasticache.boto3_session.Session")
    def test_elasticache_handler_initialization(self, mock_session):
        """Test ElastiCacheHandler initialization."""
        mock_session_instance = MagicMock()
        mock_session.return_value = mock_session_instance
        mock_session_instance.client.return_value = MagicMock()

        handler = ElastiCacheHandler()
        assert handler.session is not None
        assert handler.elasticache_client is not None

    @patch("aws.elasticache.boto3_session.Session")
    def test_elasticache_handler_with_session(self, mock_session):
        """Test ElastiCacheHandler with provided session."""
        mock_session_obj = MagicMock()
        mock_session_obj.client.return_value = MagicMock()

        handler = ElastiCacheHandler(session=mock_session_obj)
        assert handler.session == mock_session_obj

    @patch("aws.elasticache.boto3_session.Session")
    def test_generate_redis_auth_token(self, mock_session):
        """Test generating Redis auth token."""
        mock_session_instance = MagicMock()
        mock_session_instance.client.return_value = MagicMock()
        mock_session.return_value = mock_session_instance

        handler = ElastiCacheHandler(session=mock_session_instance)
        token = handler.generate_redis_auth_token(length=32)
        assert isinstance(token, str)
        assert len(token) == 32

    @patch("aws.elasticache.boto3_session.Session")
    def test_generate_redis_auth_token_invalid_length(self, mock_session):
        """Test generating Redis auth token with invalid length raises error."""
        mock_session_instance = MagicMock()
        mock_session_instance.client.return_value = MagicMock()
        mock_session.return_value = mock_session_instance

        handler = ElastiCacheHandler(session=mock_session_instance)
        with pytest.raises(ValueError, match="Token length must be between"):
            handler.generate_redis_auth_token(length=10)
