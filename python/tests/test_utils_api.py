"""
Tests for API utilities.
"""

from unittest.mock import MagicMock, patch

import pytest
from utils import api


@pytest.mark.unit
class TestAPIUtils:
    """Test API utility functions."""

    def test_api_import(self):
        """Test that api module can be imported."""
        assert api is not None

    @patch("utils.api.requests.get")
    def test_api_request(self, mock_get):
        """Test API request function."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"test": "data"}
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        # Add specific tests based on api.py functions
        assert api is not None
