"""
Server Management utilities for infrastructure automation.
"""

from server_management.ansible import AnsibleHandler
from server_management.app_deployment import (
    AppDeploymentConfig,
    AppDeploymentManager,
    Credentials,
    EnvironmentType,
    ServerConfig,
    VaultConfig,
)
from server_management.app_registry import AppRegistry
from server_management.coder import CoderHandler
from server_management.credential_generator import CredentialGenerator
from server_management.gpu_utils import (
    allocate_gpu_memory,
    allocate_gpu_memory_for_vllm_instances,
    detect_gpu_memory_via_ssh,
)
from server_management.ipsa import (
    IPSAAppConfig,
    IPSADeploymentManager,
)
from server_management.terraform import TerraformHandler
from server_management.vault import VaultHandler
from server_management.vault_auto_config import (
    auto_configure_vault,
    detect_vault_addr_via_tailscale,
    retrieve_vault_token_from_server,
)

__all__ = [
    "AnsibleHandler",
    "AppDeploymentConfig",
    "AppDeploymentManager",
    "AppRegistry",
    "CoderHandler",
    "CredentialGenerator",
    "Credentials",
    "EnvironmentType",
    "IPSAAppConfig",
    "IPSADeploymentManager",
    "ServerConfig",
    "TerraformHandler",
    "VaultConfig",
    "VaultHandler",
    "allocate_gpu_memory",
    "allocate_gpu_memory_for_vllm_instances",
    "auto_configure_vault",
    "detect_gpu_memory_via_ssh",
    "detect_vault_addr_via_tailscale",
    "retrieve_vault_token_from_server",
]
