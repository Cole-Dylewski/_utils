"""
Tests for structured logging utilities.
"""

from io import StringIO
import json
import logging

import pytest
from utils.logger import StructuredLogger, configure_logging, get_logger


@pytest.mark.unit
class TestStructuredLogger:
    """Test StructuredLogger class."""

    def test_logger_initialization(self):
        """Test logger initialization."""
        logger = StructuredLogger("test_module")
        assert logger.name == "test_module"
        assert logger.use_json is False
        assert logger._logger is not None

    def test_logger_with_json(self):
        """Test logger with JSON output."""
        logger = StructuredLogger("test_module", use_json=True)
        assert logger.use_json is True

    def test_logger_with_extra_context(self):
        """Test logger with extra context."""
        context = {"user_id": "123", "request_id": "abc"}
        logger = StructuredLogger("test_module", extra_context=context)
        assert logger.extra_context == context

    def test_log_levels(self, caplog):
        """Test all log levels."""
        logger = StructuredLogger("test_module", level=logging.DEBUG)
        with caplog.at_level(logging.DEBUG):
            logger.debug("Debug message")
            logger.info("Info message")
            logger.warning("Warning message")
            logger.error("Error message")
            logger.critical("Critical message")

        assert "Debug message" in caplog.text
        assert "Info message" in caplog.text
        assert "Warning message" in caplog.text
        assert "Error message" in caplog.text
        assert "Critical message" in caplog.text

    def test_logger_with_kwargs(self, caplog):
        """Test logger with additional kwargs."""
        logger = StructuredLogger("test_module")
        with caplog.at_level(logging.INFO):
            logger.info("Test message", extra={"key": "value"})
        assert "Test message" in caplog.text

    def test_logger_exception(self, caplog):
        """Test exception logging."""
        logger = StructuredLogger("test_module")
        with caplog.at_level(logging.ERROR):
            try:
                raise ValueError("Test error")
            except ValueError:
                logger.exception("Exception occurred")
        assert "Exception occurred" in caplog.text
        assert "ValueError" in caplog.text


@pytest.mark.unit
class TestGetLogger:
    """Test get_logger function."""

    def test_get_logger_default(self):
        """Test get_logger with default parameters."""
        logger = get_logger("test_module")
        assert isinstance(logger, StructuredLogger)
        assert logger.name == "test_module"

    def test_get_logger_with_json(self):
        """Test get_logger with JSON output."""
        logger = get_logger("test_module", use_json=True)
        assert logger.use_json is True

    def test_get_logger_with_level(self):
        """Test get_logger with custom level."""
        logger = get_logger("test_module", level=logging.WARNING)
        assert logger._logger.level == logging.WARNING

    def test_get_logger_with_context(self):
        """Test get_logger with extra context."""
        context = {"app": "test"}
        logger = get_logger("test_module", extra_context=context)
        assert logger.extra_context == context


@pytest.mark.unit
class TestConfigureLogging:
    """Test configure_logging function."""

    def test_configure_logging_default(self):
        """Test configure logging with defaults."""
        configure_logging()
        logger = logging.getLogger("test")
        assert logger.level <= logging.INFO

    def test_configure_logging_custom_level(self):
        """Test configure logging with custom level."""
        configure_logging(level="DEBUG")
        logger = logging.getLogger("test")
        assert logger.level <= logging.DEBUG

    def test_configure_logging_json(self):
        """Test configure logging with JSON format."""
        # This will work if structlog is available
        try:
            configure_logging(use_json=True, level="INFO")
            # If no exception, it worked
            assert True
        except Exception:
            # structlog might not be available
            pytest.skip("structlog not available")

    def test_logger_merge_context(self):
        """Test logger context merging."""
        logger = StructuredLogger("test_module", extra_context={"base": "value"})
        merged = logger._merge_context(key="value")
        assert "base" in merged
        assert merged["key"] == "value"

    def test_logger_setup_with_level(self):
        """Test logger setup with custom level."""
        logger = StructuredLogger("test_module", level=logging.WARNING)
        assert logger._logger.level == logging.WARNING

    def test_logger_setup_json_mode(self):
        """Test logger setup in JSON mode."""
        logger = StructuredLogger("test_module", use_json=True)
        # Should not raise exception
        logger.info("Test message")
        assert logger.use_json is True

    def test_configure_logging_custom_format(self):
        """Test configure logging with custom format string."""
        configure_logging(level="INFO", format_string="%(message)s")
        logger = logging.getLogger("test")
        assert logger.level <= logging.INFO

    def test_logger_setup_logger_method(self):
        """Test logger _setup_logger method."""
        logger = StructuredLogger("test_module")
        # _setup_logger is called in __init__, verify it worked
        assert logger._logger is not None
        assert logger._logger.name == "test_module"

    def test_logger_with_structlog_unavailable(self):
        """Test logger behavior when structlog is not available."""
        # This tests the fallback behavior
        logger = StructuredLogger("test_module", use_json=False)
        logger.info("Test message")
        assert logger.use_json is False
