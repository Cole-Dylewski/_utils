"""
Tests for log_print utilities.
"""

from io import StringIO
from unittest.mock import patch

import pytest
from utils import log_print


@pytest.mark.unit
class TestLogPrintUtils:
    """Test log_print utility functions."""

    @patch("sys.stdout", new_callable=StringIO)
    def test_color_print_basic(self, mock_stdout):
        """Test basic color printing."""
        styles = [{"string": "Hello", "text": "red"}]
        log_print.color_print(styles)
        output = mock_stdout.getvalue()
        assert "Hello" in output

    @patch("sys.stdout", new_callable=StringIO)
    def test_color_print_multiple_styles(self, mock_stdout):
        """Test color printing with multiple styles."""
        styles = [
            {"string": "Red", "text": "red"},
            {"string": "Green", "text": "green"},
            {"string": "Blue", "text": "blue"},
        ]
        log_print.color_print(styles)
        output = mock_stdout.getvalue()
        assert "Red" in output
        assert "Green" in output
        assert "Blue" in output

    @patch("sys.stdout", new_callable=StringIO)
    def test_color_print_with_background(self, mock_stdout):
        """Test color printing with background color."""
        styles = [{"string": "Test", "text": "white", "background": "blue"}]
        log_print.color_print(styles)
        output = mock_stdout.getvalue()
        assert "Test" in output

    @patch("sys.stdout", new_callable=StringIO)
    def test_color_print_no_reset(self, mock_stdout):
        """Test color printing without reset."""
        styles = [{"string": "Test", "text": "red", "reset": False}]
        log_print.color_print(styles)
        output = mock_stdout.getvalue()
        assert "Test" in output

    @patch("sys.stdout", new_callable=StringIO)
    def test_color_print_invalid_color(self, mock_stdout):
        """Test color printing with invalid color (should handle gracefully)."""
        styles = [{"string": "Test", "text": "invalid_color"}]
        log_print.color_print(styles)
        output = mock_stdout.getvalue()
        assert "Test" in output
