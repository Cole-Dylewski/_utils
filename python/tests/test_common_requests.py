"""
Tests for common requests utilities.
"""

from unittest.mock import MagicMock, patch

from common import requests
import pytest


@pytest.mark.unit
class TestCommonRequestsUtils:
    """Test common requests utility functions."""

    @patch("common.requests.requests.get")
    def test_internet_test_success(self, mock_get):
        """Test internet connection test with success."""
        mock_response = MagicMock()
        mock_get.return_value = mock_response

        result = requests.internet_test()
        assert result is True
        mock_get.assert_called_once()

    @patch("common.requests.requests.get")
    def test_internet_test_failure(self, mock_get):
        """Test internet connection test with failure."""
        import requests as requests_lib

        mock_get.side_effect = requests_lib.ConnectionError("No connection")

        result = requests.internet_test()
        assert result is False

    @patch("common.requests.requests.get")
    def test_fastapi_success(self, mock_get):
        """Test FastAPI connection test with success."""
        mock_response = MagicMock()
        mock_response.text = "OK"
        mock_get.return_value = mock_response

        result = requests.fastAPI()
        assert result is True
        mock_get.assert_called_once()

    @patch("common.requests.requests.get")
    def test_fastapi_failure(self, mock_get):
        """Test FastAPI connection test with failure."""
        import requests as requests_lib

        mock_get.side_effect = requests_lib.ConnectionError("No connection")

        result = requests.fastAPI()
        assert result is False
