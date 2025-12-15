"""
Tests for AWS Lambda utilities.
"""

from unittest.mock import MagicMock, patch

from aws.aws_lambda import LambdaHandler
import pytest


@pytest.mark.aws
@pytest.mark.unit
class TestLambdaHandler:
    """Test LambdaHandler class."""

    @patch("aws.boto3_session.Session")
    def test_lambda_handler_initialization(self, mock_session):
        """Test LambdaHandler initialization."""
        mock_session_instance = MagicMock()
        mock_session.return_value = mock_session_instance
        mock_session_instance.client.return_value = MagicMock()

        handler = LambdaHandler()
        assert handler.session is not None
        assert handler.lambda_client is not None

    @patch("aws.boto3_session.Session")
    def test_lambda_handler_with_session(self, mock_session):
        """Test LambdaHandler with provided session."""
        mock_session_obj = MagicMock()
        mock_session_obj.client.return_value = MagicMock()

        handler = LambdaHandler(session=mock_session_obj)
        assert handler.session == mock_session_obj

    @patch("aws.boto3_session.Session")
    def test_invoke_lambda(self, mock_session):
        """Test invoking Lambda function."""
        mock_session_instance = MagicMock()
        mock_lambda_client = MagicMock()
        mock_lambda_client.invoke.return_value = {
            "StatusCode": 200,
            "Payload": MagicMock(read=lambda: b'{"result": "success"}'),
        }
        mock_session_instance.client.return_value = mock_lambda_client
        mock_session.return_value = mock_session_instance

        handler = LambdaHandler(session=mock_session_instance)
        response = handler.invoke_lambda(
            function_name="test-function",
            payload={"key": "value"},
        )
        assert response is not None
        mock_lambda_client.invoke.assert_called_once()

    def test_context_to_json(self):
        """Test converting Lambda context to JSON."""
        from aws.aws_lambda import context_to_json

        class MockContext:
            function_name = "test-function"
            function_version = "$LATEST"
            invoked_function_arn = "arn:aws:lambda:us-east-1:123:function:test"
            memory_limit_in_mb = 128
            aws_request_id = "test-request-id"
            log_stream_name = "test-log-stream"
            log_group_name = "/aws/lambda/test-function"

        context = MockContext()
        result = context_to_json(context)
        assert isinstance(result, dict)
        assert "function_name" in result
