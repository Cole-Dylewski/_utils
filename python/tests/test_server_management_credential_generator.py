"""
Tests for credential generator utilities.
"""

import pytest
from server_management.credential_generator import CredentialGenerator


@pytest.mark.unit
class TestCredentialGenerator:
    """Test CredentialGenerator class."""

    def test_generate_password_default(self):
        """Test generating password with default settings."""
        password = CredentialGenerator.generate_password()
        assert isinstance(password, str)
        assert len(password) == 32

    def test_generate_password_custom_length(self):
        """Test generating password with custom length."""
        password = CredentialGenerator.generate_password(length=16)
        assert len(password) == 16

    def test_generate_password_minimum_length(self):
        """Test generating password with minimum length."""
        password = CredentialGenerator.generate_password(length=8)
        assert len(password) == 8

    def test_generate_password_invalid_length(self):
        """Test generating password with invalid length raises error."""
        with pytest.raises(ValueError, match="Password length must be at least 8"):
            CredentialGenerator.generate_password(length=5)

    def test_generate_password_uppercase_only(self):
        """Test generating password with uppercase only."""
        password = CredentialGenerator.generate_password(
            length=10,
            include_uppercase=True,
            include_lowercase=False,
            include_digits=False,
            include_special=False,
        )
        assert password.isupper()
        assert len(password) == 10

    def test_generate_password_lowercase_only(self):
        """Test generating password with lowercase only."""
        password = CredentialGenerator.generate_password(
            length=10,
            include_uppercase=False,
            include_lowercase=True,
            include_digits=False,
            include_special=False,
        )
        assert password.islower()
        assert len(password) == 10

    def test_generate_password_digits_only(self):
        """Test generating password with digits only."""
        password = CredentialGenerator.generate_password(
            length=10,
            include_uppercase=False,
            include_lowercase=False,
            include_digits=True,
            include_special=False,
        )
        assert password.isdigit()
        assert len(password) == 10

    def test_generate_password_exclude_chars(self):
        """Test generating password with excluded characters."""
        password = CredentialGenerator.generate_password(length=20, exclude_chars="aA1")
        assert "a" not in password
        assert "A" not in password
        assert "1" not in password
