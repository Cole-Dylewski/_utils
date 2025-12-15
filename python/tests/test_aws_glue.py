"""
Tests for AWS Glue utilities.
"""

from unittest.mock import MagicMock, patch

from aws.glue import GlueHandler
import pytest


@pytest.mark.aws
@pytest.mark.unit
class TestGlueHandler:
    """Test GlueHandler class."""

    @patch("aws.glue.boto3_session.Session")
    def test_glue_handler_initialization(self, mock_session):
        """Test GlueHandler initialization."""
        mock_session_instance = MagicMock()
        mock_session.return_value = mock_session_instance
        mock_session_instance.client.return_value = MagicMock()

        handler = GlueHandler()
        assert handler.session is not None
        assert handler.glue_client is not None
        assert handler.logs_client is not None
        assert handler.region == "us-east-1"

    @patch("aws.glue.boto3_session.Session")
    def test_glue_handler_with_session(self, mock_session):
        """Test GlueHandler with provided session."""
        mock_session_obj = MagicMock()
        mock_session_obj.client.return_value = MagicMock()

        handler = GlueHandler(session=mock_session_obj)
        assert handler.session == mock_session_obj

    @patch("aws.glue.boto3_session.Session")
    def test_get_current_glue_job_metadata(self, mock_session):
        """Test getting Glue job metadata."""
        mock_session_instance = MagicMock()
        mock_glue_client = MagicMock()
        mock_glue_client.get_job.return_value = {"Job": {"Name": "test-job", "Role": "test-role"}}
        mock_session_instance.client.return_value = mock_glue_client
        mock_session.return_value = mock_session_instance

        handler = GlueHandler(session=mock_session_instance)
        metadata = handler.get_current_glue_job_metadata("test-job")
        assert metadata is not None
        assert "Name" in metadata or metadata == {}
        mock_glue_client.get_job.assert_called_once()

    @patch("aws.glue.boto3_session.Session")
    def test_get_current_glue_job_metadata_no_job_name(self, mock_session):
        """Test getting Glue job metadata without job name raises error."""
        mock_session_instance = MagicMock()
        mock_session_instance.client.return_value = MagicMock()
        mock_session.return_value = mock_session_instance

        handler = GlueHandler(session=mock_session_instance)
        with pytest.raises(ValueError, match="JOB_NAME environment variable not set"):
            handler.get_current_glue_job_metadata("")

    @patch("aws.glue.boto3_session.Session")
    def test_delete_job(self, mock_session):
        """Test deleting Glue job."""
        mock_session_instance = MagicMock()
        mock_glue_client = MagicMock()
        mock_glue_client.delete_job.return_value = {}
        mock_session_instance.client.return_value = mock_glue_client
        mock_session.return_value = mock_session_instance

        handler = GlueHandler(session=mock_session_instance)
        handler.delete_job("test-job")
        mock_glue_client.delete_job.assert_called_once_with(JobName="test-job")

    @patch("aws.glue.boto3_session.Session")
    def test_trigger_glue_job(self, mock_session):
        """Test triggering Glue job."""
        mock_session_instance = MagicMock()
        mock_glue_client = MagicMock()
        mock_glue_client.start_job_run.return_value = {"JobRunId": "test-run-id"}
        mock_session_instance.client.return_value = mock_glue_client
        mock_session.return_value = mock_session_instance

        handler = GlueHandler(session=mock_session_instance)
        run_id = handler.trigger_glue_job("test-job")
        assert run_id == "test-run-id"
        mock_glue_client.start_job_run.assert_called_once()
