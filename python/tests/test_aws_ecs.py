"""
Tests for AWS ECS utilities.
"""

from unittest.mock import MagicMock, Mock, patch

from aws.ecs import ECSHandler, FargateDeploymentRollbackException
import pytest


@pytest.mark.aws
@pytest.mark.unit
class TestECSHandler:
    """Test ECSHandler class."""

    @patch("aws.ecs.boto3_session.Session")
    def test_ecs_handler_initialization(self, mock_session):
        """Test ECSHandler initialization."""
        mock_session_instance = MagicMock()
        mock_session.return_value = mock_session_instance
        mock_session_instance.client.return_value = MagicMock()

        handler = ECSHandler()
        assert handler.session is not None
        assert handler.ecs_client is not None
        assert handler.region == "us-east-1"

    @patch("aws.ecs.boto3_session.Session")
    def test_ecs_handler_with_session(self, mock_session):
        """Test ECSHandler with provided session."""
        mock_session_obj = MagicMock()
        mock_session_obj.client.return_value = MagicMock()

        handler = ECSHandler(session=mock_session_obj)
        assert handler.session == mock_session_obj

    @patch("aws.ecs.boto3_session.Session")
    def test_ecs_handler_custom_region(self, mock_session):
        """Test ECSHandler with custom region."""
        mock_session_instance = MagicMock()
        mock_session.return_value = mock_session_instance
        mock_session_instance.client.return_value = MagicMock()

        handler = ECSHandler(region_name="us-west-2")
        assert handler.region == "us-west-2"

    @patch("aws.ecs.boto3_session.Session")
    def test_create_service(self, mock_session):
        """Test creating ECS service."""
        mock_session_instance = MagicMock()
        mock_ecs_client = MagicMock()
        mock_ecs_client.create_service.return_value = {"service": {"serviceName": "test-service"}}
        mock_session_instance.client.return_value = mock_ecs_client
        mock_session.return_value = mock_session_instance

        handler = ECSHandler(session=mock_session_instance)
        response = handler.create_service(
            cluster_name="test-cluster",
            service_name="test-service",
            task_definition="test-task:1",
        )
        assert response is not None
        mock_ecs_client.create_service.assert_called_once()

    @patch("aws.ecs.boto3_session.Session")
    def test_list_clusters(self, mock_session):
        """Test listing ECS clusters."""
        mock_session_instance = MagicMock()
        mock_ecs_client = MagicMock()
        mock_ecs_client.list_clusters.return_value = {
            "clusterArns": ["arn:aws:ecs:us-east-1:123:cluster/test"]
        }
        mock_session_instance.client.return_value = mock_ecs_client
        mock_session.return_value = mock_session_instance

        handler = ECSHandler(session=mock_session_instance)
        clusters = handler.list_clusters()
        assert isinstance(clusters, list)
        mock_ecs_client.list_clusters.assert_called_once()

    @patch("aws.ecs.boto3_session.Session")
    def test_list_services(self, mock_session):
        """Test listing ECS services."""
        mock_session_instance = MagicMock()
        mock_ecs_client = MagicMock()
        mock_ecs_client.list_services.return_value = {
            "serviceArns": ["arn:aws:ecs:us-east-1:123:service/test-service"]
        }
        mock_session_instance.client.return_value = mock_ecs_client
        mock_session.return_value = mock_session_instance

        handler = ECSHandler(session=mock_session_instance)
        services = handler.list_services("test-cluster")
        assert isinstance(services, list)
        mock_ecs_client.list_services.assert_called_once()

    @patch("aws.ecs.boto3_session.Session")
    def test_delete_service(self, mock_session):
        """Test deleting ECS service."""
        mock_session_instance = MagicMock()
        mock_ecs_client = MagicMock()
        mock_ecs_client.delete_service.return_value = {"service": {"serviceName": "test-service"}}
        mock_session_instance.client.return_value = mock_ecs_client
        mock_session.return_value = mock_session_instance

        handler = ECSHandler(session=mock_session_instance)
        response = handler.delete_service("test-cluster", "test-service")
        assert response is not None
        mock_ecs_client.delete_service.assert_called_once()


@pytest.mark.aws
@pytest.mark.unit
class TestFargateDeploymentRollbackException:
    """Test FargateDeploymentRollbackException."""

    def test_exception_creation(self):
        """Test exception creation."""
        exc = FargateDeploymentRollbackException("test-service")
        assert exc.service_name == "test-service"
        assert "test-service" in str(exc)

    def test_exception_with_custom_message(self):
        """Test exception with custom message."""
        exc = FargateDeploymentRollbackException("test-service", "Custom error message")
        assert "Custom error message" in str(exc)
