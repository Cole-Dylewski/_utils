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
