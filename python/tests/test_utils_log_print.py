"""
Tests for log_print utilities.
"""

from unittest.mock import patch

import pytest
from utils import log_print


@pytest.mark.unit
class TestLogPrintUtils:
    """Test log_print utility functions."""

    @patch("builtins.print")
    def test_color_print_basic(self, mock_print):
        """Test basic color printing."""
        styles = [{"string": "Hello", "text": "red"}]
        log_print.color_print(styles)
        mock_print.assert_called_once()
        # Check that the printed content contains the string
        call_args = str(mock_print.call_args)
        assert "Hello" in call_args or "\033[31m" in call_args  # red ANSI code

    @patch("builtins.print")
    def test_color_print_multiple_styles(self, mock_print):
        """Test color printing with multiple styles."""
        styles = [
            {"string": "Red", "text": "red"},
            {"string": "Green", "text": "green"},
            {"string": "Blue", "text": "blue"},
        ]
        log_print.color_print(styles)
        mock_print.assert_called_once()
        call_args = str(mock_print.call_args)
        assert "Red" in call_args
        assert "Green" in call_args
        assert "Blue" in call_args

    @patch("builtins.print")
    def test_color_print_with_background(self, mock_print):
        """Test color printing with background color."""
        styles = [{"string": "Test", "text": "white", "background": "blue"}]
        log_print.color_print(styles)
        mock_print.assert_called_once()
        call_args = str(mock_print.call_args)
        assert "Test" in call_args

    @patch("builtins.print")
    def test_color_print_no_reset(self, mock_print):
        """Test color printing without reset."""
        styles = [{"string": "Test", "text": "red", "reset": False}]
        log_print.color_print(styles)
        mock_print.assert_called_once()
        call_args = str(mock_print.call_args)
        assert "Test" in call_args

    @patch("builtins.print")
    def test_color_print_invalid_color(self, mock_print):
        """Test color printing with invalid color (should handle gracefully)."""
        styles = [{"string": "Test", "text": "invalid_color"}]
        log_print.color_print(styles)
        mock_print.assert_called_once()
        call_args = str(mock_print.call_args)
        assert "Test" in call_args
