"""
Tests for misc utilities.
"""

import pytest
from utils import misc


@pytest.mark.unit
class TestMiscUtils:
    """Test misc utility functions."""

    def test_get_uuid(self):
        """Test UUID generation."""
        uuid_str = misc.get_uuid(uuidVer=4, format="str")
        assert isinstance(uuid_str, str)
        assert len(uuid_str) == 36  # Standard UUID format

    def test_get_uuid_hex(self):
        """Test UUID generation in hex format."""
        uuid_hex = misc.get_uuid(uuidVer=4, format="hex")
        assert isinstance(uuid_hex, str)
        assert len(uuid_hex) == 32  # Hex format without dashes

    def test_flatten_dict(self):
        """Test dictionary flattening."""
        nested = {
            "level1": {
                "level2": {"level3": "value"},
                "simple": "value2",
            },
            "top": "value3",
        }
        flattened = misc.flatten_dict(nested)
        assert "level1_level2_level3" in flattened
        assert flattened["level1_level2_level3"] == "value"
        assert flattened["top"] == "value3"

    def test_flatten_dict_custom_separator(self):
        """Test dictionary flattening with custom separator."""
        nested = {"a": {"b": "value"}}
        flattened = misc.flatten_dict(nested, sep=".")
        assert "a.b" in flattened

    def test_make_serializable(self):
        """Test making data serializable."""
        from datetime import datetime

        data = {
            "date": datetime.now(),
            "decimal": 123.45,
            "normal": "string",
        }
        serializable = misc.make_serializable(data)
        assert isinstance(serializable["date"], str)
        assert isinstance(serializable["normal"], str)

    def test_print_nested(self, capsys):
        """Test printing nested data structures."""
        nested = {"a": {"b": "value"}}
        misc.print_nested(nested)
        captured = capsys.readouterr()
        assert "a" in captured.out or "value" in captured.out

    def test_format_nested(self):
        """Test formatting nested data structures."""
        nested = {"a": {"b": "value"}}
        formatted = misc.format_nested(nested)
        assert isinstance(formatted, str)
        assert "a" in formatted or "value" in formatted
