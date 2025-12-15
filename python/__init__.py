"""
_utils package - Shared utilities for Django, FastAPI, Alpaca, AWS, data, and ML.
"""

__version__ = "0.1.0"

# Export logger utilities
try:
    from utils.logger import StructuredLogger, configure_logging, get_logger
except ImportError:
    StructuredLogger = None
    configure_logging = None
    get_logger = None

# Export custom exceptions for easy access
from contextlib import suppress

with suppress(ImportError):
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

__all__ = [
    "APIAuthenticationError",
    "APIConnectionError",
    "APIError",
    "APIRateLimitError",
    "APIResponseError",
    "AWSConfigurationError",
    "AWSConnectionError",
    "AWSOperationError",
    "AlpacaAPIError",
    "AlpacaAuthenticationError",
    "AnsibleError",
    "ConfigurationError",
    "CryptographyError",
    "DataFrameError",
    "DataProcessingError",
    "DatabaseConfigurationError",
    "DatabaseConnectionError",
    "DatabaseError",
    "DatabaseQueryError",
    "DecryptionError",
    "EncryptionError",
    "EnvironmentVariableError",
    "FileNotFoundError",
    "FileOperationError",
    "FilePermissionError",
    "SQLGenerationError",
    "TableauAPIError",
    "TableauAuthenticationError",
    "TerraformError",
    "TypeValidationError",
    "UtilsError",
    "ValidationError",
    "VaultError",
    "__version__",
    "configure_logging",
    "get_logger",
]
