"""
Tests for Teams notification utilities.
"""

from unittest.mock import MagicMock, patch

import pytest
from utils import teams


@pytest.mark.unit
class TestTeamsUtils:
    """Test Teams utility functions."""

    @patch("utils.teams.secrets_handler.get_secret")
    @patch("utils.teams.sql.run_sql")
    @patch("requests.post")
    def test_send_teams_notification_basic(self, mock_post, mock_sql, mock_secret):
        """Test sending Teams notification without users."""
        mock_secret.return_value = {"channel1": "https://webhook.url"}
        mock_post.return_value = MagicMock(status_code=200)

        teams.send_teams_notification(
            channel="channel1",
            premsg="Test message",
            postmsg="Additional info",
            webhook_secret_name="teams-secret",
        )
        mock_secret.assert_called_once()
        mock_post.assert_called_once()

    @patch("utils.teams.secrets_handler.get_secret")
    @patch("utils.teams.sql.run_sql")
    @patch("requests.post")
    def test_send_teams_notification_with_users(self, mock_post, mock_sql, mock_secret):
        """Test sending Teams notification with user mentions."""
        import pandas as pd

        mock_secret.return_value = {"channel1": "https://webhook.url"}
        mock_sql.return_value = pd.DataFrame(
            {
                "email": ["user@example.com"],
                "first_name": ["John"],
                "last_name": ["Doe"],
            }
        )
        mock_post.return_value = MagicMock(status_code=200)

        teams.send_teams_notification(
            channel="channel1",
            users=["user@example.com"],
            premsg="Test message",
            webhook_secret_name="teams-secret",
            directory_schema="schema.directory_table",
        )
        mock_sql.assert_called_once()
        mock_post.assert_called_once()

    def test_send_teams_notification_missing_webhook(self):
        """Test sending Teams notification without webhook raises error."""
        with pytest.raises(ValueError, match="webhook_secret_name parameter is required"):
            teams.send_teams_notification(
                channel="channel1",
                premsg="Test",
            )

    @patch("utils.teams.secrets_handler.get_secret")
    def test_send_teams_notification_missing_directory_schema(self, mock_secret):
        """Test sending Teams notification with users but no directory schema raises error."""
        mock_secret.return_value = {"channel1": "https://webhook.url"}
        with pytest.raises(ValueError, match="directory_schema parameter is required"):
            teams.send_teams_notification(
                channel="channel1",
                users=["user@example.com"],
                premsg="Test",
                webhook_secret_name="secret",
            )
