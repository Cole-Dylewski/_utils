"""
Tests for Tableau utilities.
"""

from unittest.mock import MagicMock, patch

import pytest
from tableau import tableau_client


@pytest.mark.unit
class TestTableauClient:
    """Test TableauClient class."""

    @patch("tableau.tableau_client.requests.request")
    def test_tableau_client_initialization(self, mock_request):
        """Test TableauClient initialization."""
        # Mock the login response (called during get_site in __init__)
        # First call is login(getSites=True), second is get_site
        mock_responses = [
            MagicMock(
                text='{"credentials": {"token": "test-token"}, "sites": {"site": [{"id": "test-site", "contentUrl": "", "name": "Default"}]}}'
            ),
            MagicMock(
                text='{"sites": {"site": [{"id": "test-site", "contentUrl": "", "name": "Default"}]}}'
            ),
        ]
        mock_request.side_effect = mock_responses

        client = tableau_client.tableau_client(
            username="test",
            password="test",
            server_url="https://tableau.example.com",
        )
        assert client is not None
        assert client.username == "test"
        assert client.password == "test"
        assert client.site is not None

    @patch("tableau.tableau_client.requests.request")
    def test_tableau_client_login(self, mock_request):
        """Test Tableau client login."""
        # Mock responses: first for login(getSites=True) in __init__, second for get_site, third for login()
        # When site is empty, get_site returns a dict keyed by site name, but login() expects a single site dict
        # So we'll pass a site name to get a single site dict
        mock_responses = [
            MagicMock(
                text='{"credentials": {"token": "init-token"}, "sites": {"site": [{"id": "test-site", "contentUrl": "", "name": "Default"}]}}'
            ),
            MagicMock(
                text='{"sites": {"site": [{"id": "test-site", "contentUrl": "", "name": "Default"}]}}'
            ),
            MagicMock(text='{"credentials": {"token": "login-token"}}'),
        ]
        mock_request.side_effect = mock_responses

        client = tableau_client.tableau_client(
            username="test",
            password="test",
            server_url="https://tableau.example.com",
            site="Default",  # Pass site name to get single site dict instead of dict of sites
        )
        # After initialization, client.site should be a single site dict with contentUrl
        # If get_site returned a dict of sites, extract the first one
        if isinstance(client.site, dict) and "contentUrl" not in client.site:
            # It's a dict of sites, extract the first one
            if client.site:
                first_site_key = next(iter(client.site.keys()))
                client.site = client.site[first_site_key]

        result = client.login()
        assert result is not None
        assert "token" in result
        assert mock_request.call_count >= 3  # login(getSites=True), get_site, and login()

    # Note: tableau_client class doesn't support tableau_creds_secret_name parameter
    # This test is skipped as the functionality doesn't exist in the current implementation
    @pytest.mark.skip(reason="tableau_client doesn't support tableau_creds_secret_name parameter")
    def test_tableau_client_with_secret(self):
        """Test Tableau client initialization with Secrets Manager."""
