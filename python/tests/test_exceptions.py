"""
Tests for custom exception hierarchy.
"""

from exceptions import (
    AlpacaAPIError,
    AlpacaAuthenticationError,
    AnsibleError,
    APIAuthenticationError,
    APIConnectionError,
    APIError,
    APIRateLimitError,
    APIResponseError,
    AWSConfigurationError,
    AWSConnectionError,
    AWSOperationError,
    ConfigurationError,
    CryptographyError,
    DatabaseConfigurationError,
    DatabaseConnectionError,
    DatabaseError,
    DatabaseQueryError,
    DataFrameError,
    DataProcessingError,
    DecryptionError,
    EncryptionError,
    EnvironmentVariableError,
    FileNotFoundError,
    FileOperationError,
    FilePermissionError,
    SQLGenerationError,
    TableauAPIError,
    TableauAuthenticationError,
    TerraformError,
    TypeValidationError,
    UtilsError,
    ValidationError,
    VaultError,
)
import pytest


@pytest.mark.unit
class TestExceptionHierarchy:
    """Test exception hierarchy and inheritance."""

    def test_base_exception(self):
        """Test base UtilsError exception."""
        error = UtilsError("Test error")
        assert str(error) == "Test error"
        assert isinstance(error, Exception)
        assert isinstance(error, UtilsError)

    def test_aws_exceptions(self):
        """Test AWS-related exceptions."""
        conn_error = AWSConnectionError("Connection failed")
        assert isinstance(conn_error, UtilsError)
        assert isinstance(conn_error, AWSConnectionError)

        config_error = AWSConfigurationError("Invalid config")
        assert isinstance(config_error, UtilsError)
        assert isinstance(config_error, AWSConfigurationError)

        op_error = AWSOperationError("Operation failed")
        assert isinstance(op_error, UtilsError)
        assert isinstance(op_error, AWSOperationError)

    def test_database_exceptions(self):
        """Test database-related exceptions."""
        db_error = DatabaseError("Database error")
        assert isinstance(db_error, UtilsError)
        assert isinstance(db_error, DatabaseError)

        conn_error = DatabaseConnectionError("Connection failed")
        assert isinstance(conn_error, DatabaseError)
        assert isinstance(conn_error, UtilsError)

        query_error = DatabaseQueryError("Query failed")
        assert isinstance(query_error, DatabaseError)
        assert isinstance(query_error, UtilsError)

    def test_api_exceptions(self):
        """Test API-related exceptions."""
        api_error = APIError("API error")
        assert isinstance(api_error, UtilsError)
        assert isinstance(api_error, APIError)

        conn_error = APIConnectionError("Connection failed")
        assert isinstance(conn_error, APIError)
        assert isinstance(conn_error, UtilsError)

        auth_error = APIAuthenticationError("Auth failed")
        assert isinstance(auth_error, APIError)
        assert isinstance(auth_error, UtilsError)

        rate_error = APIRateLimitError("Rate limit exceeded")
        assert isinstance(rate_error, APIError)
        assert isinstance(rate_error, UtilsError)

    def test_alpaca_exceptions(self):
        """Test Alpaca-specific exceptions."""
        alpaca_error = AlpacaAPIError("Alpaca error")
        assert isinstance(alpaca_error, APIError)
        assert isinstance(alpaca_error, UtilsError)

        auth_error = AlpacaAuthenticationError("Auth failed")
        assert isinstance(auth_error, AlpacaAPIError)
        assert isinstance(auth_error, APIAuthenticationError)
        assert isinstance(auth_error, UtilsError)

    def test_file_exceptions(self):
        """Test file-related exceptions."""
        file_error = FileOperationError("File operation failed")
        assert isinstance(file_error, UtilsError)
        assert isinstance(file_error, FileOperationError)

        not_found = FileNotFoundError("File not found")
        assert isinstance(not_found, FileOperationError)
        assert isinstance(not_found, UtilsError)

        perm_error = FilePermissionError("Permission denied")
        assert isinstance(perm_error, FileOperationError)
        assert isinstance(perm_error, UtilsError)

    def test_validation_exceptions(self):
        """Test validation exceptions."""
        val_error = ValidationError("Validation failed")
        assert isinstance(val_error, UtilsError)
        assert isinstance(val_error, ValidationError)

        type_error = TypeValidationError("Type validation failed")
        assert isinstance(type_error, ValidationError)
        assert isinstance(type_error, UtilsError)

    def test_cryptography_exceptions(self):
        """Test cryptography exceptions."""
        crypto_error = CryptographyError("Crypto error")
        assert isinstance(crypto_error, UtilsError)
        assert isinstance(crypto_error, CryptographyError)

        enc_error = EncryptionError("Encryption failed")
        assert isinstance(enc_error, CryptographyError)
        assert isinstance(enc_error, UtilsError)

        dec_error = DecryptionError("Decryption failed")
        assert isinstance(dec_error, CryptographyError)
        assert isinstance(dec_error, UtilsError)

    def test_exception_message_preservation(self):
        """Test that exception messages are preserved."""
        message = "Custom error message"
        error = UtilsError(message)
        assert error.message == message
        assert str(error) == message

    def test_exception_chaining(self):
        """Test exception chaining."""
        with pytest.raises(DatabaseConnectionError) as exc_info:
            raise DatabaseConnectionError("Connection failed")
        assert isinstance(exc_info.value, DatabaseError)
        assert isinstance(exc_info.value, UtilsError)
        assert str(exc_info.value) == "Connection failed"
