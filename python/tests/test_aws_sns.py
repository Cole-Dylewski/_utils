"""
Tests for AWS SNS utilities.
"""

from unittest.mock import MagicMock, patch

from aws.sns import SNSHandler
import pytest


@pytest.mark.aws
@pytest.mark.unit
class TestSNSHandler:
    """Test SNSHandler class."""

    @patch("aws.sns.boto3_session.Session")
    def test_sns_handler_initialization(self, mock_session):
        """Test SNSHandler initialization."""
        mock_session_instance = MagicMock()
        mock_session.return_value = mock_session_instance
        mock_session_instance.client.return_value = MagicMock()

        handler = SNSHandler()
        assert handler.session is not None
        assert handler.sns_client is not None

    @patch("aws.sns.boto3_session.Session")
    def test_sns_handler_with_session(self, mock_session):
        """Test SNSHandler with provided session."""
        mock_session_obj = MagicMock()
        mock_session_obj.client.return_value = MagicMock()

        handler = SNSHandler(session=mock_session_obj)
        assert handler.session == mock_session_obj

    @patch("aws.sns.boto3_session.Session")
    def test_publish_message(self, mock_session):
        """Test publishing SNS message."""
        mock_session_instance = MagicMock()
        mock_sns_client = MagicMock()
        mock_sns_client.publish.return_value = {"MessageId": "test-message-id"}
        mock_session_instance.client.return_value = mock_sns_client
        mock_session.return_value = mock_session_instance

        handler = SNSHandler(session=mock_session_instance)
        response = handler.publish_message(
            topic_arn="arn:aws:sns:us-east-1:123:test-topic",
            message="Test message",
        )
        assert response is not None
        assert "MessageId" in response
        mock_sns_client.publish.assert_called_once()
