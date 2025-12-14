"""
Server Management utilities for infrastructure automation.
"""

from _utils.server_management.terraform import TerraformHandler
from _utils.server_management.ansible import AnsibleHandler
from _utils.server_management.coder import CoderHandler
from _utils.server_management.vault import VaultHandler
from _utils.server_management.vault_auto_config import (
    auto_configure_vault,
    detect_vault_addr_via_tailscale,
    retrieve_vault_token_from_server,
)
from _utils.server_management.app_deployment import (
    AppDeploymentConfig,
    AppDeploymentManager,
    ServerConfig,
    Credentials,
    EnvironmentType,
    VaultConfig,
)
from _utils.server_management.app_registry import AppRegistry
from _utils.server_management.credential_generator import CredentialGenerator
from _utils.server_management.gpu_utils import (
    detect_gpu_memory_via_ssh,
    allocate_gpu_memory,
    allocate_gpu_memory_for_vllm_instances,
)
from _utils.server_management.ipsa import (
    IPSAAppConfig,
    IPSADeploymentManager,
)

__all__ = [
    'TerraformHandler',
    'AnsibleHandler',
    'CoderHandler',
    'VaultHandler',
    'auto_configure_vault',
    'detect_vault_addr_via_tailscale',
    'retrieve_vault_token_from_server',
    'AppDeploymentConfig',
    'AppDeploymentManager',
    'ServerConfig',
    'Credentials',
    'EnvironmentType',
    'VaultConfig',
    'AppRegistry',
    'CredentialGenerator',
    'detect_gpu_memory_via_ssh',
    'allocate_gpu_memory',
    'allocate_gpu_memory_for_vllm_instances',
    'IPSAAppConfig',
    'IPSADeploymentManager',
]

