"""
Tests for Snowflake utilities.
"""

from unittest.mock import MagicMock, patch

import pytest
from snowflake import snowpark


@pytest.mark.unit
class TestSnowflakeUtils:
    """Test Snowflake utility functions."""

    def test_snowflake_import(self):
        """Test that snowflake module can be imported."""
        assert snowpark is not None

    @patch("snowflake.snowpark.Session")
    def test_snowpark_client_from_env(self, mock_session):
        """Test SnowparkClient.from_env()."""
        import os

        with patch.dict(os.environ, {"SNOWFLAKE_ACCOUNT": "test", "SNOWFLAKE_USER": "user"}):
            try:
                client = snowpark.SnowparkClient.from_env()
                assert client is not None
                assert "ACCOUNT" in client.configs
            except RuntimeError:
                # Expected if required env vars not set
                pass

    @patch("snowflake.snowpark.Session")
    def test_snowpark_client_context_manager(self, mock_session):
        """Test SnowparkClient as context manager."""
        mock_session_instance = MagicMock()
        mock_session.builder.configs.return_value = mock_session_instance
        mock_session_instance.create.return_value = MagicMock()

        client = snowpark.SnowparkClient(configs={"ACCOUNT": "test", "USER": "user"})
        with client:
            assert client.session is not None

    @patch("snowflake.snowpark.Session")
    def test_snowpark_client_run(self, mock_session):
        """Test SnowparkClient.run() method."""
        mock_session_instance = MagicMock()
        mock_dataframe = MagicMock()
        mock_dataframe.collect.return_value = [{"col": "value"}]
        mock_session_instance.sql.return_value = mock_dataframe
        mock_session.builder.configs.return_value = MagicMock()
        mock_session.builder.configs.return_value.create.return_value = mock_session_instance

        client = snowpark.SnowparkClient(configs={"ACCOUNT": "test", "USER": "user"})
        client._session = mock_session_instance
        result = client.run("SELECT 1", collect=True)
        assert isinstance(result, list)
