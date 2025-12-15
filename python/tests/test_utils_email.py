"""
Tests for email utilities.
"""

from unittest.mock import MagicMock, patch

import pytest
from utils import email


@pytest.mark.unit
class TestEmailUtils:
    """Test email utility functions."""

    def test_email_import(self):
        """Test that email module can be imported."""
        assert email is not None

    @patch("utils.email.secrets_handler")
    def test_send_email_with_secret(self, mock_secrets_handler):
        """Test sending email with Secrets Manager."""
        mock_secrets_handler.get_secret.return_value = {
            "username": "test@example.com",
            "password": "test-pass",
        }

        with patch("smtplib.SMTP") as mock_smtp:
            mock_server = MagicMock()
            mock_smtp.return_value = mock_server

            email.send_email(
                email_body="Test body",
                email_subject="Test Subject",
                to="recipient@example.com",
                email_sender="sender@example.com",
                email_creds_secret_name="email-secret",
            )
            mock_server.sendmail.assert_called_once()

    def test_send_email_missing_sender(self):
        """Test send_email without sender raises error."""
        with pytest.raises(ValueError, match="email_sender parameter is required"):
            email.send_email(
                email_body="Test",
                email_subject="Test",
                to="test@example.com",
            )

    def test_send_email_missing_secret(self):
        """Test send_email without secret name raises error."""
        with pytest.raises(ValueError, match="email_creds_secret_name parameter is required"):
            email.send_email(
                email_body="Test",
                email_subject="Test",
                to="test@example.com",
                email_sender="sender@example.com",
            )
