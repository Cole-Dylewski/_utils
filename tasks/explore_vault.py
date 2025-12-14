"""
Explore Vault secrets using VaultHandler.

This script lists and retrieves secrets from Vault using the vault.py functions.
"""

import sys
from pathlib import Path

# Add the parent directory to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from _utils.server_management.vault import VaultHandler
from _utils.server_management.vault_auto_config import (
    auto_configure_vault,
    detect_vault_addr_via_tailscale,
    retrieve_vault_token_from_server,
)

def explore_vault(server_host="demobox", server_user="cole"):
    """Explore Vault secrets."""
    print("=" * 80)
    print("Exploring Vault Secrets")
    print("=" * 80)
    print()
    
    # Auto-detect Vault configuration
    print("1. Auto-detecting Vault configuration...")
    vault_addr, vault_token = auto_configure_vault(
        host=server_host,
        user=server_user,
        port=22,
        base_path="ipsa",
    )
    
    if not vault_addr:
        print("ERROR: Could not detect Vault address")
        return
    
    print(f"   ✓ Vault address: {vault_addr}")
    
    if not vault_token:
        print("   ⚠ Vault token not found on server")
        print("   Trying alternative methods...")
        # Try to get token from environment or files
        import os
        vault_token = os.getenv("VAULT_TOKEN")
        if not vault_token:
            print("   ERROR: Vault token required. Set VAULT_TOKEN or place token on server.")
            return
        print("   ✓ Using token from environment")
    else:
        print(f"   ✓ Vault token retrieved from server")
    
    print()
    
    # Initialize handler for root level
    print("2. Listing secrets at root level...")
    root_handler = VaultHandler(
        vault_addr=vault_addr,
        base_path="",
        vault_token=vault_token,
        vault_skip_verify=True,
    )
    
    root_secrets = root_handler.list_secrets("")
    if root_secrets:
        print(f"   Found {len(root_secrets)} top-level secret(s):")
        for secret in root_secrets:
            print(f"     - {secret.rstrip('/')}")
    else:
        print("   No secrets found at root level")
    
    print()
    
    # Check infra/tailscale
    print("3. Checking infra/tailscale...")
    infra_handler = VaultHandler(
        vault_addr=vault_addr,
        base_path="infra",
        vault_token=vault_token,
        vault_skip_verify=True,
    )
    
    infra_secrets = infra_handler.list_secrets()
    if infra_secrets:
        print(f"   Found {len(infra_secrets)} secret(s) under infra/:")
        for secret in infra_secrets:
            print(f"     - {secret.rstrip('/')}")
        
        # Get tailscale secret if it exists
        if "tailscale" in [s.rstrip("/") for s in infra_secrets]:
            print()
            print("   Retrieving tailscale secret...")
            tailscale_secret = infra_handler.get_secret("tailscale")
            if tailscale_secret:
                print("   ✓ Tailscale secret found:")
                for key, value in tailscale_secret.items():
                    if key == "auth_key":
                        # Mask the key for security
                        if len(value) > 20:
                            masked = f"{value[:10]}...{value[-10:]}"
                        else:
                            masked = "***"
                        print(f"     {key}: {masked} (length: {len(value)})")
                        print(f"     Full key starts with: {value[:15]}")
                    else:
                        print(f"     {key}: {value}")
            else:
                print("   ✗ Could not retrieve tailscale secret")
        else:
            print("   ✗ tailscale secret not found under infra/")
    else:
        print("   No secrets found under infra/")
    
    print()
    
    # Check ipsa secrets
    print("4. Checking ipsa secrets...")
    ipsa_handler = VaultHandler(
        vault_addr=vault_addr,
        base_path="ipsa",
        vault_token=vault_token,
        vault_skip_verify=True,
    )
    
    ipsa_secrets = ipsa_handler.list_secrets()
    if ipsa_secrets:
        print(f"   Found {len(ipsa_secrets)} secret(s) under ipsa/:")
        for secret in ipsa_secrets:
            print(f"     - {secret.rstrip('/')}")
        
        # Check demo environment
        if "demo" in [s.rstrip("/") for s in ipsa_secrets]:
            print()
            print("   Checking ipsa/demo/...")
            demo_secrets = ipsa_handler.list_secrets("demo")
            if demo_secrets:
                print(f"     Found {len(demo_secrets)} secret(s):")
                for secret in demo_secrets:
                    print(f"       - {secret.rstrip('/')}")
    else:
        print("   No secrets found under ipsa/")
    
    print()
    print("=" * 80)
    print("Exploration complete")
    print("=" * 80)

if __name__ == "__main__":
    explore_vault()

