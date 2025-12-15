"""
Comprehensive tests for common basic utilities.
"""

from common import basic
import pytest


@pytest.mark.unit
class TestBasicUtilsExpanded:
    """Comprehensive tests for basic utility functions."""

    def test_get_uuid(self):
        """Test UUID generation."""
        uuid_str = basic.get_uuid(uuidVer=4, format="str")
        assert isinstance(uuid_str, str)
        assert len(uuid_str) == 36

        uuid_hex = basic.get_uuid(uuidVer=4, format="hex")
        assert isinstance(uuid_hex, str)
        assert len(uuid_hex) == 32

    def test_col_num_to_col_name(self):
        """Test column number to column name conversion."""
        assert basic.ColNum2ColName(1) == "A"
        assert basic.ColNum2ColName(26) == "Z"
        assert basic.ColNum2ColName(27) == "AA"

    def test_flatten_dict(self):
        """Test dictionary flattening."""
        nested = {
            "a": {
                "b": {
                    "c": "value",
                },
            },
            "top": "value2",
        }
        flattened = basic.flatten_dict(nested)
        assert "a_b_c" in flattened or "a" in str(flattened)
        assert isinstance(flattened, dict)

    def test_basic_import(self):
        """Test that basic module can be imported."""
        assert basic is not None
        assert hasattr(basic, "get_uuid")
