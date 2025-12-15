"""
Tests for server management utilities.
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest
from server_management.ansible import AnsibleHandler
from server_management.terraform import TerraformHandler


@pytest.mark.unit
class TestTerraformHandler:
    """Test TerraformHandler class."""

    def test_terraform_handler_initialization(self, temp_dir):
        """Test TerraformHandler initialization."""
        handler = TerraformHandler(project_dir=temp_dir)
        assert handler.project_dir == Path(temp_dir).resolve()
        assert handler.is_remote is False

    def test_terraform_handler_remote_initialization(self, temp_dir):
        """Test TerraformHandler with remote host."""
        handler = TerraformHandler(project_dir=temp_dir, remote_host="example.com")
        assert handler.is_remote is True
        assert handler.remote_host == "example.com"

    def test_terraform_handler_remote_with_user(self, temp_dir):
        """Test TerraformHandler with user@host format."""
        handler = TerraformHandler(project_dir=temp_dir, remote_host="user@example.com")
        assert handler.remote_user == "user"
        assert handler.remote_host == "example.com"

    def test_terraform_handler_invalid_directory(self):
        """Test TerraformHandler with invalid directory raises error."""
        with pytest.raises(ValueError, match="does not exist"):
            TerraformHandler(project_dir="./non-existent-directory-12345")

    @patch("server_management.terraform.subprocess.run")
    def test_terraform_init(self, mock_subprocess, temp_dir):
        """Test terraform init."""
        mock_subprocess.return_value = MagicMock(returncode=0, stdout="", stderr="")
        handler = TerraformHandler(project_dir=temp_dir)
        result = handler.init()
        assert result is not None
        assert result.returncode == 0
        mock_subprocess.assert_called()

    @patch("server_management.terraform.subprocess.run")
    def test_terraform_init_with_upgrade(self, mock_subprocess, temp_dir):
        """Test terraform init with upgrade."""
        mock_subprocess.return_value = MagicMock(returncode=0)
        handler = TerraformHandler(project_dir=temp_dir)
        result = handler.init(upgrade=True)
        assert result is not None
        mock_subprocess.assert_called()

    @patch("server_management.terraform.subprocess.run")
    def test_terraform_plan(self, mock_subprocess, temp_dir):
        """Test terraform plan."""
        mock_subprocess.return_value = MagicMock(returncode=0, stdout="plan output", stderr="")
        handler = TerraformHandler(project_dir=temp_dir)
        result, is_crd_error = handler.plan()
        assert result is not None
        assert isinstance(is_crd_error, bool)
        mock_subprocess.assert_called()

    @patch("server_management.terraform.subprocess.run")
    def test_terraform_plan_with_vars(self, mock_subprocess, temp_dir):
        """Test terraform plan with variables."""
        mock_subprocess.return_value = MagicMock(returncode=0, stdout="", stderr="")
        handler = TerraformHandler(project_dir=temp_dir)
        result, _ = handler.plan(vars={"var1": "value1", "var2": 123})
        assert result is not None
        mock_subprocess.assert_called()

    @patch("server_management.terraform.subprocess.run")
    def test_terraform_apply(self, mock_subprocess, temp_dir):
        """Test terraform apply."""
        mock_subprocess.return_value = MagicMock(returncode=0, stdout="", stderr="")
        handler = TerraformHandler(project_dir=temp_dir, auto_approve=True)
        result = handler.apply()
        assert result is not None
        assert result.returncode == 0
        mock_subprocess.assert_called()

    @patch("server_management.terraform.subprocess.run")
    def test_terraform_apply_with_plan_file(self, mock_subprocess, temp_dir):
        """Test terraform apply with plan file."""
        mock_subprocess.return_value = MagicMock(returncode=0)
        handler = TerraformHandler(project_dir=temp_dir)
        result = handler.apply(plan_file="plan.tfplan")
        assert result is not None
        mock_subprocess.assert_called()

    @patch("server_management.terraform.subprocess.run")
    def test_terraform_destroy(self, mock_subprocess, temp_dir):
        """Test terraform destroy."""
        mock_subprocess.return_value = MagicMock(returncode=0, stdout="", stderr="")
        handler = TerraformHandler(project_dir=temp_dir, auto_approve=True)
        result = handler.destroy()
        assert result is not None
        assert result.returncode == 0
        mock_subprocess.assert_called()

    def test_terraform_destroy_requires_approval(self, temp_dir):
        """Test terraform destroy requires auto_approve."""
        handler = TerraformHandler(project_dir=temp_dir, auto_approve=False)
        with pytest.raises(ValueError, match="requires auto_approve"):
            handler.destroy()

    @patch("server_management.terraform.subprocess.run")
    def test_terraform_output(self, mock_subprocess, temp_dir):
        """Test terraform output."""
        output_data = {"key": "value", "number": 123}
        mock_subprocess.return_value = MagicMock(
            returncode=0, stdout=json.dumps(output_data), stderr=""
        )
        handler = TerraformHandler(project_dir=temp_dir)
        output = handler.output()
        assert isinstance(output, dict)
        assert "key" in output
        mock_subprocess.assert_called()

    @patch("server_management.terraform.subprocess.run")
    def test_terraform_output_single_name(self, mock_subprocess, temp_dir):
        """Test terraform output with specific name."""
        output_data = {"value": "test_value", "sensitive": False}
        mock_subprocess.return_value = MagicMock(
            returncode=0, stdout=json.dumps(output_data), stderr=""
        )
        handler = TerraformHandler(project_dir=temp_dir)
        output = handler.output(name="test_output")
        assert isinstance(output, dict)
        mock_subprocess.assert_called()

    @patch("server_management.terraform.subprocess.run")
    def test_terraform_validate(self, mock_subprocess, temp_dir):
        """Test terraform validate."""
        mock_subprocess.return_value = MagicMock(returncode=0, stdout="Success!", stderr="")
        handler = TerraformHandler(project_dir=temp_dir)
        is_valid, message = handler.validate()
        assert is_valid is True
        assert "Success" in message
        mock_subprocess.assert_called()

    @patch("server_management.terraform.subprocess.run")
    def test_terraform_validate_invalid(self, mock_subprocess, temp_dir):
        """Test terraform validate with invalid config."""
        mock_subprocess.return_value = MagicMock(
            returncode=1, stdout="", stderr="Error: Invalid configuration"
        )
        handler = TerraformHandler(project_dir=temp_dir)
        is_valid, message = handler.validate()
        assert is_valid is False
        assert "Invalid" in message

    @patch("server_management.terraform.subprocess.run")
    def test_terraform_fmt(self, mock_subprocess, temp_dir):
        """Test terraform fmt."""
        mock_subprocess.return_value = MagicMock(returncode=0)
        handler = TerraformHandler(project_dir=temp_dir)
        result = handler.fmt()
        assert result is not None
        mock_subprocess.assert_called()

    @patch("server_management.terraform.subprocess.run")
    def test_terraform_state_list(self, mock_subprocess, temp_dir):
        """Test terraform state list."""
        mock_subprocess.return_value = MagicMock(
            returncode=0, stdout="resource1\nresource2\n", stderr=""
        )
        handler = TerraformHandler(project_dir=temp_dir)
        resources = handler.state_list()
        assert isinstance(resources, list)
        assert len(resources) == 2
        mock_subprocess.assert_called()

    @patch("server_management.terraform.subprocess.run")
    def test_terraform_state_show(self, mock_subprocess, temp_dir):
        """Test terraform state show."""
        state_data = {"type": "aws_instance", "name": "test"}
        mock_subprocess.return_value = MagicMock(
            returncode=0, stdout=json.dumps(state_data), stderr=""
        )
        handler = TerraformHandler(project_dir=temp_dir)
        state = handler.state_show("resource.address")
        assert isinstance(state, dict)
        mock_subprocess.assert_called()

    @patch("server_management.terraform.subprocess.run")
    def test_terraform_workspace_list(self, mock_subprocess, temp_dir):
        """Test terraform workspace list."""
        mock_subprocess.return_value = MagicMock(
            returncode=0, stdout="default\n* dev\nprod\n", stderr=""
        )
        handler = TerraformHandler(project_dir=temp_dir)
        workspaces = handler.workspace_list()
        assert isinstance(workspaces, list)
        assert "default" in workspaces
        assert "dev" in workspaces
        mock_subprocess.assert_called()

    @patch("server_management.terraform.subprocess.run")
    def test_terraform_workspace_select(self, mock_subprocess, temp_dir):
        """Test terraform workspace select."""
        mock_subprocess.return_value = MagicMock(returncode=0)
        handler = TerraformHandler(project_dir=temp_dir)
        result = handler.workspace_select("dev")
        assert result is not None
        mock_subprocess.assert_called()

    @patch("server_management.terraform.subprocess.run")
    def test_terraform_workspace_new(self, mock_subprocess, temp_dir):
        """Test terraform workspace new."""
        mock_subprocess.return_value = MagicMock(returncode=0)
        handler = TerraformHandler(project_dir=temp_dir)
        result = handler.workspace_new("new_workspace")
        assert result is not None
        mock_subprocess.assert_called()

    @patch("server_management.terraform.subprocess.run")
    def test_terraform_workspace_delete(self, mock_subprocess, temp_dir):
        """Test terraform workspace delete."""
        mock_subprocess.return_value = MagicMock(returncode=0)
        handler = TerraformHandler(project_dir=temp_dir)
        result = handler.workspace_delete("old_workspace")
        assert result is not None
        mock_subprocess.assert_called()

    @patch("server_management.terraform.subprocess.run")
    def test_terraform_command_error(self, mock_subprocess, temp_dir):
        """Test terraform command with error."""
        mock_subprocess.side_effect = FileNotFoundError()
        handler = TerraformHandler(project_dir=temp_dir)
        with pytest.raises(ValueError, match="is not installed"):
            handler.init()


@pytest.mark.unit
class TestAnsibleHandler:
    """Test AnsibleHandler class."""

    def test_ansible_handler_initialization(self, temp_dir):
        """Test AnsibleHandler initialization."""
        handler = AnsibleHandler(ansible_dir=temp_dir)
        assert handler.ansible_dir == Path(temp_dir).resolve()
        assert handler.is_remote is False

    def test_ansible_handler_remote_initialization(self, temp_dir):
        """Test AnsibleHandler with remote host."""
        handler = AnsibleHandler(ansible_dir=temp_dir, remote_host="example.com")
        assert handler.is_remote is True
        assert handler.remote_host == "example.com"

    def test_ansible_handler_remote_with_user(self, temp_dir):
        """Test AnsibleHandler with user@host format."""
        handler = AnsibleHandler(ansible_dir=temp_dir, remote_host="user@example.com")
        assert handler.remote_user == "user"
        assert handler.remote_host == "example.com"

    def test_ansible_handler_invalid_directory(self):
        """Test AnsibleHandler with invalid directory raises error."""
        with pytest.raises(ValueError, match="does not exist"):
            AnsibleHandler(ansible_dir="./non-existent-directory-12345")

    @patch("server_management.ansible.subprocess.run")
    def test_ansible_run_playbook(self, mock_subprocess, temp_dir):
        """Test running Ansible playbook."""
        mock_subprocess.return_value = MagicMock(returncode=0, stdout="", stderr="")
        handler = AnsibleHandler(ansible_dir=temp_dir)
        # Create a dummy playbook file
        playbook_file = Path(temp_dir) / "test.yml"
        playbook_file.write_text("---\n- hosts: all\n  tasks: []")
        result = handler.run_playbook("test.yml")
        assert result is not None
        assert result.returncode == 0
        mock_subprocess.assert_called()

    @patch("server_management.ansible.subprocess.run")
    def test_ansible_run_playbook_with_vars(self, mock_subprocess, temp_dir):
        """Test running Ansible playbook with extra vars."""
        mock_subprocess.return_value = MagicMock(returncode=0)
        handler = AnsibleHandler(ansible_dir=temp_dir)
        playbook_file = Path(temp_dir) / "test.yml"
        playbook_file.write_text("---\n- hosts: all\n  tasks: []")
        result = handler.run_playbook("test.yml", extra_vars={"var1": "value1"})
        assert result is not None
        mock_subprocess.assert_called()

    @patch("server_management.ansible.subprocess.run")
    def test_ansible_run_playbook_with_tags(self, mock_subprocess, temp_dir):
        """Test running Ansible playbook with tags."""
        mock_subprocess.return_value = MagicMock(returncode=0)
        handler = AnsibleHandler(ansible_dir=temp_dir)
        playbook_file = Path(temp_dir) / "test.yml"
        playbook_file.write_text("---\n- hosts: all\n  tasks: []")
        result = handler.run_playbook("test.yml", tags=["deploy", "config"])
        assert result is not None
        mock_subprocess.assert_called()

    @patch("server_management.ansible.subprocess.run")
    def test_ansible_install_collections(self, mock_subprocess, temp_dir):
        """Test installing Ansible collections."""
        mock_subprocess.return_value = MagicMock(returncode=0)
        handler = AnsibleHandler(ansible_dir=temp_dir)
        result = handler.install_collections(collections=["community.general"])
        assert result is not None
        assert result.returncode == 0
        mock_subprocess.assert_called()

    @patch("server_management.ansible.subprocess.run")
    def test_ansible_ad_hoc(self, mock_subprocess, temp_dir):
        """Test running Ansible ad-hoc command."""
        mock_subprocess.return_value = MagicMock(returncode=0, stdout="pong", stderr="")
        handler = AnsibleHandler(ansible_dir=temp_dir)
        result = handler.ad_hoc("ping", "", "all")
        assert result is not None
        assert result.returncode == 0
        mock_subprocess.assert_called()

    @patch("server_management.ansible.subprocess.run")
    def test_ansible_ping(self, mock_subprocess, temp_dir):
        """Test Ansible ping."""
        mock_subprocess.return_value = MagicMock(returncode=0, stdout="pong", stderr="")
        handler = AnsibleHandler(ansible_dir=temp_dir)
        result = handler.ping("all")
        assert result is True
        mock_subprocess.assert_called()

    @patch("server_management.ansible.subprocess.run")
    def test_ansible_ping_failure(self, mock_subprocess, temp_dir):
        """Test Ansible ping failure."""
        mock_subprocess.return_value = MagicMock(returncode=1, stdout="", stderr="Error")
        handler = AnsibleHandler(ansible_dir=temp_dir)
        result = handler.ping("all")
        assert result is False

    @patch("server_management.ansible.subprocess.run")
    def test_ansible_list_playbooks(self, mock_subprocess, temp_dir):
        """Test listing Ansible playbooks."""
        handler = AnsibleHandler(ansible_dir=temp_dir)
        # Create some playbook files
        playbook1 = Path(temp_dir) / "playbook1.yml"
        playbook2 = Path(temp_dir) / "playbook2.yml"
        playbook1.write_text("---\n- hosts: all")
        playbook2.write_text("---\n- hosts: all")
        playbooks = handler.list_playbooks()
        assert isinstance(playbooks, list)
        assert len(playbooks) >= 2

    @patch("server_management.ansible.subprocess.run")
    def test_ansible_validate_playbook(self, mock_subprocess, temp_dir):
        """Test validating Ansible playbook."""
        mock_subprocess.return_value = MagicMock(returncode=0, stdout="Valid", stderr="")
        handler = AnsibleHandler(ansible_dir=temp_dir)
        playbook_file = Path(temp_dir) / "test.yml"
        playbook_file.write_text("---\n- hosts: all\n  tasks: []")
        is_valid, message = handler.validate_playbook("test.yml")
        assert is_valid is True
        assert "Valid" in message
        mock_subprocess.assert_called()

    @patch("server_management.ansible.subprocess.run")
    def test_ansible_validate_playbook_invalid(self, mock_subprocess, temp_dir):
        """Test validating invalid Ansible playbook."""
        mock_subprocess.return_value = MagicMock(returncode=1, stdout="", stderr="Syntax error")
        handler = AnsibleHandler(ansible_dir=temp_dir)
        playbook_file = Path(temp_dir) / "invalid.yml"
        playbook_file.write_text("invalid yaml: [")
        is_valid, message = handler.validate_playbook("invalid.yml")
        assert is_valid is False
        assert "error" in message.lower()

    @patch("server_management.ansible.subprocess.run")
    def test_ansible_get_inventory_hosts(self, mock_subprocess, temp_dir):
        """Test getting inventory hosts."""
        handler = AnsibleHandler(ansible_dir=temp_dir)
        # Create inventory file
        inventory_dir = Path(temp_dir) / "inventory"
        inventory_dir.mkdir()
        inventory_file = inventory_dir / "hosts.yml"
        inventory_file.write_text("all:\n  hosts:\n    host1:\n    host2:")
        hosts = handler.get_inventory_hosts()
        assert isinstance(hosts, dict)

    @patch("server_management.ansible.subprocess.run")
    def test_ansible_command_timeout(self, mock_subprocess, temp_dir):
        """Test Ansible command with timeout."""
        import subprocess

        mock_subprocess.side_effect = subprocess.TimeoutExpired("ansible-playbook", 30)
        handler = AnsibleHandler(ansible_dir=temp_dir)
        playbook_file = Path(temp_dir) / "test.yml"
        playbook_file.write_text("---\n- hosts: all\n  tasks: []")
        with pytest.raises(TimeoutError):
            handler.run_playbook("test.yml", timeout=30)

    @patch("server_management.ansible.subprocess.run")
    def test_ansible_command_error(self, mock_subprocess, temp_dir):
        """Test Ansible command with error."""
        mock_subprocess.side_effect = FileNotFoundError()
        handler = AnsibleHandler(ansible_dir=temp_dir)
        playbook_file = Path(temp_dir) / "test.yml"
        playbook_file.write_text("---\n- hosts: all\n  tasks: []")
        with pytest.raises(ValueError, match="is not installed"):
            handler.run_playbook("test.yml")
