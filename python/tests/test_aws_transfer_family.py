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

    @patch("aws.boto3_session.Session")
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

    @patch("aws.boto3_session.Session")
    def test_transfer_family_handler_with_session(self, mock_session):
        """Test TransferFamilyHandler with provided session."""
        mock_session_obj = MagicMock()
        mock_session_obj.client.return_value = MagicMock()

        handler = TransferFamilyHandler(session=mock_session_obj)
        assert handler.session == mock_session_obj

    @patch("aws.boto3_session.Session")
    def test_create_server(self, mock_session):
        """Test creating Transfer Family server."""
        mock_session_instance = MagicMock()
        mock_transfer_client = MagicMock()
        mock_transfer_client.create_server.return_value = {"ServerId": "test-server-id"}
        mock_session_instance.client.return_value = mock_transfer_client
        mock_session.return_value = mock_session_instance

        handler = TransferFamilyHandler(session=mock_session_instance)
        response = handler.create_server()
        assert response is not None
        assert "ServerId" in response
        mock_transfer_client.create_server.assert_called_once()

    @patch("aws.boto3_session.Session")
    def test_list_servers(self, mock_session):
        """Test listing Transfer Family servers."""
        mock_session_instance = MagicMock()
        mock_transfer_client = MagicMock()
        mock_transfer_client.list_servers.return_value = {
            "Servers": [{"ServerId": "test-server-id"}]
        }
        mock_session_instance.client.return_value = mock_transfer_client
        mock_session.return_value = mock_session_instance

        handler = TransferFamilyHandler(session=mock_session_instance)
        servers = handler.list_servers()
        assert isinstance(servers, list)
        mock_transfer_client.list_servers.assert_called_once()


@pytest.mark.aws
@pytest.mark.unit
class TestTransferServerException:
    """Test TransferServerException."""

    def test_exception_creation(self):
        """Test exception creation."""
        from aws.transfer_family import TransferServerException

        exc = TransferServerException("test-server-id")
        assert exc.server_id == "test-server-id"
        assert "test-server-id" in str(exc)
