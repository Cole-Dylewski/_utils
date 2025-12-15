"""
Tests for server management utilities.
"""

from unittest.mock import MagicMock, Mock, patch

import pytest
from server_management.ansible import AnsibleHandler
from server_management.terraform import TerraformHandler


@pytest.mark.unit
class TestTerraformHandler:
    """Test TerraformHandler class."""

    def test_terraform_handler_initialization(self):
        """Test TerraformHandler initialization."""
        handler = TerraformHandler(project_dir="./test-terraform")
        assert handler.project_dir == "./test-terraform"

    @patch("server_management.terraform.subprocess.run")
    def test_terraform_init(self, mock_subprocess):
        """Test terraform init."""
        mock_subprocess.return_value = MagicMock(returncode=0)
        handler = TerraformHandler(project_dir="./test")
        result = handler.init()
        assert result is not None
        mock_subprocess.assert_called()

    @patch("server_management.terraform.subprocess.run")
    def test_terraform_plan(self, mock_subprocess):
        """Test terraform plan."""
        mock_subprocess.return_value = MagicMock(returncode=0, stdout="plan output")
        handler = TerraformHandler(project_dir="./test")
        result = handler.plan()
        assert result is not None
        mock_subprocess.assert_called()

    @patch("server_management.terraform.subprocess.run")
    def test_terraform_apply(self, mock_subprocess):
        """Test terraform apply."""
        mock_subprocess.return_value = MagicMock(returncode=0)
        handler = TerraformHandler(project_dir="./test")
        result = handler.apply()
        assert result is not None
        mock_subprocess.assert_called()

    def test_terraform_handler_invalid_directory(self):
        """Test TerraformHandler with invalid directory raises error."""
        with pytest.raises(ValueError, match="does not exist"):
            TerraformHandler(project_dir="./non-existent-directory")

    @patch("server_management.terraform.subprocess.run")
    def test_terraform_destroy(self, mock_subprocess):
        """Test terraform destroy."""
        mock_subprocess.return_value = MagicMock(returncode=0)
        handler = TerraformHandler(project_dir="./test")
        result = handler.destroy()
        assert result is not None
        mock_subprocess.assert_called()

    @patch("server_management.terraform.subprocess.run")
    def test_terraform_output(self, mock_subprocess):
        """Test terraform output."""
        mock_subprocess.return_value = MagicMock(returncode=0, stdout='{"key": "value"}')
        handler = TerraformHandler(project_dir="./test")
        output = handler.output()
        assert isinstance(output, dict)
        mock_subprocess.assert_called()


@pytest.mark.unit
class TestAnsibleHandler:
    """Test AnsibleHandler class."""

    def test_ansible_handler_initialization(self):
        """Test AnsibleHandler initialization."""
        handler = AnsibleHandler(ansible_dir="./test-ansible", inventory="hosts.yml")
        assert handler.ansible_dir == "./test-ansible"
        assert handler.inventory == "hosts.yml"

    @patch("server_management.ansible.subprocess.run")
    def test_ansible_run_playbook(self, mock_subprocess):
        """Test running Ansible playbook."""
        mock_subprocess.return_value = MagicMock(returncode=0)
        handler = AnsibleHandler(ansible_dir="./test", inventory="hosts.yml")
        result = handler.run_playbook("test.yml")
        assert result is not None
        mock_subprocess.assert_called()
