"""
Ansible Playbook Manager

Provides a class-based interface for managing Ansible playbooks with support for:
- Local and remote execution
- Playbook execution with inventory
- Collection management
- Variable passing and host limiting
- Error handling and timeout management
"""

import json
import logging
import subprocess
import time
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
import os

try:
    import yaml
except ImportError:
    yaml = None

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class AnsibleHandler:
    """
    Handles Ansible playbook operations: execution, collection management, and inventory handling.
    Supports both local and remote execution via SSH.
    """
    
    def __init__(
        self,
        ansible_dir: str,
        inventory: Optional[str] = None,
        remote_host: Optional[str] = None,
        remote_user: Optional[str] = None,
        remote_ansible_dir: Optional[str] = None,
        ansible_binary: str = 'ansible-playbook',
        ansible_cfg: Optional[str] = None
    ):
        """
        Initialize Ansible handler.
        
        :param ansible_dir: Local path to Ansible directory (contains playbooks, inventory, etc.)
        :param inventory: Path to inventory file (relative to ansible_dir or absolute)
        :param remote_host: Remote host for SSH execution (e.g., 'server.example.com' or 'user@host')
        :param remote_user: SSH user (if not included in remote_host)
        :param remote_ansible_dir: Remote path to Ansible directory
        :param ansible_binary: Path to ansible-playbook binary (default: 'ansible-playbook')
        :param ansible_cfg: Path to ansible.cfg file (optional)
        
        Example usage:
            # Local execution
            handler = AnsibleHandler(ansible_dir="./ansible")
            
            # Remote execution
            handler = AnsibleHandler(
                ansible_dir="./ansible",
                remote_host="server.example.com",
                remote_user="myuser",
                remote_ansible_dir="/remote/path/to/ansible"
            )
        """
        self.ansible_dir = Path(ansible_dir).resolve()
        if not self.ansible_dir.exists():
            raise ValueError(f"Ansible directory does not exist: {ansible_dir}")
        
        # Set inventory path
        if inventory:
            if Path(inventory).is_absolute():
                self.inventory = Path(inventory)
            else:
                self.inventory = self.ansible_dir / inventory
        else:
            # Default to inventory/hosts.yml
            self.inventory = self.ansible_dir / "inventory" / "hosts.yml"
        
        self.remote_host = remote_host
        self.remote_user = remote_user
        
        # Determine if we're running locally or remotely (must be set before using it)
        self.is_remote = remote_host is not None
        
        # For remote execution, use a standard remote path
        if self.is_remote:
            # Use a standard remote path like /opt/{app}/ansible or derive from app_repo_path
            self.remote_ansible_dir = remote_ansible_dir or f"/opt/ipsa/ansible"
        else:
            self.remote_ansible_dir = remote_ansible_dir or str(self.ansible_dir)
        self.ansible_binary = ansible_binary
        self.ansible_cfg = ansible_cfg
        
        # Parse remote_host if it includes user
        if self.is_remote and '@' in remote_host:
            self.remote_user, self.remote_host = remote_host.split('@', 1)
        
        logger.info(f"AnsibleHandler initialized: ansible_dir={self.ansible_dir}, remote={self.is_remote}")
    
    def _run_command(
        self,
        cmd: List[str],
        cwd: Optional[Path] = None,
        check: bool = True,
        capture_output: bool = False,
        env: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None
    ) -> subprocess.CompletedProcess:
        """
        Run a command locally or remotely via SSH.
        
        :param cmd: Command to run as list of strings
        :param cwd: Working directory (local path for local, remote path for remote)
        :param check: Raise exception on non-zero exit code
        :param capture_output: Capture stdout/stderr
        :param env: Environment variables to set
        :param timeout: Command timeout in seconds
        :return: CompletedProcess result
        """
        if self.is_remote:
            return self._run_remote_command(cmd, cwd, check, capture_output, env, timeout)
        else:
            return self._run_local_command(cmd, cwd, check, capture_output, env, timeout)
    
    def _run_local_command(
        self,
        cmd: List[str],
        cwd: Optional[Path] = None,
        check: bool = True,
        capture_output: bool = False,
        env: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None
    ) -> subprocess.CompletedProcess:
        """Run command locally."""
        working_dir = cwd or self.ansible_dir
        
        # Prepare environment
        subprocess_env = os.environ.copy()
        if env:
            subprocess_env.update(env)
        if self.ansible_cfg:
            subprocess_env['ANSIBLE_CONFIG'] = str(self.ansible_cfg)
        
        try:
            result = subprocess.run(
                cmd,
                cwd=working_dir,
                check=check,
                capture_output=capture_output,
                text=True,
                encoding='utf-8',
                errors='replace',
                env=subprocess_env,
                timeout=timeout
            )
            return result
        except subprocess.TimeoutExpired:
            logger.error(f"Command timed out after {timeout}s: {' '.join(cmd)}")
            raise TimeoutError(f"Command exceeded {timeout}s timeout")
        except subprocess.CalledProcessError as e:
            logger.error(f"Command failed: {' '.join(cmd)}")
            if e.stdout:
                logger.error(f"stdout: {e.stdout}")
            if e.stderr:
                logger.error(f"stderr: {e.stderr}")
            raise
        except FileNotFoundError:
            logger.error(f"Command not found: {cmd[0]}")
            raise ValueError(f"{cmd[0]} is not installed or not in PATH")
    
    def _run_remote_command(
        self,
        cmd: List[str],
        cwd: Optional[Path] = None,
        check: bool = True,
        capture_output: bool = False,
        env: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None
    ) -> subprocess.CompletedProcess:
        """Run command on remote server via SSH."""
        # Convert Path to string and ensure it's a Unix path (not Windows)
        if cwd:
            if isinstance(cwd, Path):
                working_dir = str(cwd).replace('\\', '/')
            else:
                working_dir = str(cwd).replace('\\', '/')
        else:
            working_dir = str(self.remote_ansible_dir).replace('\\', '/')
        
        # Build environment variable exports
        env_exports = []
        if env:
            for key, value in env.items():
                env_exports.append(f"export {key}='{value}'")
        if self.ansible_cfg:
            env_exports.append(f"export ANSIBLE_CONFIG='{self.ansible_cfg}'")
        
        # Build full command with optional timeout
        env_prefix = " && ".join(env_exports) + " && " if env_exports else ""
        cmd_str = ' '.join(cmd)
        
        if timeout:
            full_cmd = f"cd {working_dir} && {env_prefix}timeout {timeout} {cmd_str}"
        else:
            full_cmd = f"cd {working_dir} && {env_prefix}{cmd_str}"
        
        # Build SSH command
        ssh_target = f"{self.remote_user}@{self.remote_host}" if self.remote_user else self.remote_host
        # Use -t instead of -tt for non-interactive commands to avoid hanging
        # Only use -tt if we need a TTY (which we don't for most commands)
        ssh_cmd = ['ssh', '-t', '-o', 'StrictHostKeyChecking=no', '-o', 'BatchMode=yes', ssh_target, full_cmd]
        
        try:
            result = subprocess.run(
                ssh_cmd,
                check=check,
                capture_output=capture_output,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=timeout if timeout else None
            )
            
            # Check for timeout exit code (124)
            if result.returncode == 124:
                logger.error(f"Remote command timed out after {timeout}s")
                raise TimeoutError(f"Command exceeded {timeout}s timeout")
            
            return result
        except subprocess.CalledProcessError as e:
            logger.error(f"Remote command failed: {' '.join(cmd)}")
            if e.stdout:
                logger.error(f"stdout: {e.stdout}")
            if e.stderr:
                logger.error(f"stderr: {e.stderr}")
            raise
        except FileNotFoundError:
            logger.error("SSH command not found")
            raise ValueError("SSH is not installed or not in PATH")
    
    def install_collections(
        self,
        requirements_file: Optional[str] = None,
        collections: Optional[List[str]] = None
    ) -> subprocess.CompletedProcess:
        """
        Install Ansible collections.
        
        :param requirements_file: Path to requirements.yml file (relative to ansible_dir or absolute)
        :param collections: List of collection names to install (e.g., ['community.general'])
        :return: CompletedProcess result
        """
        logger.info("Installing Ansible collections...")
        
        cmd = ['ansible-galaxy', 'collection', 'install']
        
        if requirements_file:
            if Path(requirements_file).is_absolute():
                req_path = Path(requirements_file)
            else:
                req_path = self.ansible_dir / requirements_file
            
            if not req_path.exists():
                raise ValueError(f"Requirements file does not exist: {requirements_file}")
            
            cmd.extend(['-r', str(req_path)])
        elif collections:
            cmd.extend(collections)
        else:
            # Default to requirements.yml
            if self.is_remote:
                # Use remote path for remote execution
                default_req = f"{self.remote_ansible_dir}/requirements.yml"
            else:
                default_req = self.ansible_dir / "requirements.yml"
                if not default_req.exists():
                    raise ValueError("No requirements file or collections specified, and requirements.yml not found")
                default_req = str(default_req)
            
            cmd.extend(['-r', default_req])
        
        # For remote execution, set working directory to remote ansible dir
        if self.is_remote:
            # Use string path for remote (not Path object which might convert to Windows format)
            cwd = self.remote_ansible_dir
        else:
            cwd = self.ansible_dir
        result = self._run_command(cmd, cwd=cwd, check=True)
        logger.info("Ansible collections installed")
        return result
    
    def run_playbook(
        self,
        playbook: str,
        inventory: Optional[str] = None,
        extra_vars: Optional[Dict[str, Any]] = None,
        limit: Optional[str] = None,
        tags: Optional[List[str]] = None,
        skip_tags: Optional[List[str]] = None,
        check_mode: bool = False,
        diff: bool = False,
        timeout: Optional[int] = None,
        verbose: bool = False
    ) -> subprocess.CompletedProcess:
        """
        Run an Ansible playbook.
        
        :param playbook: Playbook name (without .yml) or path to playbook file
        :param inventory: Inventory file path (overrides default)
        :param extra_vars: Dictionary of extra variables to pass
        :param limit: Limit execution to specific hosts/groups
        :param tags: List of tags to run
        :param skip_tags: List of tags to skip
        :param check_mode: Run in check mode (dry-run)
        :param diff: Show differences when files are changed
        :param timeout: Command timeout in seconds
        :param verbose: Enable verbose output (-v)
        :return: CompletedProcess result
        """
        logger.info(f"Running Ansible playbook: {playbook}")
        
        # Resolve playbook path
        if playbook.endswith('.yml') or playbook.endswith('.yaml'):
            playbook_path = playbook
        else:
            # Try to find playbook in common locations
            possible_paths = [
                self.ansible_dir / "playbooks" / f"{playbook}.yml",
                self.ansible_dir / "deployments" / f"{playbook}.yml",
                self.ansible_dir / f"{playbook}.yml"
            ]
            
            playbook_path = None
            for path in possible_paths:
                if path.exists():
                    playbook_path = path  # Keep as Path object for now
                    break
            
            if not playbook_path:
                # If not found locally, use as-is (might be remote path)
                playbook_path = playbook
        
        # Build command
        cmd = [self.ansible_binary]
        
        # Inventory
        inv_path = inventory or str(self.inventory)
        if self.is_remote:
            # For remote execution, check if inventory path is already a remote path
            if inv_path.startswith(self.remote_ansible_dir):
                # Already a remote path, use as-is
                pass
            elif not Path(inv_path).is_absolute():
                # Relative path, prepend remote ansible_dir
                normalized_path = inv_path.replace('\\', '/')
                inv_path = f"{self.remote_ansible_dir}/{normalized_path}"
            elif str(self.ansible_dir) in inv_path:
                # Convert local absolute path to remote path
                try:
                    rel_path = Path(inv_path).relative_to(self.ansible_dir)
                    rel_path_str = str(rel_path).replace('\\', '/')
                    inv_path = f"{self.remote_ansible_dir}/{rel_path_str}"
                except ValueError:
                    pass
            # If it's already an absolute path that doesn't contain ansible_dir, use as-is
        cmd.extend(['-i', inv_path])
        
        # Playbook path - convert to remote path if needed
        if self.is_remote:
            if isinstance(playbook_path, Path):
                # Convert Path object to relative path, then to remote Unix path
                try:
                    rel_path = playbook_path.relative_to(self.ansible_dir)
                    rel_path_str = str(rel_path).replace('\\', '/')
                    playbook_path = f"{self.remote_ansible_dir}/{rel_path_str}"
                except ValueError:
                    # Not relative to ansible_dir, use playbook name
                    playbook_path = f"{self.remote_ansible_dir}/playbooks/{playbook_path.name}"
            elif isinstance(playbook_path, str):
                # String path - check if it's a Windows absolute path
                if Path(playbook_path).is_absolute() and '\\' in playbook_path:
                    # Windows absolute path, convert to remote path
                    try:
                        rel_path = Path(playbook_path).relative_to(self.ansible_dir)
                        rel_path_str = str(rel_path).replace('\\', '/')
                        playbook_path = f"{self.remote_ansible_dir}/{rel_path_str}"
                    except ValueError:
                        # Not relative, use playbook name
                        playbook_name = Path(playbook_path).name
                        playbook_path = f"{self.remote_ansible_dir}/playbooks/{playbook_name}"
            elif not Path(playbook_path).is_absolute():
                # Relative path, prepend remote ansible_dir
                    playbook_path = f"{self.remote_ansible_dir}/{playbook_path.replace('\\', '/')}"
        else:
            # Local execution - convert Path to string
            if isinstance(playbook_path, Path):
                playbook_path = str(playbook_path)
        
        cmd.append(playbook_path)
        
        # Extra variables
        if extra_vars:
            # Convert dict to JSON string for -e
            # For remote execution, we need to properly quote the JSON
            extra_vars_str = json.dumps(extra_vars)
            if self.is_remote:
                # For remote execution, use single quotes to prevent shell interpretation
                # and escape any single quotes in the JSON
                escaped_json = extra_vars_str.replace("'", "'\"'\"'")
                cmd.extend(['-e', f"'{escaped_json}'"])
            else:
                cmd.extend(['-e', extra_vars_str])
        
        # Limit
        if limit:
            cmd.extend(['--limit', limit])
        
        # Tags
        if tags:
            cmd.extend(['--tags', ','.join(tags)])
        
        # Skip tags
        if skip_tags:
            cmd.extend(['--skip-tags', ','.join(skip_tags)])
        
        # Check mode
        if check_mode:
            cmd.append('--check')
        
        # Diff
        if diff:
            cmd.append('--diff')
        
        # Verbose
        if verbose:
            cmd.append('-v')
        
        # Run playbook
        result = self._run_command(cmd, check=False, capture_output=False, timeout=timeout)
        
        if result.returncode == 0:
            logger.info(f"Playbook '{playbook}' completed successfully")
        else:
            logger.error(f"Playbook '{playbook}' failed with exit code {result.returncode}")
        
        return result
    
    def ad_hoc(
        self,
        module: str,
        args: str,
        hosts: str,
        inventory: Optional[str] = None,
        extra_vars: Optional[Dict[str, Any]] = None,
        become: bool = False,
        become_user: Optional[str] = None,
        check_mode: bool = False,
        verbose: bool = False
    ) -> subprocess.CompletedProcess:
        """
        Run an Ansible ad-hoc command.
        
        :param module: Ansible module name (e.g., 'ping', 'shell', 'command')
        :param args: Module arguments
        :param hosts: Target hosts/group
        :param inventory: Inventory file path (overrides default)
        :param extra_vars: Dictionary of extra variables
        :param become: Use privilege escalation
        :param become_user: User to become (requires become=True)
        :param check_mode: Run in check mode
        :param verbose: Enable verbose output
        :return: CompletedProcess result
        """
        logger.info(f"Running Ansible ad-hoc: {module} on {hosts}")
        
        cmd = ['ansible', hosts]
        
        # Inventory
        if inventory:
            inv_path = inventory
        else:
            inv_path = str(self.inventory)
        
        if self.is_remote:
            # For remote execution, convert inventory path
            if Path(inv_path).is_absolute() and str(self.ansible_dir) in inv_path:
                # Convert absolute local path to remote path
                try:
                    rel_path = Path(inv_path).relative_to(self.ansible_dir)
                    rel_path_str = str(rel_path).replace('\\', '/')
                    inv_path = f"{self.remote_ansible_dir}/{rel_path_str}"
                except ValueError:
                    # Fallback: use inventory name
                    inv_path = f"{self.remote_ansible_dir}/inventory/hosts.yml"
            elif not Path(inv_path).is_absolute():
                # Relative path, prepend remote ansible_dir
                normalized_path = inv_path.replace('\\', '/')
                inv_path = f"{self.remote_ansible_dir}/{normalized_path}"
            else:
                # Absolute path that's not under ansible_dir, use as-is
                pass
        
        cmd.extend(['-i', inv_path])
        
        # Module and args
        cmd.extend(['-m', module, '-a', args])
        
        # Extra variables
        if extra_vars:
            extra_vars_str = json.dumps(extra_vars)
            cmd.extend(['-e', extra_vars_str])
        
        # Become
        if become:
            cmd.append('--become')
            if become_user:
                cmd.extend(['--become-user', become_user])
        
        # Check mode
        if check_mode:
            cmd.append('--check')
        
        # Verbose
        if verbose:
            cmd.append('-v')
        
        result = self._run_command(cmd, check=False, capture_output=True)
        
        if result.returncode == 0:
            logger.info(f"Ad-hoc command completed successfully")
        else:
            logger.error(f"Ad-hoc command failed with exit code {result.returncode}")
        
        return result
    
    def ping(
        self,
        hosts: str,
        inventory: Optional[str] = None
    ) -> bool:
        """
        Test connectivity to hosts using Ansible ping module.
        
        :param hosts: Target hosts/group
        :param inventory: Inventory file path (overrides default)
        :return: True if all hosts are reachable, False otherwise
        """
        logger.info(f"Testing connectivity to hosts: {hosts}")
        
        result = self.ad_hoc('ping', '', hosts, inventory=inventory)
        return result.returncode == 0
    
    def get_inventory_hosts(
        self,
        inventory: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Parse and return inventory structure.
        
        :param inventory: Inventory file path (overrides default)
        :return: Dictionary representation of inventory
        """
        inv_path = inventory or self.inventory
        
        if self.is_remote:
            # For remote, we'd need to fetch the file first
            # For now, assume we can access it via remote path
            if not Path(inv_path).is_absolute():
                inv_path = f"{self.remote_ansible_dir}/{inv_path}"
            logger.warning("Remote inventory parsing not fully supported - use local inventory file")
            return {}
        
        if not Path(inv_path).exists():
            logger.warning(f"Inventory file not found: {inv_path}")
            return {}
        
        if yaml is None:
            logger.warning("PyYAML not installed - cannot parse inventory file")
            return {}
        
        try:
            with open(inv_path, 'r', encoding='utf-8') as f:
                inventory_data = yaml.safe_load(f)
            return inventory_data or {}
        except Exception as e:
            logger.error(f"Failed to parse inventory: {e}")
            return {}
    
    def list_playbooks(
        self,
        directory: Optional[str] = None
    ) -> List[str]:
        """
        List available playbooks in the Ansible directory.
        
        :param directory: Directory to search (relative to ansible_dir)
        :return: List of playbook names (without .yml extension)
        """
        search_dir = self.ansible_dir
        if directory:
            search_dir = self.ansible_dir / directory
        
        if not search_dir.exists():
            logger.warning(f"Directory not found: {search_dir}")
            return []
        
        playbooks = []
        for path in search_dir.rglob('*.yml'):
            if path.is_file():
                # Get relative path from ansible_dir
                rel_path = path.relative_to(self.ansible_dir)
                # Remove .yml extension
                playbook_name = str(rel_path).replace('.yml', '').replace('.yaml', '')
                playbooks.append(playbook_name)
        
        return sorted(playbooks)
    
    def validate_playbook(
        self,
        playbook: str
    ) -> Tuple[bool, str]:
        """
        Validate Ansible playbook syntax.
        
        :param playbook: Playbook path or name
        :return: Tuple of (is_valid, message)
        """
        logger.info(f"Validating playbook: {playbook}")
        
        # Resolve playbook path (similar to run_playbook)
        if playbook.endswith('.yml') or playbook.endswith('.yaml'):
            playbook_path = playbook
        else:
            possible_paths = [
                self.ansible_dir / "playbooks" / f"{playbook}.yml",
                self.ansible_dir / "deployments" / f"{playbook}.yml",
                self.ansible_dir / f"{playbook}.yml"
            ]
            
            playbook_path = None
            for path in possible_paths:
                if path.exists():
                    playbook_path = str(path)
                    break
            
            if not playbook_path:
                return False, f"Playbook not found: {playbook}"
        
        # Use ansible-playbook --syntax-check
        cmd = [self.ansible_binary, '--syntax-check', playbook_path]
        
        result = self._run_command(cmd, check=False, capture_output=True)
        
        if result.returncode == 0:
            logger.info("Playbook syntax is valid")
            return True, result.stdout or "Playbook syntax is valid"
        else:
            error_msg = result.stderr or result.stdout or "Validation failed"
            logger.error(f"Playbook validation failed: {error_msg}")
            return False, error_msg

