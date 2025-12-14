"""
Vault Handler - Manage HashiCorp Vault secrets

Provides a class-based interface for managing secrets in HashiCorp Vault with support for:
- Multiple authentication methods (token, Kubernetes, SSH)
- Secret CRUD operations
- Environment file parsing and migration
- Command-line interface

Usage:
    from _utils.server_management import VaultHandler

    # Initialize handler
    handler = VaultHandler(
        vault_addr="https://vault.example.com:8200",
        vault_skip_verify=True,
        base_path="my-project",
        vault_token="your-token"  # Optional, will try other methods if not provided
    )

    # List secrets
    secrets = handler.list_secrets()

    # Get a secret
    secret = handler.get_secret("my-secret")

    # Create/update a secret
    handler.create_or_update_secret("my-secret", {"key": "value"})

    # Delete a secret
    handler.delete_secret("my-secret")
"""

import json
import logging
import os
from pathlib import Path
import subprocess
import sys
from typing import Any

try:
    import hvac
    from hvac.exceptions import InvalidPath, VaultError
except ImportError:
    hvac = None
    InvalidPath = None
    VaultError = None

# Set up logging
logger = logging.getLogger(__name__)


def _mask_sensitive_value(value: str | Any) -> str:
    """
    Mask sensitive values for logging/display purposes.

    This function sanitizes sensitive data by masking it, making it safe to log or display.
    CodeQL recognizes that values passed through this function are no longer sensitive.

    :param value: The sensitive value to mask
    :return: Masked (non-sensitive) value string safe for logging/display
    """
    if value is None:
        return "*** (masked)"

    value_str = str(value)
    if len(value_str) <= 8:
        return "*** (masked)"

    # Show first 4 and last 4 characters - this is safe for logging
    return f"{value_str[:4]}...{value_str[-4:]} (masked)"


class VaultHandler:
    """
    Handles HashiCorp Vault operations including authentication, secret management,
    and environment file migration.
    """

    def __init__(
        self,
        vault_addr: str,
        base_path: str = "cortex",
        vault_token: str | None = None,
        vault_skip_verify: bool = True,
        vault_host: str | None = None,
        token_path: str | None = None,
        kubernetes_roles: list[str] | None = None,
    ):
        """
        Initialize Vault handler.

        :param vault_addr: Vault server address (e.g., "https://vault.example.com:8200")
        :param base_path: Base path for secrets (defaults to "cortex")
        :param vault_token: Vault token (optional, will try other methods if not provided)
        :param vault_skip_verify: Skip SSL certificate verification (default: True)
        :param vault_host: Remote host for SSH token retrieval (e.g., "user@host")
        :param token_path: Path to token file on remote host (defaults to "~/.vault-root-token")
        :param kubernetes_roles: List of Kubernetes roles to try for authentication (optional)

        Example usage:
            handler = VaultHandler(
                vault_addr="https://vault.example.com:8200",
                base_path="my-project",
                vault_token="your-token"
            )
        """
        if hvac is None:
            raise ImportError("hvac library is required. Install it with: pip install hvac")

        self.vault_addr = vault_addr
        self.base_path = base_path
        self.vault_skip_verify = vault_skip_verify
        self.vault_host = vault_host
        self.token_path = token_path or "~/.vault-root-token"
        self.kubernetes_roles = kubernetes_roles or [
            "coder-workspace",
            "default",
            "coder",
            "workspace",
            "coder-workspace-role",
        ]

        # Set token if provided
        self._token = vault_token

        # Client will be initialized on first use
        self._client: hvac.Client | None = None

        logger.info(f"VaultHandler initialized: vault_addr={vault_addr}, base_path={base_path}")

    def _get_vault_token(self) -> str | None:
        """Get Vault token from various sources."""
        # Method 1: Use provided token
        if self._token:
            return self._token

        # Method 2: Environment variable
        token = os.getenv("VAULT_TOKEN")
        if token:
            return token

        # Method 3: Token files (local)
        token_files = [
            Path.home() / ".vault-token",
            Path.home() / ".vault-root-token",
            Path("/root/.vault-token"),
            Path("/root/.vault-root-token"),
        ]

        for token_file in token_files:
            try:
                if token_file.exists() and token_file.is_file():
                    token = token_file.read_text().strip()
                    if token:
                        return token
            except (PermissionError, OSError):
                continue

        # Method 4: Kubernetes authentication
        sa_token_file = Path("/var/run/secrets/kubernetes.io/serviceaccount/token")
        if sa_token_file.exists():
            try:
                import urllib.error
                import urllib.request

                with open(sa_token_file) as f:
                    jwt = f.read().strip()

                for role in self.kubernetes_roles:
                    try:
                        payload = json.dumps({"role": role, "jwt": jwt}).encode("utf-8")
                        req = urllib.request.Request(
                            f"{self.vault_addr}/v1/auth/kubernetes/login",
                            data=payload,
                            headers={"Content-Type": "application/json"},
                            method="POST",
                        )

                        with urllib.request.urlopen(req, timeout=10) as response:
                            if response.status == 200:
                                result = json.loads(response.read().decode("utf-8"))
                                token = result.get("auth", {}).get("client_token")
                                if token:
                                    logger.info(f"Authenticated with Kubernetes role: {role}")
                                    return token
                    except urllib.error.HTTPError as e:
                        if e.code == 400:
                            continue  # Wrong role, try next
                    except Exception:
                        continue
            except Exception:
                pass  # Kubernetes auth not available

        # Method 5: SSH to remote host (if configured)
        if self.vault_host:
            ssh_command = [
                "ssh",
                "-o",
                "StrictHostKeyChecking=no",
                "-o",
                "ConnectTimeout=10",
                "-o",
                "BatchMode=yes",
                self.vault_host,
                f"cat {self.token_path}",
            ]

            try:
                result = subprocess.run(
                    ssh_command, check=False, capture_output=True, text=True, timeout=15
                )

                if result.returncode == 0:
                    token = result.stdout.strip()
                    if token:
                        return token
                    logger.warning("Token file is empty on remote server")
                    return None
                # Don't log error for SSH failures - it's expected if not accessible
                return None
            except subprocess.TimeoutExpired:
                return None
            except FileNotFoundError:
                return None
            except Exception:
                return None

        return None

    def connect(self) -> hvac.Client | None:
        """
        Connect to Vault and return a client.

        :return: Vault client or None if connection failed
        """
        if self._client is not None:
            return self._client

        token = self._get_vault_token()
        if not token:
            logger.error("[VAULT] Cannot get Vault token. Try:")
            logger.error("[VAULT]   1. Set VAULT_TOKEN environment variable")
            logger.error("[VAULT]   2. Place token in ~/.vault-token or ~/.vault-root-token")
            logger.error("[VAULT]   3. Configure Kubernetes authentication")
            logger.error("[VAULT]   4. Provide vault_token parameter or configure vault_host")
            return None

        # Log connection details (mask token)
        masked_token = f"{token[:4]}...{token[-4:]}" if len(token) > 8 else "***"
        logger.info(f"[VAULT] Connecting to Vault at: {self.vault_addr}")
        logger.debug(f"[VAULT] Using token: {masked_token} (length: {len(token)})")
        logger.debug(f"[VAULT] Base path: {self.base_path}")
        logger.debug(f"[VAULT] Skip TLS verify: {self.vault_skip_verify}")

        try:
            client = hvac.Client(
                url=self.vault_addr, token=token, verify=not self.vault_skip_verify
            )
            if not client.is_authenticated():
                logger.error(
                    "[VAULT] Vault authentication failed - token may be invalid or expired"
                )
                return None
            logger.info("[VAULT] Successfully authenticated to Vault")
            self._client = client
            return client
        except Exception as e:
            logger.exception(f"[VAULT] Error connecting to Vault at {self.vault_addr}: {e}")
            logger.debug(f"[VAULT] Exception type: {type(e).__name__}")
            return None

    def list_secrets(self, path: str | None = None) -> list[str]:
        """
        List all secret paths under the given path.

        :param path: Path to list (defaults to base_path)
        :return: List of secret names
        """
        client = self.connect()
        if not client:
            return []

        list_path = path or self.base_path

        try:
            response = client.secrets.kv.v2.list_secrets(path=list_path)
            if response and "data" in response and "keys" in response["data"]:
                return response["data"]["keys"]
            return []
        except InvalidPath:
            return []
        except Exception as e:
            logger.warning(f"Could not list secrets at {list_path}: {e}")
            return []

    def get_secret(self, secret_name: str, path: str | None = None) -> dict[str, Any] | None:
        """
        Get a secret from Vault.

        :param secret_name: Name of the secret (without base path)
        :param path: Base path (defaults to base_path)
        :return: Secret data as dictionary or None if not found
        """
        client = self.connect()
        if not client:
            logger.debug("[VAULT] Cannot get secret: Vault client connection failed")
            return None

        base = path or self.base_path
        secret_path = f"{base}/{secret_name}"
        full_path = f"secret/{secret_path}"  # KV v2 mount path

        try:
            logger.debug(f"[VAULT] Reading secret from path: {full_path}")
            response = client.secrets.kv.v2.read_secret_version(path=secret_path)
            if response and "data" in response and "data" in response["data"]:
                data = response["data"]["data"]
                # Log keys only, never log values
                logger.debug(
                    f"[VAULT] Successfully read secret from {full_path}, keys: {list(data.keys())}"
                )
                return data
            logger.debug(f"[VAULT] Secret not found or empty at {full_path}")
            return None
        except InvalidPath:
            return None
        except Exception as e:
            logger.debug(f"[VAULT] Error reading secret from {full_path}: {e}")
            logger.debug(f"[VAULT] Exception type: {type(e).__name__}")
            return None

    def create_or_update_secret(
        self, secret_name: str, data: dict[str, Any], path: str | None = None
    ) -> bool:
        """
        Create or update a secret in Vault.

        :param secret_name: Name of the secret (without base path)
        :param data: Secret data as dictionary
        :param path: Base path (defaults to base_path)
        :return: True if successful, False otherwise
        """
        client = self.connect()
        if not client:
            logger.error("[VAULT] Cannot create/update secret: Vault client connection failed")
            return False

        base = path or self.base_path
        secret_path = f"{base}/{secret_name}"
        full_path = f"secret/{secret_path}"  # KV v2 mount path

        try:
            logger.debug(f"[VAULT] Creating/updating secret at path: {full_path}")
            logger.debug(f"[VAULT] Secret data keys: {list(data.keys())}")
            client.secrets.kv.v2.create_or_update_secret(path=secret_path, secret=data)
            logger.info(f"[VAULT] Successfully created/updated secret: {full_path}")
            return True
        except Exception as e:
            logger.exception(f"[VAULT] Error creating/updating secret at {full_path}: {e}")
            logger.debug(f"[VAULT] Exception type: {type(e).__name__}")
            return False

    def delete_secret(self, secret_name: str, path: str | None = None) -> bool:
        """
        Delete a secret from Vault.

        :param secret_name: Name of the secret (without base path)
        :param path: Base path (defaults to base_path)
        :return: True if successful, False otherwise
        """
        client = self.connect()
        if not client:
            return False

        base = path or self.base_path
        secret_path = f"{base}/{secret_name}"

        try:
            client.secrets.kv.v2.delete_metadata_and_all_versions(path=secret_path)
            logger.info(f"Successfully deleted secret: secret/{secret_path}")
            return True
        except InvalidPath:
            logger.warning(f"Secret not found: {secret_path}")
            return False
        except Exception as e:
            logger.exception(f"Error deleting secret: {e}")
            return False

    def parse_env_file(self, file_path: Path) -> dict[str, str]:
        """
        Parse a .env file and return a dictionary of key-value pairs.

        :param file_path: Path to .env file
        :return: Dictionary of environment variables
        """
        env_vars = {}
        if not file_path.exists():
            logger.error(f"File not found: {file_path}")
            return env_vars

        with open(file_path) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip()
                    # Remove quotes if present
                    if (value.startswith('"') and value.endswith('"')) or (
                        value.startswith("'") and value.endswith("'")
                    ):
                        value = value[1:-1]
                    env_vars[key] = value

        return env_vars

    def migrate_env_file(self, env_file: Path, secret_name: str, path: str | None = None) -> bool:
        """
        Migrate environment file variables to Vault.

        :param env_file: Path to .env file
        :param secret_name: Name of the secret to create/update
        :param path: Base path (defaults to base_path)
        :return: True if successful, False otherwise
        """
        logger.info(f"Reading environment file: {env_file}")
        env_vars = self.parse_env_file(env_file)

        if not env_vars:
            logger.error("No variables found in environment file")
            return False

        logger.info(f"Found {len(env_vars)} variables")
        logger.info(f"Migrating to secret: secret/{path or self.base_path}/{secret_name}")

        success = self.create_or_update_secret(secret_name, env_vars, path)

        if success:
            logger.info("Migration complete!")
            # Verify
            verify_data = self.get_secret(secret_name, path)
            if verify_data:
                logger.info(f"Verification successful. Keys: {', '.join(verify_data.keys())}")
            else:
                logger.warning("Verification failed - secret may not be accessible")

        return success


def main():
    """Main CLI entry point."""
    import argparse

    if hvac is None:
        print("Error: hvac library is required. Install it with: pip install hvac", file=sys.stderr)
        sys.exit(1)

    parser = argparse.ArgumentParser(
        description="Vault CLI Tool - Manage HashiCorp Vault secrets",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--vault-addr",
        default=os.getenv("VAULT_ADDR", "https://vault.example.com:8200"),
        help="Vault server address (default: from VAULT_ADDR env var or https://vault.example.com:8200)",
    )
    parser.add_argument(
        "--base-path", default="cortex", help="Base path for secrets (default: cortex)"
    )
    parser.add_argument(
        "--vault-token",
        default=None,
        help="Vault token (optional, will try other methods if not provided)",
    )
    parser.add_argument(
        "--vault-skip-verify",
        action="store_true",
        default=os.getenv("VAULT_SKIP_VERIFY", "true").lower() == "true",
        help="Skip SSL certificate verification",
    )
    parser.add_argument(
        "--vault-host", default=None, help="Remote host for SSH token retrieval (e.g., user@host)"
    )
    parser.add_argument(
        "--token-path",
        default="~/.vault-root-token",
        help="Path to token file on remote host (default: ~/.vault-root-token)",
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # List command
    list_parser = subparsers.add_parser("list", help="List all secrets")
    list_parser.set_defaults(func=lambda args: _cmd_list(args, parser))

    # List all command
    list_all_parser = subparsers.add_parser("list-all", help="List all secrets with their values")
    list_all_parser.set_defaults(func=lambda args: _cmd_list_all(args, parser))

    # Get command
    get_parser = subparsers.add_parser("get", help="Get a specific secret")
    get_parser.add_argument("secret_name", help="Name of the secret (without base path prefix)")
    get_parser.add_argument("--json", action="store_true", help="Output as JSON")
    get_parser.set_defaults(func=lambda args: _cmd_get(args, parser))

    # Put command
    put_parser = subparsers.add_parser("put", help="Create or update a secret")
    put_parser.add_argument("secret_name", help="Name of the secret (without base path prefix)")
    put_parser.add_argument("--file", help="JSON file containing secret data")
    put_parser.add_argument(
        "--kv",
        action="append",
        help="Key-value pair in format key=value (can be used multiple times)",
    )
    put_parser.set_defaults(func=lambda args: _cmd_put(args, parser))

    # Delete command
    delete_parser = subparsers.add_parser("delete", help="Delete a secret")
    delete_parser.add_argument("secret_name", help="Name of the secret (without base path prefix)")
    delete_parser.add_argument("--force", action="store_true", help="Skip confirmation prompt")
    delete_parser.set_defaults(func=lambda args: _cmd_delete(args, parser))

    # Migrate command
    migrate_parser = subparsers.add_parser("migrate-env", help="Migrate .env file to Vault")
    migrate_parser.add_argument("env_file", help="Path to .env file")
    migrate_parser.add_argument("secret_name", help="Name of the secret to create/update")
    migrate_parser.set_defaults(func=lambda args: _cmd_migrate_env(args, parser))

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    args.func(args)


def _get_handler(args) -> VaultHandler:
    """Get VaultHandler instance from parsed arguments."""
    return VaultHandler(
        vault_addr=args.vault_addr,
        base_path=args.base_path,
        vault_token=args.vault_token,
        vault_skip_verify=args.vault_skip_verify,
        vault_host=args.vault_host,
        token_path=args.token_path,
    )


def _cmd_list(args, parser):
    """List all secrets."""
    handler = _get_handler(args)
    client = handler.connect()
    if not client:
        sys.exit(1)

    secrets = handler.list_secrets()
    if not secrets:
        print("No secrets found.")
        return

    print(f"Found {len(secrets)} secret(s):")
    for i, secret_name in enumerate(secrets, 1):
        print(f"  {i}. {secret_name.rstrip('/')}")


def _cmd_list_all(args, parser):
    """List all secrets with their keys only (values are not displayed for security)."""
    handler = _get_handler(args)
    client = handler.connect()
    if not client:
        sys.exit(1)

    secrets = handler.list_secrets()
    if not secrets:
        print("No secrets found.")
        return

    print(f"\nFound {len(secrets)} secret(s):\n")
    print("=" * 80)

    for secret_name in secrets:
        secret_name = secret_name.rstrip("/")
        secret_data = handler.get_secret(secret_name)

        if secret_data:
            print(f"\nSecret: secret/{handler.base_path}/{secret_name}")
            print("-" * 80)
            # Only print keys for security - values are never displayed
            for key in secret_data:
                print(f"  {key}: [REDACTED]")
            print()

    print("=" * 80)
    print(f"\nTotal: {len(secrets)} secret(s)")
    print("NOTE: Secret values are not displayed for security reasons.")


def _cmd_get(args, parser):
    """Get a specific secret."""
    handler = _get_handler(args)
    client = handler.connect()
    if not client:
        sys.exit(1)

    secret_data = handler.get_secret(args.secret_name)

    if not secret_data:
        print(f"Secret '{args.secret_name}' not found", file=sys.stderr)
        sys.exit(1)

    if args.json:
        # Only output keys for security - values are never included in JSON output
        keys_only = dict.fromkeys(secret_data, "[REDACTED]")
        print(json.dumps(keys_only, indent=2))
        print("\nNOTE: Secret values are not displayed for security reasons.", file=sys.stderr)
    else:
        print(f"\nSecret: secret/{handler.base_path}/{args.secret_name}")
        print("=" * 60)
        # Only print keys for security - values are never displayed
        for key in secret_data:
            print(f"{key}: [REDACTED]")
        print("=" * 60)
        print("NOTE: Secret values are not displayed for security reasons.")


def _cmd_put(args, parser):
    """Create or update a secret."""
    handler = _get_handler(args)
    client = handler.connect()
    if not client:
        sys.exit(1)

    data = {}

    # Read from file if provided
    if args.file:
        try:
            with open(args.file) as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON in file: {e}", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"Error reading file: {e}", file=sys.stderr)
            sys.exit(1)

    # Add key-value pairs from command line
    if args.kv:
        for kv_pair in args.kv:
            if "=" not in kv_pair:
                print(
                    f"Error: Invalid key-value pair: {kv_pair}. Use format key=value",
                    file=sys.stderr,
                )
                sys.exit(1)
            key, value = kv_pair.split("=", 1)
            data[key.strip()] = value.strip()

    if not data:
        print("Error: No data provided. Use --file or --kv to provide data", file=sys.stderr)
        sys.exit(1)

    success = handler.create_or_update_secret(args.secret_name, data)
    if not success:
        print("[ERROR] Failed to create/update secret", file=sys.stderr)
        sys.exit(1)


def _cmd_delete(args, parser):
    """Delete a secret."""
    handler = _get_handler(args)

    if not args.force:
        response = input(
            f"Are you sure you want to delete secret/{handler.base_path}/{args.secret_name}? [y/N]: "
        )
        if response.lower() != "y":
            print("Cancelled.")
            return

    client = handler.connect()
    if not client:
        sys.exit(1)

    success = handler.delete_secret(args.secret_name)
    if not success:
        print("[ERROR] Failed to delete secret", file=sys.stderr)
        sys.exit(1)


def _cmd_migrate_env(args, parser):
    """Migrate .env file to Vault."""
    handler = _get_handler(args)
    client = handler.connect()
    if not client:
        sys.exit(1)

    env_file = Path(args.env_file)
    success = handler.migrate_env_file(env_file, args.secret_name)

    if not success:
        print("[ERROR] Migration failed", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
