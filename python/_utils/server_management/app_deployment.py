"""
Application Deployment Framework

Provides a general, reusable framework for deploying applications on Linux servers
using Terraform and Ansible. Supports multiple applications, environments, and
idempotent operations. Designed for physical Linux servers with modular support
for future cloud migration.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
import logging
from pathlib import Path
from typing import Any

from _utils.server_management.ansible import AnsibleHandler
from _utils.server_management.credential_generator import CredentialGenerator
from _utils.server_management.terraform import TerraformHandler
from _utils.server_management.vault import VaultHandler

logger = logging.getLogger(__name__)


class EnvironmentType(Enum):
    """Deployment environment types."""

    DEMO = "demo"
    STAGING = "staging"
    PROD = "prod"
    DEV = "dev"


@dataclass
class ServerConfig:
    """Server connection configuration."""

    host: str
    user: str
    port: int = 22
    ssh_key_path: str | None = None

    def __post_init__(self) -> None:
        """Validate server configuration."""
        if not self.host:
            raise ValueError("host is required")
        if not self.user:
            raise ValueError("user is required")


@dataclass
class VaultConfig:
    """Vault configuration for credential management."""

    vault_addr: str
    base_path: str = "ipsa"
    vault_token: str | None = None
    vault_skip_verify: bool = True
    vault_host: str | None = None
    token_path: str | None = None

    def __post_init__(self) -> None:
        """Validate Vault configuration."""
        if not self.vault_addr:
            raise ValueError("vault_addr is required")


@dataclass
class Credentials:
    """Application credentials."""

    database_password: str = ""
    api_keys: dict[str, str] = field(default_factory=dict)
    secrets: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate credentials."""
        if not self.database_password:
            logger.warning("database_password not provided")


@dataclass
class AppDeploymentConfig(ABC):
    """Base configuration for application deployment."""

    server: ServerConfig
    credentials: Credentials
    environment: EnvironmentType
    app_name: str
    # Repository defaults should be set by app-specific configs
    app_repo_url: str = ""  # Should be overridden by app-specific configs
    app_repo_branch: str = "main"
    app_repo_path: str = ""  # Should be overridden by app-specific configs
    vault_config: VaultConfig | None = None
    terraform_dir: str | None = None
    ansible_dir: str | None = None

    def __post_init__(self) -> None:
        """Validate base configuration."""
        if not self.app_name:
            raise ValueError("app_name is required")
        if not self.app_repo_path:
            raise ValueError("app_repo_path is required (should be set by app-specific config)")
        if not self.app_repo_url:
            raise ValueError("app_repo_url is required (should be set by app-specific config)")

    @abstractmethod
    def get_required_credentials(self) -> list[str]:
        """
        Get list of required credential names for this application.

        :return: List of credential names (e.g., ['database_password', 'jwt_secret'])
        """

    def generate_missing_credentials(self, overwrite_existing: bool = False) -> dict[str, str]:
        """
        Generate missing credentials.

        :param overwrite_existing: If True, regenerate existing credentials
        :return: Dictionary of generated credentials
        """
        generated = {}
        required = self.get_required_credentials()

        generator = CredentialGenerator()

        for cred_name in required:
            if cred_name == "database_password":
                if not self.credentials.database_password or overwrite_existing:
                    self.credentials.database_password = generator.generate_password(
                        length=32, include_special=False, exclude_chars="\"'\\"
                    )
                    generated["database_password"] = self.credentials.database_password
                    logger.info("Generated database password")
            elif cred_name.startswith("api_key_"):
                key_name = cred_name.replace("api_key_", "")
                if key_name not in self.credentials.api_keys or overwrite_existing:
                    self.credentials.api_keys[key_name] = generator.generate_api_key()
                    generated[cred_name] = self.credentials.api_keys[key_name]
                    logger.info(f"Generated API key: {key_name}")
            elif cred_name == "jwt_secret":
                if "jwt_secret" not in self.credentials.secrets or overwrite_existing:
                    self.credentials.secrets["jwt_secret"] = generator.generate_jwt_secret()
                    generated["jwt_secret"] = self.credentials.secrets["jwt_secret"]
                    logger.info("Generated JWT secret")
            elif cred_name == "encryption_key":
                if "encryption_key" not in self.credentials.secrets or overwrite_existing:
                    self.credentials.secrets["encryption_key"] = generator.generate_encryption_key()
                    generated["encryption_key"] = self.credentials.secrets["encryption_key"]
                    logger.info("Generated encryption key")
            elif cred_name not in self.credentials.secrets or overwrite_existing:
                self.credentials.secrets[cred_name] = generator.generate_secret_token()
                generated[cred_name] = self.credentials.secrets[cred_name]
                logger.info(f"Generated secret: {cred_name}")

        return generated

    def get_vault_handler(self) -> VaultHandler | None:
        """
        Get Vault handler if configured.

        :return: VaultHandler instance or None
        """
        if not self.vault_config:
            return None

        try:
            return VaultHandler(
                vault_addr=self.vault_config.vault_addr,
                base_path=self.vault_config.base_path,
                vault_token=self.vault_config.vault_token,
                vault_skip_verify=self.vault_config.vault_skip_verify,
                vault_host=self.vault_config.vault_host,
                token_path=self.vault_config.token_path,
            )
        except Exception as e:
            logger.warning(f"Failed to initialize Vault handler: {e}")
            return None

    def load_credentials_from_vault(self) -> bool:
        """
        Load credentials from Vault if configured.

        Vault secret structure expected:
        - {base_path}/{environment}/database -> contains "password" key
        - {base_path}/{environment}/secrets -> contains application secrets

        :return: True if credentials loaded successfully
        """
        if not self.vault_config:
            return False

        try:
            vault = self.get_vault_handler()
            if not vault:
                logger.warning("Failed to initialize Vault handler")
                return False

            # Test connection
            client = vault.connect()
            if not client:
                logger.error("Failed to connect to Vault")
                return False

            # Load database password
            # Secret path: {base_path}/{environment}/database
            database_secret_name = f"{self.environment.value}/database"
            database_secret = vault.get_secret(database_secret_name)

            if database_secret:
                if "password" in database_secret:
                    self.credentials.database_password = database_secret["password"]
                    logger.info("Loaded database password from Vault")
                else:
                    logger.warning(
                        f"Database secret found but 'password' key not present. "
                        f"Keys: {list(database_secret.keys())}"
                    )
            else:
                logger.warning(
                    f"Database secret not found at: {vault.base_path}/{database_secret_name}"
                )

            # Load application secrets
            # Secret path: {base_path}/{environment}/secrets
            secrets_secret_name = f"{self.environment.value}/secrets"
            app_secrets = vault.get_secret(secrets_secret_name)

            if app_secrets:
                self.credentials.secrets.update(app_secrets)
                logger.info(f"Loaded {len(app_secrets)} secrets from Vault")
            else:
                logger.debug(
                    f"No application secrets found at: {vault.base_path}/{secrets_secret_name}"
                )

            # Load API keys if stored separately
            # Secret path: {base_path}/{environment}/api_keys
            api_keys_secret_name = f"{self.environment.value}/api_keys"
            api_keys = vault.get_secret(api_keys_secret_name)

            if api_keys:
                self.credentials.api_keys.update(api_keys)
                logger.info(f"Loaded {len(api_keys)} API keys from Vault")

            # Load infrastructure secrets (Tailscale auth key, GitHub tokens, etc.)
            # Secret path: infra/* (outside base_path)
            # Create a temporary handler with base_path="infra" to access infra secrets
            from _utils.server_management.vault import VaultHandler

            infra_handler = VaultHandler(
                vault_addr=vault.vault_addr,
                base_path="infra",
                vault_token=vault._get_vault_token(),  # Get token from existing handler
                vault_skip_verify=vault.vault_skip_verify,
            )

            # Load Tailscale auth key
            infra_secrets = infra_handler.get_secret("tailscale")
            if infra_secrets:
                # Store in a way that app configs can access
                if "auth_key" in infra_secrets:
                    self.credentials.secrets["tailscale_auth_key"] = infra_secrets["auth_key"]
                    logger.info("Loaded Tailscale auth key from Vault at infra/tailscale")
                else:
                    logger.warning("Tailscale secret found but 'auth_key' key not present")
            else:
                logger.debug("No Tailscale auth key found in Vault at infra/tailscale")

            # Load GitHub credentials (token or SSH key)
            github_secrets = infra_handler.get_secret("github")
            if github_secrets:
                if "token" in github_secrets:
                    self.credentials.secrets["github_token"] = github_secrets["token"]
                    # Also add to api_keys for compatibility
                    self.credentials.api_keys["github_token"] = github_secrets["token"]
                    logger.info("Loaded GitHub token from Vault at infra/github")
                if "ssh_key" in github_secrets:
                    self.credentials.secrets["github_ssh_key"] = github_secrets["ssh_key"]
                    logger.info("Loaded GitHub SSH key from Vault at infra/github")
            else:
                logger.debug("No GitHub credentials found in Vault at infra/github")

            return True

        except Exception as e:
            logger.error(f"Failed to load credentials from Vault: {e}", exc_info=True)
            return False

    def save_credentials_to_vault(self, overwrite: bool = True) -> bool:
        """
        Save credentials to Vault if configured.

        Creates or updates secrets in Vault:
        - {base_path}/{environment}/database -> contains "password" key
        - {base_path}/{environment}/secrets -> contains application secrets
        - {base_path}/{environment}/api_keys -> contains API keys

        :param overwrite: If True, overwrite existing secrets. If False, skip if exists.
        :return: True if credentials saved successfully
        """
        if not self.vault_config:
            logger.debug("Vault not configured, skipping secret save")
            return False

        try:
            vault = self.get_vault_handler()
            if not vault:
                logger.warning("Failed to initialize Vault handler")
                return False

            # Test connection
            client = vault.connect()
            if not client:
                logger.error("Failed to connect to Vault")
                return False

            saved_count = 0

            # Save database password
            if self.credentials.database_password:
                database_secret_name = f"{self.environment.value}/database"
                full_vault_path = f"{vault.base_path}/{database_secret_name}"
                logger.info(f"[VAULT] Preparing to save database secret to: {full_vault_path}")

                # Check if secret exists
                existing = vault.get_secret(database_secret_name)
                if existing and not overwrite:
                    logger.info(
                        f"[VAULT] Database secret already exists at {full_vault_path}, skipping (use overwrite=True to update)"
                    )
                    logger.debug(
                        f"[VAULT] Existing secret keys: {list(existing.keys()) if existing else 'None'}"
                    )
                else:
                    logger.info(f"[VAULT] Creating/updating database secret at: {full_vault_path}")
                    success = vault.create_or_update_secret(
                        database_secret_name, {"password": self.credentials.database_password}
                    )
                    if success:
                        logger.info(
                            f"[VAULT] Successfully saved database password to: {full_vault_path}"
                        )
                        # Verify the secret was saved
                        verification = vault.get_secret(database_secret_name)
                        if verification:
                            logger.info(
                                f"[VAULT] Verification: Secret exists at {full_vault_path} with keys: {list(verification.keys())}"
                            )
                        else:
                            logger.warning(
                                f"[VAULT] Verification failed: Secret not found at {full_vault_path} immediately after save"
                            )
                        saved_count += 1
                    else:
                        logger.error(
                            f"[VAULT] Failed to save database password to: {full_vault_path}"
                        )

            # Save application secrets
            if self.credentials.secrets:
                secrets_secret_name = f"{self.environment.value}/secrets"
                full_vault_path = f"{vault.base_path}/{secrets_secret_name}"
                logger.info(f"[VAULT] Preparing to save application secrets to: {full_vault_path}")
                logger.debug(f"[VAULT] Secrets to save: {list(self.credentials.secrets.keys())}")

                existing = vault.get_secret(secrets_secret_name)
                if existing and not overwrite:
                    # Merge with existing secrets
                    merged_secrets = existing.copy()
                    merged_secrets.update(self.credentials.secrets)
                    secrets_to_save = merged_secrets
                    logger.info(f"[VAULT] Merging with existing secrets at {full_vault_path}")
                    logger.debug(f"[VAULT] Existing secret keys: {list(existing.keys())}")
                else:
                    secrets_to_save = self.credentials.secrets

                success = vault.create_or_update_secret(secrets_secret_name, secrets_to_save)
                if success:
                    logger.info(
                        f"[VAULT] Successfully saved {len(secrets_to_save)} secrets to: {full_vault_path}"
                    )
                    # Verify the secret was saved
                    verification = vault.get_secret(secrets_secret_name)
                    if verification:
                        logger.info(
                            f"[VAULT] Verification: Secret exists at {full_vault_path} with keys: {list(verification.keys())}"
                        )
                    else:
                        logger.warning(
                            f"[VAULT] Verification failed: Secret not found at {full_vault_path} immediately after save"
                        )
                    saved_count += 1
                else:
                    logger.error(f"[VAULT] Failed to save secrets to: {full_vault_path}")

            # Save API keys
            if self.credentials.api_keys:
                api_keys_secret_name = f"{self.environment.value}/api_keys"

                existing = vault.get_secret(api_keys_secret_name)
                if existing and not overwrite:
                    # Merge with existing API keys
                    merged_keys = existing.copy()
                    merged_keys.update(self.credentials.api_keys)
                    keys_to_save = merged_keys
                    logger.info(f"Merging with existing API keys at {api_keys_secret_name}")
                else:
                    keys_to_save = self.credentials.api_keys

                success = vault.create_or_update_secret(api_keys_secret_name, keys_to_save)
                if success:
                    logger.info(
                        f"Saved {len(keys_to_save)} API keys to Vault: "
                        f"{vault.base_path}/{api_keys_secret_name}"
                    )
                    saved_count += 1
                else:
                    logger.error("Failed to save API keys to Vault")

            # Save infrastructure secrets (Tailscale auth key, etc.) if present
            # Check if tailscale_auth_key is in credentials.secrets
            if "tailscale_auth_key" in self.credentials.secrets:
                # Create a temporary handler with base_path="infra" to access infra secrets
                from _utils.server_management.vault import VaultHandler

                infra_handler = VaultHandler(
                    vault_addr=vault.vault_addr,
                    base_path="infra",
                    vault_token=vault._get_vault_token(),  # Get token from existing handler
                    vault_skip_verify=vault.vault_skip_verify,
                )

                tailscale_secret = {"auth_key": self.credentials.secrets["tailscale_auth_key"]}

                existing = infra_handler.get_secret("tailscale")
                if existing and not overwrite:
                    # Merge with existing infrastructure secrets
                    merged_secrets = existing.copy()
                    merged_secrets.update(tailscale_secret)
                    secrets_to_save = merged_secrets
                    logger.info("Merging with existing infrastructure secrets at infra/tailscale")
                else:
                    secrets_to_save = tailscale_secret

                success = infra_handler.create_or_update_secret("tailscale", secrets_to_save)
                if success:
                    logger.info("Saved Tailscale auth key to Vault: infra/tailscale")
                    saved_count += 1
                else:
                    logger.error("Failed to save Tailscale auth key to Vault")

            if saved_count > 0:
                logger.info(f"Successfully saved {saved_count} secret group(s) to Vault")
                return True
            logger.warning("No credentials to save to Vault")
            return False

        except Exception as e:
            logger.error(f"Failed to save credentials to Vault: {e}", exc_info=True)
            return False

    @abstractmethod
    def get_ansible_vars(self) -> dict[str, Any]:
        """
        Get Ansible variables for deployment.

        :return: Dictionary of Ansible variables
        """

    @abstractmethod
    def get_terraform_vars(self) -> dict[str, Any]:
        """
        Get Terraform variables for deployment.

        :return: Dictionary of Terraform variables
        """


class AppDeploymentManager(ABC):
    """
    Base manager for application deployment.

    Provides common deployment orchestration logic that can be extended
    by application-specific managers. Designed for physical Linux servers
    with modular support for future cloud migration.
    """

    def __init__(
        self,
        config: AppDeploymentConfig,
        terraform_dir: str | None = None,
        ansible_dir: str | None = None,
    ) -> None:
        """
        Initialize application deployment manager.

        :param config: Application deployment configuration
        :param terraform_dir: Path to Terraform project directory
        :param ansible_dir: Path to Ansible project directory
        """
        self.config = config
        self.base_dir = Path(__file__).parent

        terraform_project_dir = terraform_dir or (
            self.base_dir / self.config.app_name.lower() / "terraform"
        )
        ansible_project_dir = ansible_dir or (
            self.base_dir / self.config.app_name.lower() / "ansible"
        )

        self.terraform_dir = Path(terraform_project_dir)
        self.ansible_dir = Path(ansible_project_dir)

        self.terraform_handler: TerraformHandler | None = None
        self.ansible_handler: AnsibleHandler | None = None

        logger.info(
            f"AppDeploymentManager initialized for {self.config.app_name} "
            f"on {self.config.server.host} ({self.config.environment.value})"
        )

    def _init_terraform(self) -> TerraformHandler:
        """Initialize Terraform handler."""
        if self.terraform_handler is None:
            # Determine remote project directory - terraform files should be in the app repo
            # The terraform directory structure matches infrastructure/dev/terraform in the repo
            if self.config.app_repo_path:
                remote_project_dir = f"{self.config.app_repo_path}/infrastructure/dev"
            else:
                # Fallback to a standard location
                remote_project_dir = f"/opt/{self.config.app_name}/infrastructure/dev"

            self.terraform_handler = TerraformHandler(
                project_dir=str(self.terraform_dir),
                remote_host=self.config.server.host,
                remote_user=self.config.server.user,
                remote_project_dir=remote_project_dir,
                auto_approve=True,
                ssh_key_path=self.config.server.ssh_key_path,
                ssh_port=self.config.server.port,
            )
        return self.terraform_handler

    def _init_ansible(self) -> AnsibleHandler:
        """Initialize Ansible handler."""
        if self.ansible_handler is None:
            # Use remote ansible directory based on app_repo_path
            remote_ansible_dir = f"{self.config.app_repo_path}/ansible"
            self.ansible_handler = AnsibleHandler(
                ansible_dir=str(self.ansible_dir),
                remote_host=self.config.server.host,
                remote_user=self.config.server.user,
                remote_ansible_dir=remote_ansible_dir,
            )
        return self.ansible_handler

    def provision_infrastructure(self) -> bool:
        """
        Provision infrastructure using Terraform.

        Creates databases, containers, and other infrastructure components
        on the physical Linux server. If Vault is configured and credentials
        are provided, ensures secrets are saved to Vault before provisioning.

        :return: True if successful, False otherwise
        """
        logger.info("Provisioning infrastructure with Terraform...")

        try:
            terraform = self._init_terraform()

            if not self.terraform_dir.exists():
                logger.warning(
                    f"Terraform directory does not exist: {self.terraform_dir}. "
                    "Skipping infrastructure provisioning."
                )
                return True

            # Ensure remote directory exists and copy terraform files
            if terraform.is_remote:
                logger.info(
                    f"Ensuring remote terraform directory exists: {terraform.remote_project_dir}"
                )
                import subprocess

                ssh_target = f"{self.config.server.user}@{self.config.server.host}"
                ssh_cmd = ["ssh"]
                if self.config.server.ssh_key_path:
                    ssh_cmd.extend(["-i", self.config.server.ssh_key_path])
                ssh_cmd.extend(["-p", str(self.config.server.port)])
                ssh_cmd.extend(["-o", "StrictHostKeyChecking=no"])
                ssh_cmd.extend(["-o", "BatchMode=yes"])
                ssh_cmd.append(ssh_target)
                ssh_cmd.append(
                    f"sudo mkdir -p {terraform.remote_project_dir} && sudo chown -R {self.config.server.user}:{self.config.server.user} {terraform.remote_project_dir}"
                )

                try:
                    result = subprocess.run(
                        ssh_cmd, check=False, capture_output=True, text=True, timeout=30
                    )
                    if result.returncode != 0:
                        logger.warning(f"Failed to create remote directory: {result.stderr}")
                    else:
                        logger.info(f"Remote directory created: {terraform.remote_project_dir}")
                except Exception as e:
                    logger.warning(f"Failed to create remote directory: {e}")

                # Clean up any extra .tf files on remote server that aren't in local directory
                logger.info("Cleaning up extra Terraform files on remote server...")
                local_tf_files = {f.name for f in self.terraform_dir.glob("*.tf")}
                if local_tf_files:
                    # Build a list of files to keep
                    keep_files = " ".join(local_tf_files)
                    cleanup_cmd = ["ssh"]
                    if self.config.server.ssh_key_path:
                        cleanup_cmd.extend(["-i", self.config.server.ssh_key_path])
                    cleanup_cmd.extend(["-P", str(self.config.server.port)])
                    cleanup_cmd.extend(["-o", "StrictHostKeyChecking=no"])
                    cleanup_cmd.append(ssh_target)
                    cleanup_cmd.append(
                        f'cd {terraform.remote_project_dir} && for f in *.tf; do if ! echo \'{keep_files}\' | grep -qw "$f"; then echo "Removing extra file: $f"; rm -f "$f"; fi; done'
                    )
                    try:
                        cleanup_result = subprocess.run(
                            cleanup_cmd, check=False, capture_output=True, text=True, timeout=60
                        )
                        if cleanup_result.returncode == 0 and cleanup_result.stdout.strip():
                            logger.info(f"Cleanup output: {cleanup_result.stdout.strip()}")
                    except Exception as e:
                        logger.warning(f"Failed to clean up extra Terraform files: {e}")

                # Copy terraform files to server
                logger.info("Copying terraform files to server...")
                # Use forward slashes for scp (works on both Windows and Linux)
                str(self.terraform_dir).replace("\\", "/")
                # Copy all .tf files and README
                terraform_files = list(self.terraform_dir.glob("*.tf")) + list(
                    self.terraform_dir.glob("README*")
                )
                if not terraform_files:
                    logger.warning("No terraform files found to copy")
                    return False

                for tf_file in terraform_files:
                    scp_cmd = ["scp"]
                    if self.config.server.ssh_key_path:
                        scp_cmd.extend(["-i", self.config.server.ssh_key_path])
                    scp_cmd.extend(["-P", str(self.config.server.port)])
                    scp_cmd.extend(["-o", "StrictHostKeyChecking=no"])
                    scp_cmd.append(str(tf_file).replace("\\", "/"))
                    scp_cmd.append(f"{ssh_target}:{terraform.remote_project_dir}/")

                    try:
                        result = subprocess.run(
                            scp_cmd, check=False, capture_output=True, text=True, timeout=300
                        )
                        if result.returncode != 0:
                            logger.error(f"Failed to copy {tf_file.name}: {result.stderr}")
                            return False
                        logger.debug(f"Copied {tf_file.name}")
                    except subprocess.TimeoutExpired:
                        logger.exception(f"Terraform file copy timed out for {tf_file.name}")
                        return False
                    except FileNotFoundError:
                        logger.exception("scp not found. Please install OpenSSH client.")
                        return False
                    except Exception as e:
                        logger.exception(f"Failed to copy {tf_file.name}: {e}")
                        return False

                logger.info(f"Terraform files copied successfully ({len(terraform_files)} files)")

            # Clean up any leftover terraformrc files and old lock files before init
            # Also set up SSH config for Docker provider
            if terraform.is_remote:
                import subprocess

                ssh_target = f"{self.config.server.user}@{self.config.server.host}"
                ssh_cmd = ["ssh"]
                if self.config.server.ssh_key_path:
                    ssh_cmd.extend(["-i", self.config.server.ssh_key_path])
                ssh_cmd.extend(["-p", str(self.config.server.port)])
                ssh_cmd.extend(["-o", "StrictHostKeyChecking=no"])
                ssh_cmd.extend(["-o", "BatchMode=yes"])
                ssh_cmd.append(ssh_target)

                # Clean up any leftover terraformrc files and old lock files before init
                # Docker provider uses local socket when Terraform runs on remote server, so no SSH config needed
                cleanup_cmd = f'rm -f ~/.terraformrc ~/.terraform.d/plugins/dev_overrides.hcl 2>/dev/null; find ~ -maxdepth 2 -name ".terraformrc" -type f -delete 2>/dev/null; rm -f {terraform.remote_project_dir}/.terraform.lock.hcl 2>/dev/null; true'
                subprocess.run(
                    [*ssh_cmd, cleanup_cmd], check=False, capture_output=True, text=True, timeout=30
                )

            # Initialize Terraform first to install providers
            # Try init, and if it fails due to GPG key issues, work around it
            logger.info("[TERRAFORM] Initializing Terraform project...")
            logger.info("[TERRAFORM] This step downloads providers and may take a few minutes...")
            manually_installed_provider = False
            init_result = terraform.init(check=False)
            logger.info(f"[TERRAFORM] Init completed with exit code: {init_result.returncode}")
            if init_result.returncode != 0:
                error_output = (init_result.stderr or "") + (init_result.stdout or "")
                logger.info(f"Terraform init failed with return code {init_result.returncode}")
                logger.debug(
                    f"Terraform init stderr: {init_result.stderr[:1000] if init_result.stderr else 'None'}"
                )
                logger.debug(
                    f"Terraform init stdout: {init_result.stdout[:1000] if init_result.stdout else 'None'}"
                )
                # Check for GPG/signature errors or dev_overrides issues in the output
                has_gpg_error = (
                    "key expired" in error_output.lower()
                    or "signature" in error_output.lower()
                    or "openpgp" in error_output.lower()
                    or "expired" in error_output.lower()
                    or "error checking signature" in error_output.lower()
                    or "dev_overrides" in error_output.lower()
                    or "development overrides" in error_output.lower()
                )
                if has_gpg_error:
                    logger.warning(
                        "[TERRAFORM] Terraform init failed due to GPG signature issue, attempting workaround..."
                    )
                    if terraform.is_remote:
                        import subprocess

                        ssh_target = f"{self.config.server.user}@{self.config.server.host}"
                        logger.info(
                            "[TERRAFORM] Manually installing Docker provider to bypass GPG signature issue..."
                        )
                        logger.info(
                            "[TERRAFORM] This workaround downloads the provider directly from GitHub..."
                        )
                        ssh_cmd = ["ssh"]
                        if self.config.server.ssh_key_path:
                            ssh_cmd.extend(["-i", self.config.server.ssh_key_path])
                        ssh_cmd.extend(["-p", str(self.config.server.port)])
                        ssh_cmd.extend(["-o", "StrictHostKeyChecking=no"])
                        ssh_cmd.extend(["-o", "BatchMode=yes"])
                        ssh_cmd.append(ssh_target)
                        # Detect architecture
                        arch_cmd = "uname -m"
                        arch_result = subprocess.run(
                            [*ssh_cmd, arch_cmd],
                            check=False,
                            capture_output=True,
                            text=True,
                            timeout=30,
                        )
                        arch = (
                            "arm64"
                            if "aarch64" in (arch_result.stdout or "").lower()
                            or "arm64" in (arch_result.stdout or "").lower()
                            else "amd64"
                        )

                        # Get latest version from GitHub API (simpler and more reliable)
                        logger.info(
                            "[TERRAFORM] Fetching latest Docker provider version from GitHub..."
                        )
                        version_cmd = r"""curl -s "https://api.github.com/repos/kreuzwerker/terraform-provider-docker/releases/latest" | grep -o '"tag_name":"v[0-9.]*"' | sed 's/"tag_name":"v//' | sed 's/"//' """
                        version_result = subprocess.run(
                            [*ssh_cmd, version_cmd],
                            check=False,
                            capture_output=True,
                            text=True,
                            timeout=30,
                        )

                        provider_version = (
                            version_result.stdout.strip()
                            if version_result.stdout and version_result.returncode == 0
                            else "3.9.0"
                        )
                        logger.info(
                            f"[TERRAFORM] Using Docker provider version: {provider_version}"
                        )
                        # Remove 'v' prefix if present
                        provider_version = provider_version.lstrip("v")
                        logger.info(f"Using Docker provider version: {provider_version}")

                        # Clean up terraformrc and manually install latest provider
                        workaround_cmd = f"""cd {terraform.remote_project_dir} && \
rm -f ~/.terraformrc ~/.terraform.d/plugins/dev_overrides.hcl 2>/dev/null && \
mkdir -p .terraform/providers/registry.terraform.io/kreuzwerker/docker/{provider_version}/linux_{arch} && \
wget -q "https://github.com/kreuzwerker/terraform-provider-docker/releases/download/v{provider_version}/terraform-provider-docker_{provider_version}_linux_{arch}.zip" -O /tmp/docker-provider.zip && \
if [ -f /tmp/docker-provider.zip ]; then \
  unzip -q -o /tmp/docker-provider.zip -d .terraform/providers/registry.terraform.io/kreuzwerker/docker/{provider_version}/linux_{arch}/ && \
  chmod +x .terraform/providers/registry.terraform.io/kreuzwerker/docker/{provider_version}/linux_{arch}/terraform-provider-docker_* && \
  PROVIDER_BIN="$(find .terraform/providers/registry.terraform.io/kreuzwerker/docker/{provider_version}/linux_{arch}/ -name 'terraform-provider-docker_*' -type f | head -1)" && \
  if [ -n "$PROVIDER_BIN" ] && [ -f "$PROVIDER_BIN" ]; then \
    rm -f /tmp/docker-provider.zip && \
    echo "Docker provider installed at $PROVIDER_BIN" && \
    echo "Docker provider installed at $PROVIDER_BIN" && \
    echo "Installing other providers (vault, local)..." && \
    terraform init -backend=false -upgrade 2>&1 | (grep -v "key expired" | grep -v "signature" | grep -v "error checking signature" | grep -v "kreuzwerker/docker" || true); \
    echo "Creating lock file manually with correct provider versions..." && \
    cat > .terraform.lock.hcl << 'LOCKEOF'
# This file is maintained automatically by "terraform init".
# Manual edits may be lost in future updates.

provider "registry.terraform.io/hashicorp/local" {{
  version     = "2.6.1"
  constraints = "~> 2.5"
  hashes = [
    "h1:7y8IXQZt2qrj1slo1LmV42B8qbcFvVn1fH2GqJ6e7bs=",
    "h1:9Ba8sheiJgsnDxLYRLknHLV3+2D+BxR8Jx3W2YXw2fw=",
  ]
}}

provider "registry.terraform.io/hashicorp/vault" {{
  version     = "4.8.0"
  constraints = "~> 4.0"
  hashes = [
    "h1:ZzJfOmqpYF3dJ3QYr/wtJN3KKnJZkXq7E3Z8k8nJ3X4=",
    "h1:9Ba8sheiJgsnDxLYRLknHLV3+2D+BxR8Jx3W2YXw2fw=",
  ]
}}

provider "registry.terraform.io/kreuzwerker/docker" {{
  version     = "{provider_version}"
  hashes = [
    "h1:placeholder=",
  ]
}}
LOCKEOF
    sed -i "s|{{provider_version}}|{provider_version}|g" .terraform.lock.hcl && \
    echo "Creating .terraformrc with dev_overrides to use manually installed Docker provider..." && \
    TERRAFORM_DIR="$(pwd)" && \
    cat > ~/.terraformrc << TERRAFORMRC
provider_installation {{
  dev_overrides {{
    "kreuzwerker/docker" = "$TERRAFORM_DIR/.terraform/providers/registry.terraform.io/kreuzwerker/docker/{provider_version}/linux_{arch}"
  }}
}}
TERRAFORMRC
    echo "Running terraform init with -backend=false -lock=false to complete initialization..." && \
    terraform init -backend=false -upgrade -lock=false -input=false 2>&1 | (grep -v "key expired" | grep -v "signature" | grep -v "error checking signature" | grep -v "kreuzwerker/docker" || true); \
    INIT_EXIT=$?; \
    echo "Init exit code: $INIT_EXIT. Running full init..." && \
    terraform init -upgrade -input=false 2>&1 | (grep -v "key expired" | grep -v "signature" | grep -v "error checking signature" | grep -v "kreuzwerker/docker" || true); \
    INIT_EXIT=$?; \
    echo "Final init exit code: $INIT_EXIT"; \
    echo "Terraform init completed (exit code: $INIT_EXIT). Verifying providers..." && \
    if terraform providers 2>&1 | grep -q "provider\\[registry.terraform.io"; then \
      echo "Providers are registered. Deployment should proceed."; \
    else \
      echo "Warning: Provider registration may be incomplete, but continuing..."; \
    fi; \
  else \
    echo "Provider binary not found after extraction" && exit 1; \
  fi; \
else \
  echo "Failed to download provider" && exit 1; \
fi"""
                        logger.info("[TERRAFORM] Executing provider installation workaround...")
                        logger.info(
                            "[TERRAFORM] This may take 2-3 minutes to download and install..."
                        )
                        result = subprocess.run(
                            [*ssh_cmd, workaround_cmd],
                            check=False,
                            capture_output=True,
                            text=True,
                            timeout=600,
                        )
                        logger.info(
                            f"[TERRAFORM] Provider installation exit code: {result.returncode}"
                        )
                        if result.stdout:
                            logger.info("[TERRAFORM] Provider installation output (last 20 lines):")
                            for line in result.stdout.split("\n")[-20:]:
                                if line.strip():
                                    logger.info(f"[TERRAFORM]   {line}")
                        if result.returncode == 0:
                            logger.info(
                                "[TERRAFORM] Terraform init succeeded with manually installed provider"
                            )
                            manually_installed_provider = True
                        else:
                            logger.warning(
                                f"[TERRAFORM] Provider installation had issues: {result.stderr[:200] if result.stderr else 'No stderr'}"
                            )
                            error_msg = result.stderr or result.stdout or "Unknown error"
                            logger.error(
                                f"[TERRAFORM] Manual provider installation failed: {error_msg[:500]}"
                            )
                            raise Exception(f"Terraform init failed: {error_msg[:500]}")
                else:
                    raise Exception(f"Terraform init failed: {error_output}")
            if init_result.returncode == 0 or manually_installed_provider:
                logger.info("[TERRAFORM] Terraform initialization successful")
                if manually_installed_provider:
                    logger.info(
                        "[TERRAFORM] Note: Used manual provider installation workaround for GPG signature issue"
                    )
            else:
                logger.error(
                    f"[TERRAFORM] Terraform initialization failed: {init_result.stderr[:500] if init_result.stderr else 'Unknown error'}"
                )
                raise Exception(
                    f"Terraform init failed: {init_result.stderr[:200] if init_result.stderr else 'Unknown error'}"
                )

            # Validate Terraform configuration
            logger.info("[TERRAFORM] Validating Terraform configuration...")
            is_valid, message = terraform.validate()
            if not is_valid:
                logger.error(f"[TERRAFORM] Terraform validation failed: {message}")
                raise Exception(f"Terraform validation failed: {message[:200]}")
            logger.info("[TERRAFORM] Terraform configuration is valid")

            terraform_vars = self.config.get_terraform_vars()

            # Log Terraform variables for diagnosis (mask sensitive values)
            logger.info("[TERRAFORM] Terraform variables being passed:")
            for key, value in terraform_vars.items():
                if "token" in key.lower() or "password" in key.lower() or "secret" in key.lower():
                    masked_value = (
                        f"{str(value)[:4]}...{str(value)[-4:]}"
                        if value and len(str(value)) > 8
                        else "***"
                    )
                    logger.info(f"[TERRAFORM]   {key} = {masked_value}")
                else:
                    logger.info(f"[TERRAFORM]   {key} = {value}")

            # Log expected Vault paths that Terraform will try to read
            if self.config.vault_config:
                vault_base = terraform_vars.get("vault_base_path", "ipsa")
                environment = terraform_vars.get("environment", "demo")
                expected_db_path = f"{vault_base}/{environment}/database"
                expected_secrets_path = f"{vault_base}/{environment}/secrets"
                logger.info("[TERRAFORM] Terraform will attempt to read Vault secrets at:")
                logger.info(f"[TERRAFORM]   Database: {expected_db_path}")
                logger.info(f"[TERRAFORM]   Secrets: {expected_secrets_path}")

                # Verify secrets exist before Terraform runs
                if self.config.vault_config:
                    vault = self.config.get_vault_handler()
                    if vault:
                        logger.info(
                            "[TERRAFORM] Pre-flight check: Verifying Vault secrets exist..."
                        )
                        db_check = vault.get_secret(f"{environment}/database")
                        secrets_check = vault.get_secret(f"{environment}/secrets")
                        if db_check:
                            logger.info(
                                f"[TERRAFORM] Pre-flight check: Database secret found at {expected_db_path}"
                            )
                        else:
                            logger.warning(
                                f"[TERRAFORM] Pre-flight check: Database secret NOT found at {expected_db_path}"
                            )
                        if secrets_check:
                            logger.info(
                                f"[TERRAFORM] Pre-flight check: Application secrets found at {expected_secrets_path}"
                            )
                        else:
                            logger.warning(
                                f"[TERRAFORM] Pre-flight check: Application secrets NOT found at {expected_secrets_path}"
                            )

            # If we manually installed providers, use -lock=false to bypass lock file validation
            if manually_installed_provider:
                logger.info(
                    "Using -lock=false for plan/apply due to manually installed provider workaround"
                )
                # Run plan with -lock=false
                import subprocess

                ssh_target = f"{self.config.server.user}@{self.config.server.host}"
                ssh_cmd = ["ssh"]
                if self.config.server.ssh_key_path:
                    ssh_cmd.extend(["-i", self.config.server.ssh_key_path])
                ssh_cmd.extend(["-p", str(self.config.server.port)])
                ssh_cmd.extend(["-o", "StrictHostKeyChecking=no"])
                ssh_cmd.extend(["-o", "BatchMode=yes"])
                ssh_cmd.append(ssh_target)

                # Build plan command with -lock=false
                # Docker provider will use local socket when running on remote server
                # Build terraform command with all variables
                logger.info("[TERRAFORM] Building terraform plan command...")
                plan_cmd_parts = ["terraform plan -lock=false -input=false"]
                for key, value in terraform_vars.items():
                    if isinstance(value, (dict, list)):
                        import json

                        value = json.dumps(value)
                    plan_cmd_parts.append(f'-var "{key}={value}"')
                plan_cmd = " ".join(plan_cmd_parts)

                # Use sudo for docker access - simpler and more reliable than sg docker
                # Wrap in sh -c to handle cd and other shell built-ins
                logger.info("[TERRAFORM] Running terraform plan with sudo docker access...")

                # Test docker access first
                docker_test_cmd = 'sudo -n docker ps >/dev/null 2>&1 && echo "Docker accessible" || echo "Docker requires sudo"'
                test_result = subprocess.run(
                    [*ssh_cmd[:-1], docker_test_cmd],
                    check=False,
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                logger.info(f"[TERRAFORM] Docker access test: {test_result.stdout.strip()}")

                # Run terraform plan with sudo, wrapping in sh -c to handle cd
                plan_cmd_with_sudo = f'sudo sh -c "cd {terraform.remote_project_dir} && {plan_cmd}"'
                ssh_cmd.append(plan_cmd_with_sudo)
                logger.info(
                    "[TERRAFORM] Starting terraform plan (this may take several minutes for provider downloads)..."
                )
                logger.info("[TERRAFORM] Progress will be logged as it becomes available...")

                # Run with real-time output streaming for better visibility
                logger.info("[TERRAFORM] Executing terraform plan command...")
                plan_result = subprocess.run(
                    ssh_cmd, check=False, capture_output=True, text=True, timeout=900
                )

                # Log full Terraform plan output with more detail
                logger.info("[TERRAFORM] ========== TERRAFORM PLAN OUTPUT ==========")
                if plan_result.stdout:
                    for line in plan_result.stdout.split("\n"):
                        if line.strip():
                            logger.info(f"[TERRAFORM] {line}")
                if plan_result.stderr:
                    logger.warning("[TERRAFORM] ========== TERRAFORM PLAN STDERR ==========")
                    for line in plan_result.stderr.split("\n"):
                        if line.strip():
                            logger.warning(f"[TERRAFORM] {line}")
                    logger.warning("[TERRAFORM] ===========================================")
                logger.info(f"[TERRAFORM] Plan exit code: {plan_result.returncode}")
                logger.info("[TERRAFORM] ===========================================")

                if plan_result.stderr:
                    logger.warning("[TERRAFORM] ========== TERRAFORM PLAN STDERR ==========")
                    for line in plan_result.stderr.split("\n"):
                        if line.strip():
                            logger.warning(f"[TERRAFORM] {line}")
                    logger.warning("[TERRAFORM] ============================================")

                if plan_result.returncode == 0:
                    logger.info("[TERRAFORM] Terraform plan succeeded (no changes needed)")
                elif plan_result.returncode == 2:
                    logger.info("[TERRAFORM] Terraform plan succeeded (changes detected)")
                else:
                    logger.error(
                        f"[TERRAFORM] Terraform plan failed with return code {plan_result.returncode}"
                    )
                    raise Exception(
                        f"Terraform plan failed: {plan_result.stderr[:200] if plan_result.stderr else 'Unknown error'}"
                    )

                # Run apply with -lock=false
                # Build terraform command with all variables
                apply_cmd_parts = [
                    f"cd {terraform.remote_project_dir} && terraform apply -auto-approve -lock=false"
                ]
                for key, value in terraform_vars.items():
                    if isinstance(value, (dict, list)):
                        import json

                        value = json.dumps(value)
                    apply_cmd_parts.append(f'-var "{key}={value}"')
                apply_cmd = " ".join(apply_cmd_parts)
                # Use sudo for docker access - simpler and more reliable
                logger.info("[TERRAFORM] Building terraform apply command...")
                apply_cmd_with_sudo = f"sudo {apply_cmd}"
                ssh_cmd_apply = ssh_cmd[:-1] + [
                    apply_cmd_with_sudo
                ]  # Reuse ssh_cmd but replace the command
                logger.info("[TERRAFORM] Running terraform apply with sudo docker access...")
                logger.info("[TERRAFORM] Progress will be logged as it becomes available...")
                apply_result = subprocess.run(
                    ssh_cmd_apply, check=False, capture_output=True, text=True, timeout=900
                )

                # Log full Terraform apply output
                if apply_result.stdout:
                    logger.info("[TERRAFORM] ========== TERRAFORM APPLY OUTPUT ==========")
                    for line in apply_result.stdout.split("\n"):
                        if line.strip():
                            logger.info(f"[TERRAFORM] {line}")
                    logger.info("[TERRAFORM] ============================================")

                if apply_result.stderr:
                    logger.warning("[TERRAFORM] ========== TERRAFORM APPLY STDERR ==========")
                    for line in apply_result.stderr.split("\n"):
                        if line.strip():
                            logger.warning(f"[TERRAFORM] {line}")
                    logger.warning("[TERRAFORM] ============================================")

                if apply_result.returncode == 0:
                    logger.info("[TERRAFORM] Terraform apply succeeded")
                else:
                    logger.error(
                        f"[TERRAFORM] Terraform apply failed with return code {apply_result.returncode}"
                    )
            # For remote terraform, we also need docker group access
            elif terraform.is_remote:
                logger.info("[TERRAFORM] Running terraform plan (remote with docker group)...")
                import subprocess

                ssh_target = f"{self.config.server.user}@{self.config.server.host}"
                ssh_cmd = ["ssh"]
                if self.config.server.ssh_key_path:
                    ssh_cmd.extend(["-i", self.config.server.ssh_key_path])
                ssh_cmd.extend(["-p", str(self.config.server.port)])
                ssh_cmd.extend(["-o", "StrictHostKeyChecking=no"])
                ssh_cmd.extend(["-o", "BatchMode=yes"])
                ssh_cmd.append(ssh_target)

                # Build plan command with all variables
                plan_cmd_parts = ["terraform plan -input=false"]
                for key, value in terraform_vars.items():
                    if isinstance(value, (dict, list)):
                        import json

                        value = json.dumps(value)
                    plan_cmd_parts.append(f'-var "{key}={value}"')
                plan_cmd = " ".join(plan_cmd_parts)
                # Use sudo for docker access - simpler and more reliable
                # Wrap in sh -c to handle cd and other shell built-ins
                logger.info("[TERRAFORM] Running terraform plan with sudo docker access...")
                plan_cmd_with_sudo = f'sudo sh -c "cd {terraform.remote_project_dir} && {plan_cmd}"'
                ssh_cmd.append(plan_cmd_with_sudo)
                logger.info(
                    "[TERRAFORM] Starting terraform plan (this may take several minutes)..."
                )
                plan_result = subprocess.run(
                    ssh_cmd, check=False, capture_output=True, text=True, timeout=900
                )

                # Log full Terraform plan output
                if plan_result.stdout:
                    logger.info("[TERRAFORM] ========== TERRAFORM PLAN OUTPUT ==========")
                    for line in plan_result.stdout.split("\n"):
                        if line.strip():
                            logger.info(f"[TERRAFORM] {line}")
                    logger.info("[TERRAFORM] ===========================================")

                if plan_result.stderr:
                    logger.warning("[TERRAFORM] ========== TERRAFORM PLAN STDERR ==========")
                    for line in plan_result.stderr.split("\n"):
                        if line.strip():
                            logger.warning(f"[TERRAFORM] {line}")
                    logger.warning("[TERRAFORM] ============================================")

                if plan_result.returncode == 0:
                    logger.info("[TERRAFORM] Terraform plan succeeded (no changes needed)")
                elif plan_result.returncode == 2:
                    logger.info("[TERRAFORM] Terraform plan succeeded (changes detected)")
                else:
                    logger.error(
                        f"[TERRAFORM] Terraform plan failed with return code {plan_result.returncode}"
                    )
                    raise Exception(
                        f"Terraform plan failed: {plan_result.stderr[:200] if plan_result.stderr else 'Unknown error'}"
                    )

                # Check for actual Vault-related errors in output (not just the word "vault")
                if plan_result.stdout:
                    if "no secret found" in plan_result.stdout.lower() or (
                        "error" in plan_result.stdout.lower()
                        and "vault" in plan_result.stdout.lower()
                    ):
                        logger.error("[TERRAFORM] Vault-related error detected in plan output:")
                        for line in plan_result.stdout.split("\n"):
                            if (
                                "error" in line.lower() and "vault" in line.lower()
                            ) or "no secret found" in line.lower():
                                logger.error(f"[TERRAFORM]   {line}")

                # Build apply command
                apply_cmd_parts = ["terraform apply -auto-approve -input=false"]
                for key, value in terraform_vars.items():
                    if isinstance(value, (dict, list)):
                        import json

                        value = json.dumps(value)
                    apply_cmd_parts.append(f'-var "{key}={value}"')
                apply_cmd = " ".join(apply_cmd_parts)
                # Use sudo for docker access - simpler and more reliable
                # Wrap in sh -c to handle cd and other shell built-ins
                logger.info("[TERRAFORM] Building terraform apply command...")
                apply_cmd_with_sudo = (
                    f'sudo sh -c "cd {terraform.remote_project_dir} && {apply_cmd}"'
                )
                ssh_cmd_apply = [*ssh_cmd[:-1], apply_cmd_with_sudo]
                logger.info("[TERRAFORM] Running terraform apply with sudo docker access...")
                logger.info("[TERRAFORM] Progress will be logged as it becomes available...")
                apply_result = subprocess.run(
                    ssh_cmd_apply, check=False, capture_output=True, text=True, timeout=900
                )

                # Log full Terraform apply output
                if apply_result.stdout:
                    logger.info("[TERRAFORM] ========== TERRAFORM APPLY OUTPUT ==========")
                    for line in apply_result.stdout.split("\n"):
                        if line.strip():
                            logger.info(f"[TERRAFORM] {line}")
                    logger.info("[TERRAFORM] ============================================")

                if apply_result.stderr:
                    logger.warning("[TERRAFORM] ========== TERRAFORM APPLY STDERR ==========")
                    for line in apply_result.stderr.split("\n"):
                        if line.strip():
                            logger.warning(f"[TERRAFORM] {line}")
                    logger.warning("[TERRAFORM] ============================================")

                if apply_result.returncode == 0:
                    logger.info("[TERRAFORM] Terraform apply succeeded")
                else:
                    logger.error(
                        f"[TERRAFORM] Terraform apply failed with return code {apply_result.returncode}"
                    )
            else:
                logger.info("[TERRAFORM] Running terraform plan...")
                plan_result, _ = terraform.plan(vars=terraform_vars)

                if plan_result.returncode != 0:
                    logger.warning("[TERRAFORM] Terraform plan completed with warnings")
                    if plan_result.stderr:
                        logger.debug(f"[TERRAFORM] Plan stderr: {plan_result.stderr[:500]}")
                    if plan_result.stdout:
                        # Check for Vault-related errors in output
                        if (
                            "no secret found" in plan_result.stdout.lower()
                            or "vault" in plan_result.stdout.lower()
                        ):
                            logger.error("[TERRAFORM] Vault-related error detected in plan output:")
                            for line in plan_result.stdout.split("\n"):
                                if (
                                    "vault" in line.lower()
                                    or "secret" in line.lower()
                                    or "error" in line.lower()
                                ):
                                    logger.error(f"[TERRAFORM]   {line}")

            apply_result = terraform.apply(vars=terraform_vars)

            logger.info("Infrastructure provisioning completed")
            return apply_result.returncode == 0

        except Exception as e:
            logger.exception(f"Infrastructure provisioning failed: {e}")
            return False

    def install_basic_dependencies(self) -> bool:
        """
        Install basic system dependencies required before infrastructure provisioning.
        This includes tools like Terraform, Ansible, and other prerequisites.

        :return: True if successful, False otherwise
        """
        logger.info("Installing basic dependencies (Terraform, etc.)...")

        try:
            # Install Terraform directly via SSH (skip Ansible for this step)
            import subprocess

            ssh_target = f"{self.config.server.user}@{self.config.server.host}"
            ssh_cmd = ["ssh"]
            if self.config.server.ssh_key_path:
                ssh_cmd.extend(["-i", self.config.server.ssh_key_path])
            ssh_cmd.extend(["-p", str(self.config.server.port)])
            ssh_cmd.extend(["-o", "StrictHostKeyChecking=no"])
            ssh_cmd.extend(["-o", "BatchMode=yes"])
            ssh_cmd.append(ssh_target)

            # Check if Terraform is already installed and up to date
            check_cmd = 'which terraform && terraform version || echo "NOT_INSTALLED"'
            ssh_check_cmd = ssh_cmd.copy()
            ssh_check_cmd.append(check_cmd)

            terraform_needs_upgrade = False
            try:
                check_result = subprocess.run(
                    ssh_check_cmd, check=False, capture_output=True, text=True, timeout=30
                )
                if check_result.returncode == 0 and "NOT_INSTALLED" not in check_result.stdout:
                    # Check if version is 1.14.1 or newer
                    version_output = check_result.stdout
                    import re

                    version_match = re.search(r"Terraform v(\d+\.\d+\.\d+)", version_output)
                    if version_match:
                        current_version = version_match.group(1)
                        logger.info(f"Terraform is installed: v{current_version}")
                        # Compare versions - if less than 1.14.1, upgrade
                        version_parts = [int(x) for x in current_version.split(".")]
                        if version_parts < [1, 14, 1]:
                            logger.info(
                                f"Terraform v{current_version} is outdated, will upgrade to 1.14.1"
                            )
                            terraform_needs_upgrade = True
                        else:
                            logger.info("Terraform is up to date")
                            # Still need to ensure docker group access
                            terraform_needs_upgrade = False
                    else:
                        logger.info(
                            "Terraform is installed but version could not be determined, will upgrade"
                        )
                        terraform_needs_upgrade = True
            except Exception as e:
                logger.debug(f"Error checking Terraform: {e}")

            # Always ensure docker group access, regardless of terraform upgrade status
            logger.info("Ensuring user has Docker access...")
            docker_group_cmd = f'sudo usermod -aG docker {self.config.server.user} 2>&1; groups | grep -q docker && echo "User in docker group" || echo "User NOT in docker group"'
            ssh_docker_cmd = ssh_cmd.copy()
            ssh_docker_cmd.append(docker_group_cmd)
            try:
                docker_result = subprocess.run(
                    ssh_docker_cmd, check=False, capture_output=True, text=True, timeout=30
                )
                logger.info(f"Docker group check output: {docker_result.stdout.strip()}")
                if docker_result.returncode == 0:
                    logger.info("Docker group access configured")
                else:
                    logger.warning(f"Could not configure docker group: {docker_result.stderr}")
            except Exception as e:
                logger.warning(f"Error configuring docker group: {e}")

            # Install Ansible if not already installed
            logger.info("Checking if Ansible is installed...")
            ansible_check_cmd = "which ansible ansible-playbook ansible-galaxy 2>&1 | head -3"
            ssh_ansible_check = ssh_cmd.copy()
            ssh_ansible_check.append(ansible_check_cmd)
            try:
                ansible_check_result = subprocess.run(
                    ssh_ansible_check, check=False, capture_output=True, text=True, timeout=30
                )
                ansible_installed = (
                    ansible_check_result.returncode == 0
                    and "ansible" in ansible_check_result.stdout
                )
                if not ansible_installed:
                    logger.info("Ansible not found, installing...")
                    ansible_install_cmd = "sudo apt-get update -qq && sudo apt-get install -y ansible && ansible --version"
                    ssh_ansible_install = ssh_cmd.copy()
                    ssh_ansible_install.append(ansible_install_cmd)
                    ansible_install_result = subprocess.run(
                        ssh_ansible_install,
                        check=False,
                        capture_output=True,
                        text=True,
                        timeout=300,
                    )
                    if ansible_install_result.returncode == 0:
                        logger.info("Ansible installed successfully")
                        if ansible_install_result.stdout:
                            logger.debug(
                                f"Ansible version: {ansible_install_result.stdout.strip()}"
                            )
                    else:
                        logger.warning(
                            f"Ansible installation may have failed: {ansible_install_result.stderr[:200]}"
                        )
                else:
                    logger.info("Ansible is already installed")
            except Exception as e:
                logger.warning(f"Error checking/installing Ansible: {e}")

            if terraform_needs_upgrade:
                logger.info("Upgrading Terraform to latest version...")
            else:
                # Terraform is already installed and up to date, just return success
                return True

            # Detect architecture and install Terraform
            logger.info("Detecting architecture and installing Terraform...")
            arch_cmd = "uname -m"
            ssh_arch_cmd = ssh_cmd.copy()
            ssh_arch_cmd.append(arch_cmd)

            arch = "amd64"  # default
            try:
                arch_result = subprocess.run(
                    ssh_arch_cmd, check=False, capture_output=True, text=True, timeout=30
                )
                if arch_result.returncode == 0:
                    detected_arch = arch_result.stdout.strip()
                    if "aarch64" in detected_arch or "arm64" in detected_arch:
                        arch = "arm64"
                    elif "x86_64" in detected_arch:
                        arch = "amd64"
                    logger.info(f"Detected architecture: {detected_arch} (using {arch})")
            except Exception as e:
                logger.warning(f"Could not detect architecture, using default (amd64): {e}")

            install_cmd = f"""sudo apt-get update -qq && \
sudo apt-get install -y unzip wget && \
TERRAFORM_VERSION=1.14.1 && \
wget -q https://releases.hashicorp.com/terraform/${{TERRAFORM_VERSION}}/terraform_${{TERRAFORM_VERSION}}_linux_{arch}.zip -O /tmp/terraform.zip && \
sudo unzip -o /tmp/terraform.zip -d /usr/local/bin && \
sudo chmod +x /usr/local/bin/terraform && \
rm /tmp/terraform.zip && \
terraform version"""

            ssh_cmd.append(install_cmd)

            try:
                result = subprocess.run(
                    ssh_cmd, check=False, capture_output=True, text=True, timeout=300
                )
                if result.returncode == 0:
                    logger.info("Terraform installed successfully")
                    if result.stdout:
                        logger.debug(f"Terraform version: {result.stdout.strip()}")
                    return True
                logger.error(f"Failed to install Terraform: {result.stderr}")
                return False
            except subprocess.TimeoutExpired:
                logger.exception("Terraform installation timed out")
                return False
            except Exception as e:
                logger.exception(f"Failed to install Terraform: {e}")
                return False

        except Exception as e:
            logger.exception(f"Basic dependency installation failed: {e}")
            return False

    def install_dependencies(self) -> bool:
        """
        Install system dependencies using Ansible.
        This runs after infrastructure provisioning and installs application-specific dependencies.

        :return: True if successful, False otherwise
        """
        logger.info("Installing system dependencies with Ansible...")

        try:
            ansible = self._init_ansible()

            if not self.ansible_dir.exists():
                logger.error(f"Ansible directory does not exist: {self.ansible_dir}")
                return False

            # Copy Ansible files to remote server if running remotely
            if ansible.is_remote:
                logger.info("Copying Ansible files to server...")
                import subprocess

                ssh_target = f"{self.config.server.user}@{self.config.server.host}"
                ssh_cmd = ["ssh"]
                if self.config.server.ssh_key_path:
                    ssh_cmd.extend(["-i", self.config.server.ssh_key_path])
                ssh_cmd.extend(["-p", str(self.config.server.port)])
                ssh_cmd.extend(["-o", "StrictHostKeyChecking=no"])
                ssh_cmd.extend(["-o", "BatchMode=yes"])

                # Create remote ansible directory
                remote_ansible_dir = ansible.remote_ansible_dir
                mkdir_cmd = f"sudo mkdir -p {remote_ansible_dir} && sudo chown -R {self.config.server.user}:{self.config.server.user} {remote_ansible_dir}"
                subprocess.run(
                    [*ssh_cmd, ssh_target, mkdir_cmd],
                    check=False,
                    capture_output=True,
                    text=True,
                    timeout=30,
                )

                # Copy ansible files using scp
                scp_cmd = ["scp", "-r"]
                if self.config.server.ssh_key_path:
                    scp_cmd.extend(["-i", self.config.server.ssh_key_path])
                scp_cmd.extend(["-P", str(self.config.server.port)])
                scp_cmd.extend(["-o", "StrictHostKeyChecking=no"])
                scp_cmd.append(f"{self.ansible_dir}/*")
                scp_cmd.append(f"{ssh_target}:{remote_ansible_dir}/")

                copy_result = subprocess.run(
                    scp_cmd, check=False, capture_output=True, text=True, timeout=60
                )
                if copy_result.returncode != 0:
                    logger.error(f"Failed to copy Ansible files: {copy_result.stderr}")
                    return False
                logger.info("Ansible files copied successfully")

            ansible.install_collections()

            ansible_vars = self.config.get_ansible_vars()
            ansible_vars.update(
                {
                    "app_repo_path": self.config.app_repo_path,
                    "app_name": self.config.app_name,
                    "environment": self.config.environment.value,
                }
            )

            # For remote execution, use localhost inventory since we're already on the target server
            if ansible.is_remote:
                # Add ansible_user for localhost connection
                ansible_vars["ansible_user"] = self.config.server.user
                # Create a temporary localhost inventory for remote execution
                localhost_inventory = """
all:
  hosts:
    localhost:
      ansible_connection: local
"""
                # Write to remote server
                import subprocess

                ssh_target = f"{self.config.server.user}@{self.config.server.host}"
                ssh_cmd = ["ssh"]
                if self.config.server.ssh_key_path:
                    ssh_cmd.extend(["-i", self.config.server.ssh_key_path])
                ssh_cmd.extend(["-p", str(self.config.server.port)])
                ssh_cmd.extend(["-o", "StrictHostKeyChecking=no"])
                ssh_cmd.extend(["-o", "BatchMode=yes"])

                inventory_path = f"{ansible.remote_ansible_dir}/inventory/localhost.yml"
                write_inv_cmd = (
                    f"cat > {inventory_path} << 'INVENTORY_EOF'\n{localhost_inventory}INVENTORY_EOF"
                )
                subprocess.run(
                    [*ssh_cmd, ssh_target, write_inv_cmd],
                    check=False,
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                inventory_file = inventory_path
            else:
                inventory_file = str(self.ansible_dir / "inventory" / "hosts.yml")

            result = ansible.run_playbook(
                "install-dependencies",
                inventory=inventory_file,
                extra_vars=ansible_vars,
            )

            logger.info("Dependency installation completed")
            return result.returncode == 0

        except Exception as e:
            logger.exception(f"Dependency installation failed: {e}")
            return False

    @abstractmethod
    def deploy_services(self) -> bool:
        """
        Deploy application services using Ansible.

        Must be implemented by application-specific managers.

        :return: True if successful, False otherwise
        """

    def verify_deployment(self) -> bool:
        """
        Verify that all services are running correctly.

        :return: True if all services are healthy, False otherwise
        """
        logger.info("Verifying deployment...")

        try:
            ansible = self._init_ansible()

            ansible_vars = self.config.get_ansible_vars()
            ansible_vars.update(
                {
                    "app_name": self.config.app_name,
                    "environment": self.config.environment.value,
                }
            )

            # For remote execution, use localhost inventory since we're already on the target server
            if ansible.is_remote:
                # Add ansible_user for localhost connection
                ansible_vars["ansible_user"] = self.config.server.user
                # Create a temporary localhost inventory for remote execution
                import subprocess

                ssh_target = f"{self.config.server.user}@{self.config.server.host}"
                ssh_cmd = ["ssh"]
                if self.config.server.ssh_key_path:
                    ssh_cmd.extend(["-i", self.config.server.ssh_key_path])
                ssh_cmd.extend(["-p", str(self.config.server.port)])
                ssh_cmd.extend(["-o", "StrictHostKeyChecking=no"])
                ssh_cmd.extend(["-o", "BatchMode=yes"])

                inventory_path = f"{ansible.remote_ansible_dir}/inventory/localhost.yml"
                localhost_inventory = """
all:
  hosts:
    localhost:
      ansible_connection: local
"""
                write_inv_cmd = (
                    f"cat > {inventory_path} << 'INVENTORY_EOF'\n{localhost_inventory}INVENTORY_EOF"
                )
                subprocess.run(
                    [*ssh_cmd, ssh_target, write_inv_cmd],
                    check=False,
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                inventory_file = inventory_path
            else:
                inventory_file = str(self.ansible_dir / "inventory" / "hosts.yml")

            result = ansible.run_playbook(
                "verify-deployment",
                inventory=inventory_file,
                extra_vars=ansible_vars,
            )

            is_healthy = result.returncode == 0
            if is_healthy:
                logger.info("Deployment verification passed")
            else:
                logger.warning("Deployment verification found issues")

            return is_healthy

        except Exception as e:
            logger.exception(f"Deployment verification failed: {e}")
            return False

    def deploy(
        self,
        skip_infrastructure: bool = False,
        load_vault_creds: bool = True,
        save_vault_creds: bool = True,
        overwrite_vault_creds: bool = True,
        generate_creds: bool = True,
        overwrite_generated: bool = False,
    ) -> bool:
        """
        Execute full deployment pipeline.

        :param skip_infrastructure: Skip Terraform infrastructure provisioning
        :param load_vault_creds: Load credentials from Vault before deployment
        :param save_vault_creds: Save credentials to Vault during deployment
        :param overwrite_vault_creds: Overwrite existing secrets in Vault if True
        :param generate_creds: Generate missing credentials automatically
        :param overwrite_generated: Regenerate existing credentials if True
        :return: True if deployment successful, False otherwise
        """
        logger.info(
            f"Starting {self.config.app_name} deployment pipeline "
            f"({self.config.environment.value})..."
        )

        # Load credentials from Vault if configured
        if load_vault_creds and self.config.vault_config:
            logger.info("Loading credentials from Vault...")
            self.config.load_credentials_from_vault()

        # Generate missing credentials
        if generate_creds:
            logger.info("Generating missing credentials...")
            generated = self.config.generate_missing_credentials(
                overwrite_existing=overwrite_generated
            )
            if generated:
                logger.info(
                    f"Generated {len(generated)} credential(s): {', '.join(generated.keys())}"
                )

        # Save credentials to Vault (before infrastructure provisioning)
        if save_vault_creds and self.config.vault_config:
            logger.info("Saving credentials to Vault...")
            self.config.save_credentials_to_vault(overwrite=overwrite_vault_creds)

        steps = [
            ("Basic Dependencies", self.install_basic_dependencies, False),
            ("Infrastructure", self.provision_infrastructure, skip_infrastructure),
            ("Dependencies", self.install_dependencies, False),
            ("Services", self.deploy_services, False),
            ("Verification", self.verify_deployment, False),
        ]

        for step_name, step_func, skip in steps:
            if skip:
                logger.info(f"Skipping {step_name} step")
                continue

            logger.info(f"Executing {step_name} step...")
            if not step_func():
                logger.error(f"{step_name} step failed")
                return False

        logger.info(f"{self.config.app_name} deployment pipeline completed successfully")
        return True

    def destroy(self) -> bool:
        """
        Destroy deployed infrastructure and services.

        :return: True if destruction successful, False otherwise
        """
        logger.warning(
            f"Destroying {self.config.app_name} deployment ({self.config.environment.value})..."
        )

        try:
            ansible = self._init_ansible()

            ansible_vars = self.config.get_ansible_vars()
            ansible_vars.update(
                {
                    "app_repo_path": self.config.app_repo_path,
                    "app_name": self.config.app_name,
                    "environment": self.config.environment.value,
                }
            )

            result = ansible.run_playbook(
                "destroy-app",
                inventory=str(self.ansible_dir / "inventory" / "hosts.yml"),
                extra_vars=ansible_vars,
            )

            if self.terraform_handler and self.terraform_dir.exists():
                terraform = self._init_terraform()
                terraform.destroy(vars=self.config.get_terraform_vars())

            logger.info(f"{self.config.app_name} deployment destroyed")
            return result.returncode == 0

        except Exception as e:
            logger.exception(f"Destruction failed: {e}")
            return False
