"""
Tests for AWS Transfer Family utilities.
"""

from unittest.mock import MagicMock, patch

from aws.transfer_family import TransferFamilyHandler
import pytest


@pytest.mark.aws
@pytest.mark.unit
class TestTransferFamilyHandler:
    """Test TransferFamilyHandler class."""

    @patch("aws.transfer_family.boto3_session.Session")
    def test_transfer_family_handler_initialization(self, mock_session):
        """Test TransferFamilyHandler initialization."""
        mock_session_instance = MagicMock()
        mock_session.return_value = mock_session_instance
        mock_session_instance.client.return_value = MagicMock()

        handler = TransferFamilyHandler(
            server_id="test-server",
            region_name="us-east-1",
        )
        assert handler.session is not None
        assert handler.transfer_client is not None
        assert handler.server_id == "test-server"

    @patch("aws.transfer_family.boto3_session.Session")
    def test_transfer_family_handler_with_session(self, mock_session):
        """Test TransferFamilyHandler with provided session."""
        mock_session_obj = MagicMock()
        mock_session_obj.client.return_value = MagicMock()

        handler = TransferFamilyHandler(
            server_id="test-server",
            session=mock_session_obj,
        )
        assert handler.session == mock_session_obj
