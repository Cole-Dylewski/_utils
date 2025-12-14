"""
Check Vault secrets using VaultHandler.

This script uses VaultHandler to check if secrets exist in Vault,
including the Tailscale auth key.
"""

import argparse
import logging
import os
import sys
from pathlib import Path

# Add the parent directory to sys.path to allow importing _utils
sys.path.insert(0, str(Path(__file__).parent.parent))

from _utils.server_management.vault import VaultHandler
from _utils.server_management.vault_auto_config import (
    auto_configure_vault,
    detect_vault_addr_via_tailscale,
    retrieve_vault_token_from_server,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def check_tailscale_key(
    vault_addr: str = None,
    vault_token: str = None,
    server_host: str = None,
    server_user: str = None,
    server_port: int = 22,
    ssh_key_path: str = None,
    vault_hostname: str = "chubcity-master.chub-city.ts.net",
) -> bool:
    """
    Check if Tailscale auth key exists in Vault.

    :param vault_addr: Vault server address
    :param vault_token: Vault token
    :param server_host: Server hostname for auto-detection
    :param server_user: Server user for auto-detection
    :param server_port: SSH port
    :param ssh_key_path: SSH key path
    :param vault_hostname: Tailscale hostname for Vault server
    :return: True if key exists, False otherwise
    """
    # Get vault_addr from environment, argument, or auto-detect
    if not vault_addr:
        vault_addr = os.getenv("VAULT_ADDR")
    
    # If still no vault_addr and server info provided, try auto-detection
    if not vault_addr and server_host and server_user:
        logger.info("Auto-detecting Vault address via Tailscale...")
        vault_addr = detect_vault_addr_via_tailscale(
            host=server_host,
            user=server_user,
            port=server_port,
            ssh_key_path=ssh_key_path,
            vault_hostname=vault_hostname,
        )
    
    if not vault_addr:
        logger.error("Vault address not found. Set VAULT_ADDR or provide server info.")
        return False

    # Get vault_token from environment, argument, or retrieve from server
    if not vault_token:
        vault_token = os.getenv("VAULT_TOKEN")
    
    # If still no token and server info provided, try retrieving from server
    if not vault_token and server_host and server_user:
        logger.info("Retrieving Vault token from server...")
        vault_token = retrieve_vault_token_from_server(
            host=server_host,
            user=server_user,
            port=server_port,
            ssh_key_path=ssh_key_path,
        )
    
    if not vault_token:
        logger.error("Vault token not found. Set VAULT_TOKEN or provide server info.")
        return False

    # Initialize Vault handler
    handler = VaultHandler(
        vault_addr=vault_addr,
        base_path="infra",
        vault_token=vault_token,
        vault_skip_verify=True,
    )

    # Connect to Vault
    client = handler.connect()
    if not client:
        logger.error("Failed to connect to Vault")
        return False

    logger.info(f"✓ Connected to Vault at {vault_addr}")

    # Check for Tailscale secret
    logger.info("Checking for Tailscale auth key at infra/tailscale...")
    secret = handler.get_secret("tailscale")
    
    if secret:
        logger.info("✓ Tailscale secret found!")
        if "auth_key" in secret:
            auth_key = secret["auth_key"]
            # Show first and last few characters for security
            if len(auth_key) > 20:
                masked_key = f"{auth_key[:10]}...{auth_key[-10:]}"
            else:
                masked_key = "***"
            logger.info(f"  auth_key: {masked_key} (length: {len(auth_key)})")
            logger.info(f"  Full key starts with: {auth_key[:15]}")
            return True
        else:
            logger.warning("  Secret found but 'auth_key' key not present")
            logger.info(f"  Keys in secret: {list(secret.keys())}")
            return False
    else:
        logger.warning("✗ Tailscale secret not found at infra/tailscale")
        return False


def list_infra_secrets(
    vault_addr: str = None,
    vault_token: str = None,
    server_host: str = None,
    server_user: str = None,
    server_port: int = 22,
    ssh_key_path: str = None,
    vault_hostname: str = "chubcity-master.chub-city.ts.net",
):
    """
    List all secrets under infra/ path.

    :param vault_addr: Vault server address
    :param vault_token: Vault token
    :param server_host: Server hostname for auto-detection
    :param server_user: Server user for auto-detection
    :param server_port: SSH port
    :param ssh_key_path: SSH key path
    :param vault_hostname: Tailscale hostname for Vault server
    """
    # Get vault_addr from environment, argument, or auto-detect
    if not vault_addr:
        vault_addr = os.getenv("VAULT_ADDR")
    
    if not vault_addr and server_host and server_user:
        logger.info("Auto-detecting Vault address via Tailscale...")
        vault_addr = detect_vault_addr_via_tailscale(
            host=server_host,
            user=server_user,
            port=server_port,
            ssh_key_path=ssh_key_path,
            vault_hostname=vault_hostname,
        )
    
    if not vault_addr:
        logger.error("Vault address not found. Set VAULT_ADDR or provide server info.")
        return

    # Get vault_token
    if not vault_token:
        vault_token = os.getenv("VAULT_TOKEN")
    
    if not vault_token and server_host and server_user:
        logger.info("Retrieving Vault token from server...")
        vault_token = retrieve_vault_token_from_server(
            host=server_host,
            user=server_user,
            port=server_port,
            ssh_key_path=ssh_key_path,
        )
    
    if not vault_token:
        logger.error("Vault token not found. Set VAULT_TOKEN or provide server info.")
        return

    # Initialize Vault handler
    handler = VaultHandler(
        vault_addr=vault_addr,
        base_path="infra",
        vault_token=vault_token,
        vault_skip_verify=True,
    )

    # Connect to Vault
    client = handler.connect()
    if not client:
        logger.error("Failed to connect to Vault")
        return

    logger.info(f"✓ Connected to Vault at {vault_addr}")
    logger.info("Listing secrets under infra/...")
    
    secrets = handler.list_secrets()
    if secrets:
        logger.info(f"Found {len(secrets)} secret(s):")
        for secret_name in secrets:
            logger.info(f"  - {secret_name}")
    else:
        logger.info("No secrets found under infra/")


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Check Vault secrets using VaultHandler",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Check Tailscale key with auto-detection
  python tasks/check_vault_secrets.py --check-tailscale --server-host demobox --server-user cole

  # List all infra secrets
  python tasks/check_vault_secrets.py --list-infra --server-host demobox --server-user cole

  # With environment variables
  export VAULT_ADDR=https://vault.example.com:8200
  export VAULT_TOKEN=your-token
  python tasks/check_vault_secrets.py --check-tailscale
        """,
    )

    parser.add_argument(
        "--check-tailscale",
        action="store_true",
        help="Check if Tailscale auth key exists in Vault",
    )
    parser.add_argument(
        "--list-infra",
        action="store_true",
        help="List all secrets under infra/ path",
    )

    # Vault configuration
    vault_group = parser.add_argument_group("Vault Configuration")
    vault_group.add_argument(
        "--vault-addr",
        help="Vault server address (defaults to VAULT_ADDR env var)",
    )
    vault_group.add_argument(
        "--vault-token",
        help="Vault token (defaults to VAULT_TOKEN env var)",
    )
    vault_group.add_argument(
        "--vault-hostname",
        default="chubcity-master.chub-city.ts.net",
        help="Tailscale hostname for Vault server",
    )

    # Server configuration (for auto-detection)
    server_group = parser.add_argument_group("Server Configuration (for auto-detection)")
    server_group.add_argument(
        "--server-host",
        help="Server hostname for auto-detection",
    )
    server_group.add_argument(
        "--server-user",
        help="Server user for auto-detection",
    )
    server_group.add_argument(
        "--server-port",
        type=int,
        default=22,
        help="SSH port (default: 22)",
    )
    server_group.add_argument(
        "--ssh-key-path",
        help="Path to SSH private key",
    )

    args = parser.parse_args()

    if not args.check_tailscale and not args.list_infra:
        parser.error("Must specify --check-tailscale or --list-infra")

    try:
        if args.check_tailscale:
            exists = check_tailscale_key(
                vault_addr=args.vault_addr,
                vault_token=args.vault_token,
                server_host=args.server_host,
                server_user=args.server_user,
                server_port=args.server_port,
                ssh_key_path=args.ssh_key_path,
                vault_hostname=args.vault_hostname,
            )
            return 0 if exists else 1
        elif args.list_infra:
            list_infra_secrets(
                vault_addr=args.vault_addr,
                vault_token=args.vault_token,
                server_host=args.server_host,
                server_user=args.server_user,
                server_port=args.server_port,
                ssh_key_path=args.ssh_key_path,
                vault_hostname=args.vault_hostname,
            )
            return 0

    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())

