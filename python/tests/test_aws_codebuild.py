"""
Tests for AWS CodeBuild utilities.
"""

from unittest.mock import MagicMock, patch

from aws.codebuild import CodebuildHandler
import pytest


@pytest.mark.aws
@pytest.mark.unit
class TestCodebuildHandler:
    """Test CodebuildHandler class."""

    @patch("aws.boto3_session.Session")
    def test_codebuild_handler_initialization(self, mock_session):
        """Test CodebuildHandler initialization."""
        mock_session_instance = MagicMock()
        mock_session.return_value = mock_session_instance
        mock_session_instance.client.return_value = MagicMock()

        handler = CodebuildHandler()
        assert handler.session is not None
        assert handler.codebuild_client is not None
        assert handler.logs_client is not None

    @patch("aws.boto3_session.Session")
    def test_codebuild_handler_with_session(self, mock_session):
        """Test CodebuildHandler with provided session."""
        mock_session_obj = MagicMock()
        mock_session_obj.client.return_value = MagicMock()

        handler = CodebuildHandler(session=mock_session_obj)
        assert handler.session == mock_session_obj

    @patch("aws.boto3_session.Session")
    def test_get_project_config(self, mock_session):
        """Test getting CodeBuild project configuration."""
        mock_session_instance = MagicMock()
        mock_codebuild_client = MagicMock()
        mock_codebuild_client.batch_get_projects.return_value = {
            "projects": [{"name": "test-project", "description": "Test project"}]
        }
        mock_session_instance.client.return_value = mock_codebuild_client
        mock_session.return_value = mock_session_instance

        handler = CodebuildHandler(session=mock_session_instance)
        config = handler.get_project_config("test-project")
        assert config is not None
        mock_codebuild_client.batch_get_projects.assert_called_once()

    @patch("aws.boto3_session.Session")
    def test_get_project_config_not_found(self, mock_session):
        """Test getting non-existent project raises error."""
        mock_session_instance = MagicMock()
        mock_codebuild_client = MagicMock()
        mock_codebuild_client.batch_get_projects.return_value = {"projects": []}
        mock_session_instance.client.return_value = mock_codebuild_client
        mock_session.return_value = mock_session_instance

        handler = CodebuildHandler(session=mock_session_instance)
        with pytest.raises(ValueError, match="No project found"):
            handler.get_project_config("non-existent-project")

    @patch("aws.boto3_session.Session")
    def test_start_build(self, mock_session):
        """Test starting a CodeBuild project."""
        mock_session_instance = MagicMock()
        mock_codebuild_client = MagicMock()
        mock_codebuild_client.start_build.return_value = {
            "build": {"id": "test-build-id", "projectName": "test-project"}
        }
        mock_session_instance.client.return_value = mock_codebuild_client
        mock_session.return_value = mock_session_instance

        handler = CodebuildHandler(session=mock_session_instance)
        response = handler.start_build("test-project")
        assert response is not None
        mock_codebuild_client.start_build.assert_called_once()
