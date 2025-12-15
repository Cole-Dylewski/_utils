"""
Tests for AWS S3 utilities.
"""

from unittest.mock import MagicMock, Mock, patch

from aws.s3 import S3Handler
import pytest


@pytest.mark.aws
@pytest.mark.unit
class TestS3Handler:
    """Test S3Handler class."""

    @patch("aws.boto3_session.Session")
    def test_s3_handler_initialization(self, mock_session):
        """Test S3Handler initialization."""
        mock_session_instance = MagicMock()
        mock_session.return_value = mock_session_instance
        mock_session_instance.resource.return_value = MagicMock()
        mock_session_instance.client.return_value = MagicMock()

        handler = S3Handler()
        assert handler.session is not None
        assert handler.s3_resource is not None
        assert handler.s3_client is not None

    @patch("aws.boto3_session.Session")
    def test_s3_handler_with_session(self, mock_session):
        """Test S3Handler with provided session."""
        mock_session_obj = MagicMock()
        mock_session_obj.resource.return_value = MagicMock()
        mock_session_obj.client.return_value = MagicMock()

        handler = S3Handler(session=mock_session_obj)
        assert handler.session == mock_session_obj

    @pytest.mark.integration
    def test_s3_find_keys_containing_string(self, moto_s3):
        """Test finding S3 keys containing string."""
        import boto3

        # Create bucket and objects
        s3_client = boto3.client("s3", region_name="us-east-1")
        s3_client.create_bucket(Bucket="test-bucket")
        s3_client.put_object(Bucket="test-bucket", Key="test-file-1.txt", Body=b"content1")
        s3_client.put_object(Bucket="test-bucket", Key="test-file-2.txt", Body=b"content2")
        s3_client.put_object(Bucket="test-bucket", Key="other-file.txt", Body=b"content3")

        handler = S3Handler()
        keys = handler.s3_find_keys_containing_string("test-bucket", "test-file")
        assert len(keys) == 2
        assert "test-file-1.txt" in keys
        assert "test-file-2.txt" in keys

    @pytest.mark.integration
    def test_s3_get_file_metadata(self, moto_s3):
        """Test getting S3 file metadata."""
        import boto3

        s3_client = boto3.client("s3", region_name="us-east-1")
        s3_client.create_bucket(Bucket="test-bucket")
        s3_client.put_object(Bucket="test-bucket", Key="test.txt", Body=b"content")

        handler = S3Handler()
        metadata = handler.get_s3_file_metadata("test-bucket", "test.txt")
        assert metadata is not None
        assert "LastModified" in metadata or "last_modified" in str(metadata).lower()

    @pytest.mark.integration
    def test_s3_delete_file(self, moto_s3):
        """Test deleting S3 file."""
        import boto3

        s3_client = boto3.client("s3", region_name="us-east-1")
        s3_client.create_bucket(Bucket="test-bucket")
        s3_client.put_object(Bucket="test-bucket", Key="test.txt", Body=b"content")

        handler = S3Handler()
        result = handler.delete_s3_file("test-bucket", "test.txt")
        assert result is True

        # Verify file is deleted
        from botocore.exceptions import ClientError

        with pytest.raises(ClientError, match=r"NoSuchKey|404"):
            handler.get_s3_file_metadata("test-bucket", "test.txt")

    @pytest.mark.integration
    def test_s3_create_presigned_url(self, moto_s3):
        """Test creating presigned URL."""
        import boto3

        s3_client = boto3.client("s3", region_name="us-east-1")
        s3_client.create_bucket(Bucket="test-bucket")
        s3_client.put_object(Bucket="test-bucket", Key="test.txt", Body=b"content")

        handler = S3Handler()
        url = handler.create_presigned_url("test-bucket", "test.txt", expiration=3600)
        assert url is not None
        assert "test-bucket" in url
        assert "test.txt" in url
