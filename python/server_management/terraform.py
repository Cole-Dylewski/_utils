"""
Terraform Project Manager

Provides a class-based interface for managing Terraform projects with support for:
- Local and remote execution
- Init, plan, apply, destroy operations
- Output parsing and retrieval
- Error handling and validation
"""

import json
import logging
import os
from pathlib import Path
import subprocess
from typing import Any

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class TerraformHandler:
    """
    Handles Terraform operations: init, plan, apply, destroy, and output retrieval.
    Supports both local and remote execution via SSH.
    """

    def __init__(
        self,
        project_dir: str,
        remote_host: str | None = None,
        remote_user: str | None = None,
        remote_project_dir: str | None = None,
        kubeconfig_path: str | None = None,
        auto_approve: bool = True,
        terraform_binary: str = "terraform",
        ssh_key_path: str | None = None,
        ssh_port: int = 22,
    ):
        """
        Initialize Terraform handler.

        :param project_dir: Local path to Terraform project directory
        :param remote_host: Remote host for SSH execution (e.g., 'server.example.com' or 'user@host')
        :param remote_user: SSH user (if not included in remote_host)
        :param remote_project_dir: Remote path to Terraform project directory
        :param kubeconfig_path: Path to kubeconfig file (for Kubernetes provider)
        :param auto_approve: Automatically approve apply/destroy operations
        :param terraform_binary: Path to terraform binary (default: 'terraform')
        :param ssh_key_path: Path to SSH private key for remote connections
        :param ssh_port: SSH port (default: 22)

        Example usage:
            # Local execution
            handler = TerraformHandler(project_dir="./terraform/my-project")

            # Remote execution
            handler = TerraformHandler(
                project_dir="./terraform/my-project",
                remote_host="server.example.com",
                remote_user="myuser",
                remote_project_dir="/remote/path/to/terraform",
                kubeconfig_path="/etc/kubernetes/admin.conf",
                ssh_key_path="~/.ssh/id_rsa"
            )
        """
        self.project_dir = Path(project_dir).resolve()
        if not self.project_dir.exists():
            raise ValueError(f"Terraform project directory does not exist: {project_dir}")

        self.remote_host = remote_host
        self.remote_user = remote_user
        self.remote_project_dir = remote_project_dir or str(self.project_dir)
        self.kubeconfig_path = kubeconfig_path
        self.auto_approve = auto_approve
        self.terraform_binary = terraform_binary
        self.ssh_key_path = ssh_key_path
        self.ssh_port = ssh_port

        # Determine if we're running locally or remotely
        self.is_remote = remote_host is not None

        # Parse remote_host if it includes user
        if self.is_remote and "@" in remote_host:
            self.remote_user, self.remote_host = remote_host.split("@", 1)

        logger.info(
            f"TerraformHandler initialized: project_dir={self.project_dir}, remote={self.is_remote}"
        )

    def _run_command(
        self,
        cmd: list[str],
        cwd: Path | None = None,
        check: bool = True,
        capture_output: bool = False,
        env: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess:
        """
        Run a command locally or remotely via SSH.

        :param cmd: Command to run as list of strings
        :param cwd: Working directory (local path for local, remote path for remote)
        :param check: Raise exception on non-zero exit code
        :param capture_output: Capture stdout/stderr
        :param env: Environment variables to set
        :return: CompletedProcess result
        """
        if self.is_remote:
            return self._run_remote_command(cmd, cwd, check, capture_output, env)
        return self._run_local_command(cmd, cwd, check, capture_output, env)

    def _run_local_command(
        self,
        cmd: list[str],
        cwd: Path | None = None,
        check: bool = True,
        capture_output: bool = False,
        env: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess:
        """Run command locally."""
        working_dir = cwd or self.project_dir

        # Prepare environment
        subprocess_env = os.environ.copy()
        if env:
            subprocess_env.update(env)
        if self.kubeconfig_path:
            subprocess_env["KUBECONFIG"] = self.kubeconfig_path

        try:
            return subprocess.run(
                cmd,
                cwd=working_dir,
                check=check,
                capture_output=capture_output,
                text=True,
                encoding="utf-8",
                errors="replace",
                env=subprocess_env,
            )
        except subprocess.CalledProcessError as e:
            logger.exception(f"Command failed: {' '.join(cmd)}")
            if e.stdout:
                logger.exception(f"stdout: {e.stdout}")
            if e.stderr:
                logger.exception(f"stderr: {e.stderr}")
            raise
        except FileNotFoundError:
            logger.exception(f"Command not found: {cmd[0]}")
            raise ValueError(f"{cmd[0]} is not installed or not in PATH")

    def _run_remote_command(
        self,
        cmd: list[str],
        cwd: Path | None = None,
        check: bool = True,
        capture_output: bool = False,
        env: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess:
        """Run command on remote server via SSH."""
        working_dir = cwd or self.remote_project_dir

        # Build environment variable exports
        env_exports = []
        if env:
            for key, value in env.items():
                env_exports.append(f"export {key}='{value}'")
        if self.kubeconfig_path:
            env_exports.append(f"export KUBECONFIG='{self.kubeconfig_path}'")
            # Ensure kubeconfig is readable
            env_exports.append(f"sudo chmod 644 {self.kubeconfig_path} 2>/dev/null || true")

        # Build full command
        env_prefix = " && ".join(env_exports) + " && " if env_exports else ""
        full_cmd = f"cd {working_dir} && {env_prefix}{' '.join(cmd)}"

        # Build SSH command
        ssh_target = (
            f"{self.remote_user}@{self.remote_host}" if self.remote_user else self.remote_host
        )
        ssh_cmd = ["ssh"]

        # Add SSH options
        ssh_cmd.extend(["-o", "StrictHostKeyChecking=no"])
        ssh_cmd.extend(["-o", "ConnectTimeout=10"])
        ssh_cmd.extend(["-o", "BatchMode=yes"])
        ssh_cmd.extend(["-p", str(self.ssh_port)])

        # Add SSH key if provided
        if self.ssh_key_path:
            ssh_cmd.extend(["-i", self.ssh_key_path])

        # Use -t (single TTY) for interactive commands, no TTY for non-interactive
        # terraform validate/plan/apply are non-interactive when using -auto-approve
        # Only use TTY for commands that might need it
        needs_tty = not capture_output and self.terraform_binary in cmd and "validate" not in cmd
        if needs_tty:
            ssh_cmd.append("-t")

        ssh_cmd.append(ssh_target)
        ssh_cmd.append(full_cmd)

        try:
            return subprocess.run(
                ssh_cmd,
                check=check,
                capture_output=capture_output,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=300,  # 5 minute timeout
            )
        except subprocess.TimeoutExpired:
            logger.exception(f"Remote command timed out: {' '.join(cmd)}")
            raise
        except subprocess.CalledProcessError as e:
            logger.exception(f"Remote command failed: {' '.join(cmd)}")
            if e.stdout:
                logger.exception(f"stdout: {e.stdout}")
            if e.stderr:
                logger.exception(f"stderr: {e.stderr}")
            raise
        except FileNotFoundError:
            logger.exception("SSH command not found")
            raise ValueError("SSH is not installed or not in PATH")

    def init(
        self,
        upgrade: bool = False,
        backend_config: dict[str, str] | None = None,
        reconfigure: bool = False,
        check: bool = True,
    ) -> subprocess.CompletedProcess:
        """
        Initialize Terraform project.

        :param upgrade: Upgrade modules and plugins
        :param backend_config: Backend configuration variables
        :param reconfigure: Reconfigure backend
        :param check: Raise exception on non-zero exit code (default: True)
        :return: CompletedProcess result
        """
        logger.info("Initializing Terraform project...")

        cmd = [self.terraform_binary, "init"]

        if upgrade:
            cmd.append("-upgrade")
        if reconfigure:
            cmd.append("-reconfigure")

        if backend_config:
            for key, value in backend_config.items():
                cmd.extend(["-backend-config", f"{key}={value}"])

        # Capture output if check=False so we can inspect errors
        capture_output = not check
        result = self._run_command(cmd, check=check, capture_output=capture_output)
        if result.returncode == 0:
            logger.info("Terraform initialization complete")
        else:
            logger.warning(f"Terraform initialization completed with exit code {result.returncode}")
        return result

    def plan(
        self,
        var_file: str | None = None,
        vars: dict[str, Any] | None = None,
        targets: list[str] | None = None,
        out: str | None = None,
        detailed_exitcode: bool = False,
        check_crd_errors: bool = True,
    ) -> tuple[subprocess.CompletedProcess, bool]:
        """
        Run Terraform plan.

        :param var_file: Path to variables file
        :param vars: Dictionary of variables to pass
        :param targets: List of target resources
        :param out: Path to save plan file
        :param detailed_exitcode: Return detailed exit code (0=success, 1=error, 2=changes)
        :param check_crd_errors: Check for CRD-related errors (Kubernetes)
        :return: Tuple of (CompletedProcess, is_crd_error)
        """
        logger.info("Running Terraform plan...")

        cmd = [self.terraform_binary, "plan"]

        # Add -lock=false if lock file validation is causing issues
        # This can be set via environment or instance variable if needed

        if var_file:
            cmd.extend(["-var-file", var_file])

        if vars:
            for key, value in vars.items():
                if isinstance(value, (dict, list)):
                    value = json.dumps(value)
                cmd.extend(["-var", f"{key}={value}"])

        if targets:
            for target in targets:
                cmd.extend(["-target", target])

        if out:
            cmd.extend(["-out", out])

        if detailed_exitcode:
            cmd.append("-detailed-exitcode")

        # Run plan
        result = self._run_command(cmd, check=False, capture_output=False)

        # Check for CRD errors if requested
        is_crd_error = False
        if check_crd_errors and result.returncode != 0:
            logger.info("Checking for CRD-related errors...")
            check_result = self._run_command(
                [self.terraform_binary, "plan"] + (["-var-file", var_file] if var_file else []),
                check=False,
                capture_output=True,
            )
            output = (check_result.stdout or "") + (check_result.stderr or "")
            is_crd_error = (
                "CRD may not be installed" in output
                or "no matches for kind" in output.lower()
                or "GroupVersionKind" in output
                or ("external-secrets.io" in output.lower() and "SecretStore" in output)
            )

        if result.returncode == 0:
            logger.info("Terraform plan completed successfully")
        elif is_crd_error:
            logger.warning(
                "Terraform plan detected CRD-related errors (expected in some environments)"
            )
        else:
            logger.warning(f"Terraform plan completed with exit code {result.returncode}")

        return result, is_crd_error

    def apply(
        self,
        plan_file: str | None = None,
        var_file: str | None = None,
        vars: dict[str, Any] | None = None,
        targets: list[str] | None = None,
        auto_approve: bool | None = None,
    ) -> subprocess.CompletedProcess:
        """
        Apply Terraform changes.

        :param plan_file: Path to plan file (from terraform plan -out)
        :param var_file: Path to variables file
        :param vars: Dictionary of variables to pass
        :param targets: List of target resources
        :param auto_approve: Override instance auto_approve setting
        :return: CompletedProcess result
        """
        logger.info("Applying Terraform changes...")

        cmd = [self.terraform_binary, "apply"]

        if plan_file:
            cmd.append(plan_file)
        else:
            if auto_approve is None:
                auto_approve = self.auto_approve
            if auto_approve:
                cmd.append("-auto-approve")

            if var_file:
                cmd.extend(["-var-file", var_file])

            if vars:
                for key, value in vars.items():
                    if isinstance(value, (dict, list)):
                        value = json.dumps(value)
                    cmd.extend(["-var", f"{key}={value}"])

            if targets:
                for target in targets:
                    cmd.extend(["-target", target])

        result = self._run_command(cmd, check=True)
        logger.info("Terraform apply completed")
        return result

    def destroy(
        self,
        var_file: str | None = None,
        vars: dict[str, Any] | None = None,
        targets: list[str] | None = None,
        auto_approve: bool | None = None,
        force: bool = False,
    ) -> subprocess.CompletedProcess:
        """
        Destroy Terraform resources.

        :param var_file: Path to variables file
        :param vars: Dictionary of variables to pass
        :param targets: List of target resources
        :param auto_approve: Override instance auto_approve setting
        :param force: Skip confirmation prompt (requires auto_approve=True)
        :return: CompletedProcess result
        """
        logger.warning("Destroying Terraform resources...")

        if auto_approve is None:
            auto_approve = self.auto_approve

        if not force and not auto_approve:
            raise ValueError("destroy requires auto_approve=True or force=True")

        cmd = [self.terraform_binary, "destroy"]

        if auto_approve:
            cmd.append("-auto-approve")

        if var_file:
            cmd.extend(["-var-file", var_file])

        if vars:
            for key, value in vars.items():
                if isinstance(value, (dict, list)):
                    value = json.dumps(value)
                cmd.extend(["-var", f"{key}={value}"])

        if targets:
            for target in targets:
                cmd.extend(["-target", target])

        result = self._run_command(cmd, check=True)
        logger.info("Terraform destroy completed")
        return result

    def output(self, name: str | None = None, json_format: bool = True) -> dict[str, Any]:
        """
        Get Terraform outputs.

        :param name: Specific output name (returns all if None)
        :param json_format: Return JSON format
        :return: Dictionary of outputs
        """
        logger.info("Retrieving Terraform outputs...")

        cmd = [self.terraform_binary, "output"]

        if json_format:
            cmd.append("-json")

        if name:
            cmd.append(name)

        result = self._run_command(cmd, check=False, capture_output=True)

        if result.returncode != 0:
            logger.warning(f"Failed to retrieve outputs (exit code: {result.returncode})")
            if result.stderr:
                logger.warning(f"Error: {result.stderr}")
            return {}

        if json_format and result.stdout:
            try:
                outputs = json.loads(result.stdout)
                # Terraform output -json returns {name: {value: ..., sensitive: ...}}
                # Convert to simpler format
                if name:
                    # Single output requested
                    if isinstance(outputs, dict) and "value" in outputs:
                        return {name: outputs["value"]}
                    return {name: outputs}
                # All outputs
                simplified = {}
                for key, value in outputs.items():
                    if isinstance(value, dict) and "value" in value:
                        simplified[key] = value["value"]
                    else:
                        simplified[key] = value
                return simplified
            except json.JSONDecodeError:
                logger.warning("Failed to parse JSON output")
                return {}
        else:
            # Text format - parse manually
            outputs = {}
            for line in result.stdout.split("\n"):
                if "=" in line:
                    key, value = line.split("=", 1)
                    outputs[key.strip()] = value.strip()
            return outputs

    def validate(self) -> tuple[bool, str]:
        """
        Validate Terraform configuration.

        :return: Tuple of (is_valid, message)
        """
        logger.info("Validating Terraform configuration...")

        cmd = [self.terraform_binary, "validate"]
        result = self._run_command(cmd, check=False, capture_output=True)

        if result.returncode == 0:
            logger.info("Terraform configuration is valid")
            return True, result.stdout or "Configuration is valid"
        error_msg = result.stderr or result.stdout or "Validation failed"
        logger.error(f"Terraform validation failed: {error_msg}")
        return False, error_msg

    def fmt(self, check: bool = False, write: bool = True) -> subprocess.CompletedProcess:
        """
        Format Terraform files.

        :param check: Check if files are formatted (don't modify)
        :param write: Write formatted files (default: True)
        :return: CompletedProcess result
        """
        logger.info("Formatting Terraform files...")

        cmd = [self.terraform_binary, "fmt"]

        if check:
            cmd.append("-check")
        if not write:
            cmd.append("-write=false")

        result = self._run_command(cmd, check=False)
        logger.info("Terraform formatting complete")
        return result

    def state_list(self, addresses: list[str] | None = None) -> list[str]:
        """
        List resources in Terraform state.

        :param addresses: Filter by resource addresses
        :return: List of resource addresses
        """
        logger.info("Listing Terraform state resources...")

        cmd = [self.terraform_binary, "state", "list"]

        if addresses:
            cmd.extend(addresses)

        result = self._run_command(cmd, check=False, capture_output=True)

        if result.returncode == 0 and result.stdout:
            return [line.strip() for line in result.stdout.strip().split("\n") if line.strip()]
        return []

    def state_show(self, address: str) -> dict[str, Any]:
        """
        Show resource details from Terraform state.

        :param address: Resource address
        :return: Resource details as dictionary
        """
        logger.info(f"Showing Terraform state for: {address}")

        cmd = [self.terraform_binary, "state", "show", "-json", address]
        result = self._run_command(cmd, check=False, capture_output=True)

        if result.returncode == 0 and result.stdout:
            try:
                return json.loads(result.stdout)
            except json.JSONDecodeError:
                logger.warning("Failed to parse state JSON")
                return {}
        return {}

    def workspace_list(self) -> list[str]:
        """
        List Terraform workspaces.

        :return: List of workspace names
        """
        logger.info("Listing Terraform workspaces...")

        cmd = [self.terraform_binary, "workspace", "list"]
        result = self._run_command(cmd, check=False, capture_output=True)

        if result.returncode == 0 and result.stdout:
            workspaces = []
            for line in result.stdout.strip().split("\n"):
                line = line.strip()
                if line:
                    # Current workspace is marked with *
                    if line.startswith("*"):
                        line = line[1:].strip()
                    workspaces.append(line)
            return workspaces
        return []

    def workspace_select(self, name: str) -> subprocess.CompletedProcess:
        """
        Select Terraform workspace.

        :param name: Workspace name
        :return: CompletedProcess result
        """
        logger.info(f"Selecting Terraform workspace: {name}")

        cmd = [self.terraform_binary, "workspace", "select", name]
        result = self._run_command(cmd, check=True)
        logger.info(f"Workspace '{name}' selected")
        return result

    def workspace_new(self, name: str) -> subprocess.CompletedProcess:
        """
        Create new Terraform workspace.

        :param name: Workspace name
        :return: CompletedProcess result
        """
        logger.info(f"Creating Terraform workspace: {name}")

        cmd = [self.terraform_binary, "workspace", "new", name]
        result = self._run_command(cmd, check=True)
        logger.info(f"Workspace '{name}' created")
        return result

    def workspace_delete(self, name: str) -> subprocess.CompletedProcess:
        """
        Delete Terraform workspace.

        :param name: Workspace name
        :return: CompletedProcess result
        """
        logger.warning(f"Deleting Terraform workspace: {name}")

        cmd = [self.terraform_binary, "workspace", "delete", name]
        result = self._run_command(cmd, check=True)
        logger.info(f"Workspace '{name}' deleted")
        return result
