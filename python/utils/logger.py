"""
Structured logging utilities for _utils package.

Provides consistent, production-ready logging configuration and utilities.
"""

import json
import logging
import sys
from typing import Any, Optional

try:
    import structlog

    HAS_STRUCTLOG = True
except ImportError:
    HAS_STRUCTLOG = False


class StructuredLogger:
    """
    Structured logger wrapper that provides consistent logging across the library.

    Supports both standard logging and structlog for JSON-structured logs.
    """

    def __init__(
        self,
        name: str,
        use_json: bool = False,
        level: int = logging.INFO,
        extra_context: Optional[dict[str, Any]] = None,
    ) -> None:
        """
        Initialize structured logger.

        Args:
            name: Logger name (typically __name__)
            use_json: Whether to use JSON-structured logging
            level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            extra_context: Additional context to include in all log messages
        """
        self.name = name
        self.use_json = use_json and HAS_STRUCTLOG
        self.extra_context = extra_context or {}
        self._logger: Any = None
        self._setup_logger(level)

    def _setup_logger(self, level: int) -> None:
        """Set up the logger with appropriate configuration."""
        if self.use_json and HAS_STRUCTLOG:
            structlog.configure(
                processors=[
                    structlog.contextvars.merge_contextvars,
                    structlog.processors.add_log_level,
                    structlog.processors.TimeStamper(fmt="iso"),
                    structlog.processors.StackInfoRenderer(),
                    structlog.processors.format_exc_info,
                    structlog.processors.JSONRenderer(),
                ],
                wrapper_class=structlog.make_filtering_bound_logger(level),
                context_class=dict,
                logger_factory=structlog.PrintLoggerFactory(),
                cache_logger_on_first_use=True,
            )
            self._logger = structlog.get_logger(self.name)
        else:
            # Standard logging with structured format
            handler = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter(
                fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
            handler.setFormatter(formatter)
            logger = logging.getLogger(self.name)
            logger.setLevel(level)
            logger.addHandler(handler)
            self._logger = logger

    def _merge_context(self, **kwargs: Any) -> dict[str, Any]:
        """Merge extra context with provided kwargs."""
        return {**self.extra_context, **kwargs}

    def debug(self, message: str, **kwargs: Any) -> None:
        """Log debug message."""
        if self.use_json:
            self._logger.debug(message, **self._merge_context(**kwargs))
        else:
            context_str = json.dumps(self._merge_context(**kwargs)) if kwargs else ""
            self._logger.debug(f"{message} {context_str}".strip())

    def info(self, message: str, **kwargs: Any) -> None:
        """Log info message."""
        if self.use_json:
            self._logger.info(message, **self._merge_context(**kwargs))
        else:
            context_str = json.dumps(self._merge_context(**kwargs)) if kwargs else ""
            self._logger.info(f"{message} {context_str}".strip())

    def warning(self, message: str, **kwargs: Any) -> None:
        """Log warning message."""
        if self.use_json:
            self._logger.warning(message, **self._merge_context(**kwargs))
        else:
            context_str = json.dumps(self._merge_context(**kwargs)) if kwargs else ""
            self._logger.warning(f"{message} {context_str}".strip())

    def error(self, message: str, **kwargs: Any) -> None:
        """Log error message."""
        if self.use_json:
            self._logger.error(message, **self._merge_context(**kwargs))
        else:
            context_str = json.dumps(self._merge_context(**kwargs)) if kwargs else ""
            self._logger.error(f"{message} {context_str}".strip())

    def exception(self, message: str, **kwargs: Any) -> None:
        """Log exception with traceback."""
        if self.use_json:
            self._logger.exception(message, exc_info=True, **self._merge_context(**kwargs))
        else:
            context_str = json.dumps(self._merge_context(**kwargs)) if kwargs else ""
            self._logger.exception(f"{message} {context_str}".strip())

    def critical(self, message: str, **kwargs: Any) -> None:
        """Log critical message."""
        if self.use_json:
            self._logger.critical(message, **self._merge_context(**kwargs))
        else:
            context_str = json.dumps(self._merge_context(**kwargs)) if kwargs else ""
            self._logger.critical(f"{message} {context_str}".strip())


def get_logger(
    name: str,
    use_json: bool = False,
    level: Optional[int] = None,
    extra_context: Optional[dict[str, Any]] = None,
) -> StructuredLogger:
    """
    Get a structured logger instance.

    Args:
        name: Logger name (typically __name__)
        use_json: Whether to use JSON-structured logging
        level: Logging level (defaults to INFO)
        extra_context: Additional context to include in all log messages

    Returns:
        StructuredLogger instance
    """
    if level is None:
        level = logging.INFO
    return StructuredLogger(name, use_json=use_json, level=level, extra_context=extra_context)


def configure_logging(
    level: str = "INFO",
    use_json: bool = False,
    format_string: Optional[str] = None,
) -> None:
    """
    Configure root logging for the application.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        use_json: Whether to use JSON-structured logging
        format_string: Custom format string (ignored if use_json=True)
    """
    log_level = getattr(logging, level.upper(), logging.INFO)

    if use_json and HAS_STRUCTLOG:
        structlog.configure(
            processors=[
                structlog.contextvars.merge_contextvars,
                structlog.processors.add_log_level,
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.JSONRenderer(),
            ],
            wrapper_class=structlog.make_filtering_bound_logger(log_level),
            context_class=dict,
            logger_factory=structlog.PrintLoggerFactory(),
            cache_logger_on_first_use=True,
        )
    else:
        format_string = format_string or "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        logging.basicConfig(
            level=log_level,
            format=format_string,
            datefmt="%Y-%m-%d %H:%M:%S",
            stream=sys.stdout,
        )


# CLI functionality
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Logger utility CLI - Test logging configuration")
    parser.add_argument(
        "--level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="Log level",
    )
    parser.add_argument("--json", action="store_true", help="Use JSON logging format")
    parser.add_argument("--message", "-m", default="Test log message", help="Test message to log")

    args = parser.parse_args()

    configure_logging(level=args.level, use_json=args.json)
    logger = get_logger(__name__, use_json=args.json, level=getattr(logging, args.level))

    logger.debug("Debug message")
    logger.info(args.message)
    logger.warning("Warning message")
    logger.error("Error message")
    logger.critical("Critical message")
