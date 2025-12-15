"""
Tests for SQL utilities.
"""

from unittest.mock import MagicMock, Mock, patch

import pytest
from utils.sql import run_sql


@pytest.mark.unit
class TestSQLUtils:
    """Test SQL utility functions."""

    @patch("utils.sql.secret_handler")
    @patch("utils.sql.PostgreAdapter")
    def test_run_sql_query(self, mock_postgres, mock_secret_handler):
        """Test running a SQL query."""
        # Mock database connection
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [{"id": 1, "name": "test"}]
        mock_cursor.__enter__ = Mock(return_value=mock_cursor)
        mock_cursor.__exit__ = Mock(return_value=False)
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.__enter__ = Mock(return_value=mock_conn)
        mock_conn.__exit__ = Mock(return_value=False)
        mock_postgres.connect.return_value = mock_conn

        result = run_sql(
            query="SELECT * FROM users",
            queryType="query",
            dbname="testdb",
            host="localhost",
            username="testuser",
            password="testpass",
        )

        assert result is not None
        mock_postgres.connect.assert_called_once()

    @patch("utils.sql.secret_handler")
    @patch("utils.sql.PostgreAdapter")
    def test_run_sql_with_secret(self, mock_postgres, mock_secret_handler):
        """Test running SQL with AWS Secrets Manager secret."""
        # Mock secret handler
        mock_secret_handler.get_secret.return_value = {
            "username": "secretuser",
            "password": "secretpass",
            "host": "secret-host",
            "port": 5432,
        }

        # Mock database connection
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []
        mock_cursor.__enter__ = Mock(return_value=mock_cursor)
        mock_cursor.__exit__ = Mock(return_value=False)
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.__enter__ = Mock(return_value=mock_conn)
        mock_conn.__exit__ = Mock(return_value=False)
        mock_postgres.connect.return_value = mock_conn

        result = run_sql(
            query="SELECT 1",
            queryType="query",
            dbname="testdb",
            secret="test-secret",
        )

        assert result is not None
        mock_secret_handler.get_secret.assert_called()

    @patch("utils.sql.PostgreAdapter")
    def test_run_sql_execute(self, mock_postgres):
        """Test running SQL execute operation."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.rowcount = 1
        mock_cursor.__enter__ = Mock(return_value=mock_cursor)
        mock_cursor.__exit__ = Mock(return_value=False)
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.__enter__ = Mock(return_value=mock_conn)
        mock_conn.__exit__ = Mock(return_value=False)
        mock_postgres.connect.return_value = mock_conn

        result = run_sql(
            query="UPDATE users SET name = 'test'",
            queryType="execute",
            dbname="testdb",
            host="localhost",
            username="testuser",
            password="testpass",
        )

        assert result is not None

    @patch("utils.sql.PostgreAdapter")
    def test_run_sql_error_handling(self, mock_postgres):
        """Test SQL error handling."""
        import psycopg2

        mock_postgres.connect.side_effect = psycopg2.OperationalError("Connection failed")

        with pytest.raises(psycopg2.OperationalError, match="Connection failed"):
            run_sql(
                query="SELECT 1",
                queryType="query",
                dbname="testdb",
                host="invalid",
                username="test",
                password="test",
            )
