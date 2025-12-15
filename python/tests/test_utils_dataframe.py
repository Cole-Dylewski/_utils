"""
Tests for DataFrame utilities.
"""

import pytest
from utils import dataframe


@pytest.mark.unit
class TestDataFrameUtils:
    """Test DataFrame utility functions."""

    def test_dataframe_import(self, sample_dataframe):
        """Test DataFrame utilities can be imported."""
        assert dataframe is not None

    def test_dataframe_operations(self, sample_dataframe):
        """Test DataFrame operations."""
        # Add specific tests based on dataframe.py functions
        assert sample_dataframe is not None
        assert len(sample_dataframe) == 3
