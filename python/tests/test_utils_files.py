"""
Tests for file utilities.
"""

import os
from pathlib import Path

import pytest
from utils import files


@pytest.mark.unit
class TestFileUtils:
    """Test file utility functions."""

    def test_files_import(self):
        """Test that files module can be imported."""
        assert files is not None

    def test_file_operations(self, temp_file, temp_dir):
        """Test file operations."""
        # Test that temp file exists
        assert os.path.exists(temp_file)
        assert Path(temp_file).read_text() == "test content"
        assert os.path.exists(temp_dir)
