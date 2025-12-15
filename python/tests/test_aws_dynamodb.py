"""
Tests for AWS DynamoDB utilities.
"""

from unittest.mock import MagicMock, patch

from aws.dynamodb import DynamoDBHandler
import pytest


@pytest.mark.aws
@pytest.mark.unit
class TestDynamoDBHandler:
    """Test DynamoDBHandler class."""

    @patch("aws.dynamodb.boto3_session.Session")
    def test_dynamodb_handler_initialization(self, mock_session):
        """Test DynamoDBHandler initialization."""
        mock_session_instance = MagicMock()
        mock_session.return_value = mock_session_instance
        mock_session_instance.resource.return_value = MagicMock()
        mock_session_instance.client.return_value = MagicMock()

        handler = DynamoDBHandler()
        assert handler.session is not None
        assert handler.dynamodb_resource is not None
        assert handler.dynamodb_client is not None

    @pytest.mark.integration
    def test_dynamodb_operations(self, moto_dynamodb):
        """Test DynamoDB operations with moto."""
        import boto3

        dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
        table = dynamodb.create_table(
            TableName="test-table",
            KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "id", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )

        handler = DynamoDBHandler()
        metadata = handler.get_table_metadata("test-table")
        assert metadata is not None

    @patch("aws.dynamodb.boto3_session.Session")
    def test_get_table_metadata(self, mock_session):
        """Test getting table metadata."""
        mock_session_instance = MagicMock()
        mock_dynamodb_client = MagicMock()
        mock_dynamodb_client.describe_table.return_value = {
            "Table": {"TableName": "test-table", "ItemCount": 0}
        }
        mock_session_instance.client.return_value = mock_dynamodb_client
        mock_session_instance.resource.return_value = MagicMock()
        mock_session.return_value = mock_session_instance

        handler = DynamoDBHandler(session=mock_session_instance)
        metadata = handler.get_table_metadata("test-table")
        assert "TableName" in metadata or metadata == {}
        mock_dynamodb_client.describe_table.assert_called_once()

    @patch("aws.dynamodb.boto3_session.Session")
    def test_update_record(self, mock_session):
        """Test updating a record."""
        mock_session_instance = MagicMock()
        mock_table = MagicMock()
        mock_table.update_item.return_value = {"Attributes": {"id": "test-id"}}
        mock_session_instance.resource.return_value.Table.return_value = mock_table
        mock_session_instance.client.return_value = MagicMock()
        mock_session.return_value = mock_session_instance

        handler = DynamoDBHandler(session=mock_session_instance)
        result = handler.update_record("test-table", {"id": "test-id"}, {"name": "test"})
        assert result is not None
        mock_table.update_item.assert_called_once()

    @patch("aws.dynamodb.boto3_session.Session")
    def test_push_record(self, mock_session):
        """Test pushing a record."""
        mock_session_instance = MagicMock()
        mock_table = MagicMock()
        mock_table.put_item.return_value = {}
        mock_session_instance.resource.return_value.Table.return_value = mock_table
        mock_session_instance.client.return_value = MagicMock()
        mock_session.return_value = mock_session_instance

        handler = DynamoDBHandler(session=mock_session_instance)
        result = handler.push_record("test-table", {"id": "test-id", "name": "test"})
        assert result is not None
        mock_table.put_item.assert_called_once()
