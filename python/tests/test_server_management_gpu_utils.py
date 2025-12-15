"""
Tests for GPU utilities.
"""

from unittest.mock import MagicMock, patch

import pytest
from server_management import gpu_utils


@pytest.mark.unit
class TestGPUUtils:
    """Test GPU utility functions."""

    @patch("server_management.gpu_utils.subprocess.run")
    def test_detect_gpu_memory_via_ssh(self, mock_subprocess):
        """Test detecting GPU memory via SSH."""
        mock_result = MagicMock()
        mock_result.stdout = "8192\n"  # 8GB in MB
        mock_result.returncode = 0
        mock_subprocess.return_value = mock_result

        memory = gpu_utils.detect_gpu_memory_via_ssh(
            host="test-server",
            user="testuser",
            gpu_device_id="0",
        )
        assert memory is not None
        assert isinstance(memory, float)
        mock_subprocess.assert_called_once()

    @patch("server_management.gpu_utils.subprocess.run")
    def test_detect_gpu_memory_via_ssh_failure(self, mock_subprocess):
        """Test detecting GPU memory via SSH with failure."""
        mock_result = MagicMock()
        mock_result.stdout = ""
        mock_result.returncode = 1
        mock_subprocess.return_value = mock_result

        memory = gpu_utils.detect_gpu_memory_via_ssh(
            host="test-server",
            user="testuser",
        )
        assert memory is None

    def test_allocate_gpu_memory_for_vllm_instances(self):
        """Test allocating GPU memory for vLLM instances."""
        # Function takes memory values directly, not host/user
        result = gpu_utils.allocate_gpu_memory_for_vllm_instances(
            total_memory_gb=24.0,
            vllm_llm_memory_gb=8.0,
            vllm_embedding_memory_gb=4.0,
            vllm_ocr_memory_gb=4.0,
        )
        assert result is not None
        assert isinstance(result, dict)
        assert "vllm_llm_gpu_percentage" in result
        assert "vllm_embedding_gpu_percentage" in result
        assert "vllm_ocr_gpu_percentage" in result

    def test_allocate_gpu_memory(self):
        """Test allocating GPU memory."""
        # Function takes memory values directly, not host/user
        result = gpu_utils.allocate_gpu_memory(
            total_memory_gb=24.0,
            enable_vllm=True,
        )
        assert result is not None
        assert isinstance(result, dict)
        assert "backend_gpu_memory_gb" in result
        assert "ingest_gpu_memory_gb" in result
        assert "vllm_gpu_memory_gb" in result
