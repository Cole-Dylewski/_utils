"""
Comprehensive tests for DataFrame utilities.
"""

import numpy as np
import pandas as pd
import pytest
from utils import dataframe


@pytest.mark.unit
class TestDataFrameUtilsExpanded:
    """Comprehensive tests for DataFrame utility functions."""

    def test_col_num_to_col_name(self):
        """Test column number to column name conversion."""
        assert dataframe.ColNum2ColName(1) == "A"
        assert dataframe.ColNum2ColName(26) == "Z"
        assert dataframe.ColNum2ColName(27) == "AA"
        assert dataframe.ColNum2ColName(52) == "AZ"

    def test_build_rand_df(self, sample_dataframe):
        """Test building random DataFrame."""
        df = dataframe.build_rand_df(randRange=100, colNum=5, rowNum=10)
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 10
        assert len(df.columns) == 5

    def test_dataframe_size_in_mb(self, sample_dataframe):
        """Test calculating DataFrame size in MB."""
        size_mb = dataframe.dataframe_size_in_mb(sample_dataframe)
        assert isinstance(size_mb, float)
        assert size_mb >= 0

    def test_type_check(self):
        """Test type checking function."""
        assert dataframe.type_check(123) is not None
        assert dataframe.type_check("string") is not None
        assert dataframe.type_check(True) is not None

    def test_get_col_type(self, sample_dataframe):
        """Test getting column type."""
        col_type = dataframe.getColType(sample_dataframe["id"])
        assert col_type is not None

    def test_auto_convert(self, sample_dataframe):
        """Test auto-converting DataFrame columns."""
        converted = dataframe.autoConvert(sample_dataframe)
        assert isinstance(converted, pd.DataFrame)

    def test_normalize_col_names(self):
        """Test normalizing column names."""
        cols = ["Column Name", "another-column", "Column_Name"]
        normalized = dataframe.normalize_col_names(cols)
        assert isinstance(normalized, list)
        assert len(normalized) == len(cols)
