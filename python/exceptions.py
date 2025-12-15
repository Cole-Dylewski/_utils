"""
Custom exception hierarchy for _utils package.

This module defines a standardized exception hierarchy for consistent
error handling across all _utils modules.
"""


class UtilsError(Exception):
    """Base exception for all _utils package errors."""

    def __init__(self, message: str, *args: object) -> None:
        """Initialize exception with message."""
        self.message = message
        super().__init__(message, *args)


# AWS-related exceptions
class AWSConnectionError(UtilsError):
    """Raised when AWS service connection fails."""


class AWSConfigurationError(UtilsError):
    """Raised when AWS configuration is invalid or missing."""


class AWSOperationError(UtilsError):
    """Raised when an AWS operation fails."""


# Database-related exceptions
class DatabaseError(UtilsError):
    """Base exception for database operations."""


class DatabaseConnectionError(DatabaseError):
    """Raised when database connection fails."""


class DatabaseQueryError(DatabaseError):
    """Raised when a database query fails."""


class DatabaseConfigurationError(DatabaseError):
    """Raised when database configuration is invalid."""


# API-related exceptions
class APIError(UtilsError):
    """Base exception for API operations."""


class APIConnectionError(APIError):
    """Raised when API connection fails."""


class APIResponseError(APIError):
    """Raised when API returns an error response."""


class APIAuthenticationError(APIError):
    """Raised when API authentication fails."""


class APIRateLimitError(APIError):
    """Raised when API rate limit is exceeded."""


# Alpaca-specific exceptions
class AlpacaAPIError(APIError):
    """Raised when Alpaca API operations fail."""


class AlpacaAuthenticationError(AlpacaAPIError, APIAuthenticationError):
    """Raised when Alpaca API authentication fails."""


# Tableau-specific exceptions
class TableauAPIError(APIError):
    """Raised when Tableau API operations fail."""


class TableauAuthenticationError(TableauAPIError, APIAuthenticationError):
    """Raised when Tableau API authentication fails."""


# File and I/O exceptions
class FileOperationError(UtilsError):
    """Raised when file operations fail."""


class FileNotFoundError(FileOperationError):
    """Raised when a required file is not found."""


class FilePermissionError(FileOperationError):
    """Raised when file permission is denied."""


# Configuration exceptions
class ConfigurationError(UtilsError):
    """Raised when configuration is invalid or missing."""


class EnvironmentVariableError(ConfigurationError):
    """Raised when required environment variable is missing."""


# Validation exceptions
class ValidationError(UtilsError):
    """Raised when data validation fails."""


class TypeValidationError(ValidationError):
    """Raised when type validation fails."""


# Cryptography exceptions
class CryptographyError(UtilsError):
    """Raised when cryptography operations fail."""


class EncryptionError(CryptographyError):
    """Raised when encryption fails."""


class DecryptionError(CryptographyError):
    """Raised when decryption fails."""


# Infrastructure exceptions
class TerraformError(UtilsError):
    """Raised when Terraform operations fail."""


class AnsibleError(UtilsError):
    """Raised when Ansible operations fail."""


class VaultError(UtilsError):
    """Raised when Vault operations fail."""


# Data processing exceptions
class DataProcessingError(UtilsError):
    """Raised when data processing operations fail."""


class DataFrameError(DataProcessingError):
    """Raised when DataFrame operations fail."""


class SQLGenerationError(DataProcessingError):
    """Raised when SQL generation fails."""
