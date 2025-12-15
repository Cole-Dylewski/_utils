"""
Tests for Tableau utilities.
"""

from unittest.mock import MagicMock, patch

import pytest
from tableau import tableau_client


@pytest.mark.unit
class TestTableauClient:
    """Test TableauClient class."""

    @patch("tableau.tableau_client.TableauAuth")
    @patch("tableau.tableau_client.Server")
    def test_tableau_client_initialization(self, mock_server, mock_auth):
        """Test TableauClient initialization."""
        mock_auth_instance = MagicMock()
        mock_auth.return_value = mock_auth_instance
        mock_server_instance = MagicMock()
        mock_server.return_value = mock_server_instance

        client = tableau_client.tableau_client(
            username="test",
            password="test",
            server_url="https://tableau.example.com",
        )
        assert client is not None

    @patch("tableau.tableau_client.TableauAuth")
    @patch("tableau.tableau_client.Server")
    def test_tableau_client_login(self, mock_server, mock_auth):
        """Test Tableau client login."""
        mock_auth_instance = MagicMock()
        mock_auth.return_value = mock_auth_instance
        mock_server_instance = MagicMock()
        mock_server_instance.auth.sign_in.return_value = None
        mock_server.return_value = mock_server_instance

        client = tableau_client.tableau_client(
            username="test",
            password="test",
            server_url="https://tableau.example.com",
        )
        with client:
            client.login()
            mock_server_instance.auth.sign_in.assert_called_once()
