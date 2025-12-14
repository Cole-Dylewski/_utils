"""
Credential Generator

Generates secure random credentials for application deployment.
"""

import logging
import secrets
import string
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class CredentialGenerator:
    """Generates secure random credentials."""

    @staticmethod
    def generate_password(
        length: int = 32,
        include_uppercase: bool = True,
        include_lowercase: bool = True,
        include_digits: bool = True,
        include_special: bool = True,
        exclude_chars: str = "",
    ) -> str:
        """
        Generate a secure random password.

        :param length: Password length (default: 32)
        :param include_uppercase: Include uppercase letters
        :param include_lowercase: Include lowercase letters
        :param include_digits: Include digits
        :param include_special: Include special characters
        :param exclude_chars: Characters to exclude from password
        :return: Generated password

        Example:
            >>> password = CredentialGenerator.generate_password(length=24)
            >>> len(password)
            24
        """
        if length < 8:
            raise ValueError("Password length must be at least 8 characters")

        charset = ""

        if include_uppercase:
            charset += string.ascii_uppercase
        if include_lowercase:
            charset += string.ascii_lowercase
        if include_digits:
            charset += string.digits
        if include_special:
            charset += "!@#$%^&*()_+-=[]{}|;:,.<>?"

        if not charset:
            raise ValueError("At least one character set must be enabled")

        for char in exclude_chars:
            charset = charset.replace(char, "")

        if not charset:
            raise ValueError("No valid characters available after exclusions")

        password = "".join(secrets.choice(charset) for _ in range(length))

        logger.debug(f"Generated password of length {length}")
        return password

    @staticmethod
    def generate_api_key(length: int = 64) -> str:
        """
        Generate a secure random API key.

        :param length: Key length (default: 64)
        :return: Generated API key

        Example:
            >>> key = CredentialGenerator.generate_api_key(length=32)
            >>> len(key)
            32
        """
        charset = string.ascii_letters + string.digits
        key = "".join(secrets.choice(charset) for _ in range(length))
        logger.debug(f"Generated API key of length {length}")
        return key

    @staticmethod
    def generate_secret_token(length: int = 32) -> str:
        """
        Generate a secure random secret token.

        :param length: Token length (default: 32)
        :return: Generated secret token

        Example:
            >>> token = CredentialGenerator.generate_secret_token(length=24)
            >>> len(token)
            24
        """
        token = secrets.token_urlsafe(length)
        logger.debug(f"Generated secret token of length {length}")
        return token

    @staticmethod
    def generate_jwt_secret(length: int = 64) -> str:
        """
        Generate a JWT secret key.

        :param length: Secret length (default: 64)
        :return: Generated JWT secret

        Example:
            >>> secret = CredentialGenerator.generate_jwt_secret()
            >>> len(secret) >= 32
            True
        """
        secret = secrets.token_urlsafe(length)
        logger.debug(f"Generated JWT secret of length {length}")
        return secret

    @staticmethod
    def generate_encryption_key(length: int = 32) -> str:
        """
        Generate an encryption key (hex format).

        :param length: Key length in bytes (default: 32 for 256-bit)
        :return: Generated encryption key in hex format

        Example:
            >>> key = CredentialGenerator.generate_encryption_key()
            >>> len(key)
            64
        """
        key_bytes = secrets.token_bytes(length)
        key_hex = key_bytes.hex()
        logger.debug(f"Generated encryption key of {length} bytes ({len(key_hex)} hex chars)")
        return key_hex

    @staticmethod
    def generate_database_credentials(
        password_length: int = 32,
        username: Optional[str] = None,
    ) -> Dict[str, str]:
        """
        Generate database credentials.

        :param password_length: Password length (default: 32)
        :param username: Database username (default: auto-generated)
        :return: Dictionary with 'username' and 'password' keys

        Example:
            >>> creds = CredentialGenerator.generate_database_credentials()
            >>> 'username' in creds
            True
            >>> 'password' in creds
            True
        """
        if username is None:
            username = f"db_user_{secrets.token_hex(8)}"

        password = CredentialGenerator.generate_password(
            length=password_length,
            include_special=False,
            exclude_chars="\"'\\",
        )

        return {
            "username": username,
            "password": password,
        }

    @staticmethod
    def generate_all_credentials(
        database_password_length: int = 32,
        api_key_length: int = 64,
        jwt_secret_length: int = 64,
        encryption_key_bytes: int = 32,
    ) -> Dict[str, str]:
        """
        Generate all common application credentials.

        :param database_password_length: Database password length
        :param api_key_length: API key length
        :param jwt_secret_length: JWT secret length
        :param encryption_key_bytes: Encryption key size in bytes
        :return: Dictionary of generated credentials

        Example:
            >>> creds = CredentialGenerator.generate_all_credentials()
            >>> 'database_password' in creds
            True
            >>> 'jwt_secret' in creds
            True
        """
        credentials = {
            "database_password": CredentialGenerator.generate_password(
                length=database_password_length,
                include_special=False,
                exclude_chars="\"'\\",
            ),
            "jwt_secret": CredentialGenerator.generate_jwt_secret(
                length=jwt_secret_length
            ),
            "encryption_key": CredentialGenerator.generate_encryption_key(
                length=encryption_key_bytes
            ),
            "api_key": CredentialGenerator.generate_api_key(length=api_key_length),
        }

        logger.info(f"Generated {len(credentials)} credentials")
        return credentials

