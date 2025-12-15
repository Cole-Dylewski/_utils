"""
Tests for formatting tools utilities.
"""

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
from utils import formatting_tools


@pytest.mark.unit
class TestFormattingTools:
    """Test formatting tools utility functions."""

    @patch("utils.formatting_tools.s3_handler.send_to_s3")
    @patch("utils.formatting_tools.s3_handler.s3_to_df")
    def test_format_file(self, mock_s3_to_df, mock_send_to_s3):
        """Test format_file function."""
        # Mock S3 handler responses
        mock_df = pd.DataFrame({"col1": [1, 2], "col2": [3, 4]})
        mock_s3_to_df.return_value = mock_df
        mock_send_to_s3.return_value = None

        result = formatting_tools.format_file(
            bucket="test-bucket",
            objectKey="test/file.csv",
            log_id="log123",
        )
        assert result is not None
        assert len(result) == 3  # Returns (s3FileName, columns, data)
        mock_s3_to_df.assert_called_once()
        mock_send_to_s3.assert_called_once()

    @patch("utils.formatting_tools.s3_handler.send_to_s3")
    @patch("utils.formatting_tools.s3_handler.s3_to_df")
    def test_format_file_with_column_map_dict(self, mock_s3_to_df, mock_send_to_s3):
        """Test format_file with dictionary column mapping."""
        mock_df = pd.DataFrame({"old_col": [1, 2]})
        mock_s3_to_df.return_value = mock_df
        mock_send_to_s3.return_value = None

        column_map = {"old_col": "new_col"}
        result = formatting_tools.format_file(
            bucket="test-bucket",
            objectKey="test/file.csv",
            columnMap=column_map,
        )
        assert result is not None
        mock_s3_to_df.assert_called_once()

    @patch("utils.formatting_tools.s3_handler.send_to_s3")
    @patch("utils.formatting_tools.s3_handler.s3_to_df")
    def test_format_file_with_column_map_list(self, mock_s3_to_df, mock_send_to_s3):
        """Test format_file with list column mapping."""
        mock_df = pd.DataFrame({"col1": [1, 2], "col2": [3, 4]})
        mock_s3_to_df.return_value = mock_df
        mock_send_to_s3.return_value = None

        column_map = ["new_col1", "new_col2"]
        result = formatting_tools.format_file(
            bucket="test-bucket",
            objectKey="test/file.csv",
            columnMap=column_map,
        )
        assert result is not None
        mock_s3_to_df.assert_called_once()
