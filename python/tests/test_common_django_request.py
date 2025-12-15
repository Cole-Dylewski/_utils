"""
Tests for Django request utilities.
"""

from unittest.mock import MagicMock

from common import django_request
import pytest


@pytest.mark.unit
class TestDjangoRequestUtils:
    """Test Django request utility functions."""

    def test_request_to_dict(self):
        """Test converting Django request to dictionary."""
        mock_request = MagicMock()
        mock_request.__dict__ = {
            "method": "GET",
            "path": "/test",
            "user": "testuser",
        }

        result = django_request.request_to_dict(mock_request)
        assert isinstance(result, dict)
        assert "method" in result
        assert result["method"] == "GET"
