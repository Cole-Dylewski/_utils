"""
Tests for dict_json utilities.
"""

import datetime

import pytest
from utils import dict_json


@pytest.mark.unit
class TestDictJsonUtils:
    """Test dict_json utility functions."""

    def test_flatten_dict(self):
        """Test dictionary flattening."""
        nested = {
            "level1": {
                "level2": "value",
            },
            "top": "value2",
        }
        flattened = dict_json.flatten_dict(nested)
        assert "level1_level2" in flattened
        assert flattened["level1_level2"] == "value"
        assert flattened["top"] == "value2"

    def test_flatten_dict_with_datetime(self):
        """Test flattening dictionary with datetime."""
        dt = datetime.datetime.now()
        nested = {"timestamp": dt}
        flattened = dict_json.flatten_dict(nested)
        assert isinstance(flattened["timestamp"], str)
        assert dt.isoformat() in flattened["timestamp"]

    def test_flatten_dict_with_list(self):
        """Test flattening dictionary with list."""
        nested = {"items": [1, 2, 3]}
        flattened = dict_json.flatten_dict(nested)
        assert flattened["items"] == "1,2,3"

    def test_flatten_dict_empty(self):
        """Test flattening empty dictionary."""
        flattened = dict_json.flatten_dict({})
        assert flattened == {}

    def test_flatten_dict_nested_empty(self):
        """Test flattening nested dictionary with empty inner dict."""
        nested = {"outer": {}}
        flattened = dict_json.flatten_dict(nested)
        assert "outer" in flattened or flattened == {}
