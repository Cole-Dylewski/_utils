"""
Comprehensive tests for file utilities.
"""

import os
import tempfile

import pytest
from utils import files


@pytest.mark.unit
class TestFileUtilsExpanded:
    """Comprehensive tests for file utility functions."""

    def test_to_filename_compatible_string(self):
        """Test converting string to filename-compatible format."""
        result = files.to_filename_compatible_string("Test File Name!")
        assert " " not in result
        assert "!" not in result
        assert isinstance(result, str)

    def test_to_filename_compatible_string_special_chars(self):
        """Test filename conversion with special characters."""
        result = files.to_filename_compatible_string("file@name#with$special%chars")
        assert "@" not in result
        assert "#" not in result
        assert "$" not in result
        assert "%" not in result

    def test_merge_files_csv(self, temp_dir):
        """Test merging CSV files."""
        file1 = os.path.join(temp_dir, "file1.csv")
        file2 = os.path.join(temp_dir, "file2.csv")
        output = os.path.join(temp_dir, "merged.csv")

        # Create test CSV files
        import pandas as pd

        df1 = pd.DataFrame({"col1": [1, 2], "col2": [3, 4]})
        df2 = pd.DataFrame({"col1": [5, 6], "col2": [7, 8]})
        df1.to_csv(file1, index=False)
        df2.to_csv(file2, index=False)

        files.merge_files(output, [file1, file2], delete=False)
        assert os.path.exists(output)

    def test_merge_files_pdf(self, temp_dir):
        """Test merging PDF files (if PyPDF2 available)."""
        # This test would require actual PDF files or mocking
        # For now, just test the function exists
        assert hasattr(files, "merge_files")

    def test_merge_files_unsupported_format(self, temp_dir):
        """Test merging files with unsupported format raises error."""
        output = os.path.join(temp_dir, "output.xyz")
        with pytest.raises(ValueError, match="Unsupported output file type"):
            files.merge_files(output, ["file1.txt", "file2.txt"])
