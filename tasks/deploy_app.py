"""
Application Deployment Task

General-purpose entry point for deploying applications on Linux servers.
Supports multiple applications, environments, and idempotent operations.
"""

import argparse
import logging
import sys
from pathlib import Path

# Add the parent directory to sys.path to allow importing _utils
sys.path.insert(0, str(Path(__file__).parent.parent))

from _utils.server_management.app_deployment import (
    ServerConfig,
    Credentials,
    EnvironmentType,
    VaultConfig,
)
from _utils.server_management.app_registry import AppRegistry

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Deploy applications on Linux servers using Terraform and Ansible",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Minimal deployment (Vault auto-detected, repo URL from app selection)
  %(prog)s --app ipsa --server-host demo.example.com --server-user ubuntu \\
    --environment demo

  # Deploy specific branch
  %(prog)s --app ipsa --server-host demo.example.com --server-user ubuntu \\
    --environment demo --app-repo-branch develop

  # Deploy to production with custom ports (vLLM enabled by default)
  %(prog)s --app ipsa --server-host prod.example.com --server-user deploy \\
    --environment prod \\
    --backend-port 8000 --frontend-port 8080

  # Deploy with Tailscale (auth key retrieved from Vault automatically)
  %(prog)s --app ipsa --server-host demo.example.com --server-user ubuntu \\
    --environment demo \\
    --enable-tailscale

  # Override repository URL (if using fork or different repo)
  %(prog)s --app ipsa --server-host demo.example.com --server-user ubuntu \\
    --environment demo \\
    --app-repo-url https://github.com/your-org/ipsa-fork.git

  # Manual Vault configuration (if auto-detection fails)
  %(prog)s --app ipsa --server-host demo.example.com --server-user ubuntu \\
    --environment demo \\
    --vault-addr https://vault.example.com:8200 \\
    --vault-token your-vault-token

  # Destroy deployment
  %(prog)s --app ipsa --server-host demo.example.com --server-user ubuntu \\
    --environment demo --destroy
        """,
    )

    # Application selection
    parser.add_argument(
        "--app",
        required=True,
        choices=AppRegistry.list_apps(),
        help=f"Application to deploy (choices: {', '.join(AppRegistry.list_apps())})",
    )

    # Server configuration
    server_group = parser.add_argument_group("Server Configuration")
    server_group.add_argument(
        "--server-host",
        required=True,
        help="Server hostname or IP address",
    )
    server_group.add_argument(
        "--server-user",
        required=True,
        help="SSH user for server access",
    )
    server_group.add_argument(
        "--server-port",
        type=int,
        default=22,
        help="SSH port (default: 22)",
    )
    server_group.add_argument(
        "--ssh-key-path",
        help="Path to SSH private key (default: ~/.ssh/id_rsa)",
    )

    # Environment
    parser.add_argument(
        "--environment",
        required=True,
        choices=[e.value for e in EnvironmentType],
        help="Deployment environment (demo, staging, prod, dev)",
    )

    # Credentials (optional - auto-generated and stored in Vault)
    creds_group = parser.add_argument_group(
        "Credentials",
        "Credentials are automatically generated and stored in Vault. "
        "Only provide these if you need to override defaults."
    )
    creds_group.add_argument(
        "--api-key",
        action="append",
        metavar="KEY=VALUE",
        help="API key (can be specified multiple times, format: KEY=VALUE)",
    )
    creds_group.add_argument(
        "--secret",
        action="append",
        metavar="KEY=VALUE",
        help="Secret (can be specified multiple times, format: KEY=VALUE)",
    )

    # Vault configuration (optional - will auto-detect if not provided)
    vault_group = parser.add_argument_group(
        "Vault Configuration",
        "Vault configuration is auto-detected from server if not provided. "
        "Token is retrieved from terraform@chubcity-master at ~/.vault-root-token or can be provided manually."
    )
    vault_group.add_argument(
        "--vault-addr",
        help="Vault server address (auto-detected via Tailscale if not provided)",
    )
    vault_group.add_argument(
        "--vault-token",
        help="Vault authentication token (auto-retrieved from server if not provided)",
    )
    vault_group.add_argument(
        "--vault-base-path",
        default="ipsa",
        help="Base path for secrets in Vault (default: ipsa)",
    )
    vault_group.add_argument(
        "--vault-hostname",
        default="chubcity-master.chub-city.ts.net",
        help="Vault hostname on Tailscale network (default: chubcity-master.chub-city.ts.net)",
    )
    vault_group.add_argument(
        "--vault-token-host",
        default="chubcity-master",
        help="Host where Vault token is stored (default: chubcity-master)",
    )
    vault_group.add_argument(
        "--vault-token-user",
        default="terraform",
        help="User on Vault token host (default: terraform)",
    )

    # Application repository (optional - defaults from app selection)
    repo_group = parser.add_argument_group(
        "Repository Configuration",
        "Repository URL is automatically determined from app selection. "
        "Only override if using a different repository."
    )
    repo_group.add_argument(
        "--app-repo-url",
        help="Application repository URL (default: app-specific repository)",
    )
    repo_group.add_argument(
        "--app-repo-branch",
        default="main",
        help="Application repository branch (default: main)",
    )
    repo_group.add_argument(
        "--app-repo-path",
        help="Path on server for application code (default: app-specific)",
    )

    # Infrastructure paths
    infra_group = parser.add_argument_group("Infrastructure Paths")
    infra_group.add_argument(
        "--terraform-dir",
        help="Path to Terraform project directory (default: app-specific)",
    )
    infra_group.add_argument(
        "--ansible-dir",
        help="Path to Ansible project directory (default: app-specific)",
    )

    # Deployment options
    deploy_group = parser.add_argument_group("Deployment Options")
    deploy_group.add_argument(
        "--skip-infrastructure",
        action="store_true",
        help="Skip Terraform infrastructure provisioning",
    )
    deploy_group.add_argument(
        "--destroy",
        action="store_true",
        help="Destroy deployment instead of creating it",
    )
    deploy_group.add_argument(
        "--save-to-vault",
        action="store_true",
        default=True,
        help="Save credentials to Vault during deployment (default: True, use --no-save-to-vault to disable)",
    )
    deploy_group.add_argument(
        "--no-save-to-vault",
        dest="save_to_vault",
        action="store_false",
        help="Do not save credentials to Vault",
    )
    deploy_group.add_argument(
        "--overwrite-vault",
        action="store_true",
        default=True,
        help="Overwrite existing secrets in Vault (default: True)",
    )
    deploy_group.add_argument(
        "--no-overwrite-vault",
        dest="overwrite_vault",
        action="store_false",
        help="Do not overwrite existing secrets in Vault",
    )
    deploy_group.add_argument(
        "--skip-load-vault",
        action="store_true",
        help="Skip loading credentials from Vault (use only provided credentials)",
    )
    deploy_group.add_argument(
        "--no-generate-creds",
        dest="generate_creds",
        action="store_false",
        default=True,
        help="Do not generate missing credentials automatically",
    )
    deploy_group.add_argument(
        "--regenerate-creds",
        action="store_true",
        help="Regenerate all credentials (overwrites existing)",
    )

    # GPU Configuration (for IPSA and other GPU-enabled apps)
    gpu_group = parser.add_argument_group(
        "GPU Configuration",
        "vLLM services are enabled by default for IPSA deployments. "
        "If GPU memory limits are not specified, they will be auto-detected and allocated "
        "automatically (80% to AI services, 20% to others)."
    )
    gpu_group.add_argument(
        "--disable-vllm",
        dest="enable_vllm",
        action="store_false",
        help="Disable vLLM services (not recommended - vLLM is required for full functionality)",
    )
    gpu_group.add_argument(
        "--gpu-device-id",
        default="0",
        help="GPU device ID to use (default: 0)",
    )
    gpu_group.add_argument(
        "--backend-gpu-memory-gb",
        type=float,
        help="GPU memory limit for backend service in GB (auto-detected if not specified)",
    )
    gpu_group.add_argument(
        "--ingest-gpu-memory-gb",
        type=float,
        help="GPU memory limit for ingest service in GB (auto-detected if not specified)",
    )
    gpu_group.add_argument(
        "--vllm-gpu-memory-gb",
        type=float,
        help="GPU memory limit for vLLM service in GB (auto-detected if not specified)",
    )

    # Tailscale Configuration
    tailscale_group = parser.add_argument_group(
        "Tailscale Configuration",
        "Tailscale auth key is automatically retrieved from Vault during deployment."
    )
    tailscale_group.add_argument(
        "--enable-tailscale",
        action="store_true",
        default=True,
        help="Enable Tailscale for service access (default: True)",
    )
    tailscale_group.add_argument(
        "--disable-tailscale",
        dest="enable_tailscale",
        action="store_false",
        help="Disable Tailscale",
    )

    # Application-specific arguments (will be passed through)
    parser.add_argument(
        "--app-arg",
        action="append",
        metavar="KEY=VALUE",
        help="Application-specific argument (can be specified multiple times)",
    )
    
    # Deployment options
    parser.add_argument(
        "--skip-validation",
        action="store_true",
        help="Skip pre-deployment server validation (not recommended)",
    )

    return parser.parse_args()


def parse_key_value_args(args: list[str]) -> dict[str, str]:
    """
    Parse KEY=VALUE format arguments.

    :param args: List of KEY=VALUE strings
    :return: Dictionary of parsed key-value pairs
    """
    result = {}
    if not args:
        return result

    for arg in args:
        if "=" not in arg:
            logger.warning(f"Invalid format for argument: {arg} (expected KEY=VALUE)")
            continue
        key, value = arg.split("=", 1)
        result[key] = value

    return result


def create_config_from_args(args: argparse.Namespace) -> object:
    """
    Create application configuration from command line arguments.

    :param args: Parsed command line arguments
    :return: Application configuration object
    """
    config_class = AppRegistry.get_config_class(args.app)
    if not config_class:
        raise ValueError(f"Unknown application: {args.app}")

    server = ServerConfig(
        host=args.server_host,
        user=args.server_user,
        port=args.server_port,
        ssh_key_path=args.ssh_key_path,
    )

    api_keys = parse_key_value_args(args.api_key or [])
    secrets = parse_key_value_args(args.secret or [])
    app_args = parse_key_value_args(args.app_arg or [])

    # Auto-configure Vault if not explicitly provided
    vault_config = None
    if args.vault_addr or args.vault_token:
        # Explicit Vault configuration provided
        vault_config = VaultConfig(
            vault_addr=args.vault_addr or "",
            base_path=args.vault_base_path,
            vault_token=args.vault_token,
            vault_host=args.vault_host,
            token_path=args.vault_token_path,
        )
    else:
        # Auto-detect Vault configuration from server
        logger.info("Auto-detecting Vault configuration from server...")
        from _utils.server_management.vault_auto_config import auto_configure_vault
        
        vault_addr, vault_token = auto_configure_vault(
            host=args.server_host,
            user=args.server_user,
            port=args.server_port,
            ssh_key_path=args.ssh_key_path,
            base_path=args.vault_base_path,
            vault_hostname=getattr(args, "vault_hostname", None),
            vault_token_host=getattr(args, "vault_token_host", None),
            vault_token_user=getattr(args, "vault_token_user", None),
        )
        
        if vault_addr:
            vault_config = VaultConfig(
                vault_addr=vault_addr,
                base_path=args.vault_base_path,
                vault_token=vault_token,
            )
            if vault_token:
                logger.info("[OK] Vault configuration auto-detected successfully")
            else:
                logger.warning("⚠ Vault address detected but token not found.")
                logger.warning(f"  Token should be in: ~/.vault-root-token on terraform@chubcity-master")
                logger.warning("  Deployment will attempt to retrieve token during Vault operations.")
        else:
            logger.error("✗ Could not auto-detect Vault configuration.")
            logger.error("  Please provide --vault-addr and --vault-token manually, or ensure:")
            logger.error("  1. Tailscale is installed and configured on the server")
            logger.error("  2. Vault is accessible via Tailscale network")
            logger.error("  3. Vault token is available at ~/.vault-root-token on terraform@chubcity-master")

    # Credentials are auto-generated, so start with empty credentials
    credentials = Credentials(
        database_password="",  # Will be auto-generated
        api_keys=api_keys,
        secrets=secrets,
    )

    environment = EnvironmentType(args.environment)

    # Use provided values or defaults
    # Path defaults to /opt/{app_name} if not provided
    default_path = args.app_repo_path if hasattr(args, "app_repo_path") and args.app_repo_path else f"/opt/{args.app}"
    
    # Create temporary config instance to get app-specific defaults
    # This allows us to use the default repo URL from the app config
    temp_config = config_class(
        server=server,
        credentials=credentials,
        environment=environment,
        app_name=args.app,
        app_repo_path=default_path,  # Provide path to avoid validation error
        vault_config=vault_config,
    )
    
    # Use provided values or defaults from app config
    config_kwargs = {
        "server": server,
        "credentials": credentials,
        "environment": environment,
        "app_name": args.app,
        "app_repo_url": args.app_repo_url if args.app_repo_url else temp_config.app_repo_url,
        "app_repo_branch": args.app_repo_branch if args.app_repo_branch else temp_config.app_repo_branch,
        "app_repo_path": temp_config.app_repo_path,  # Use from temp_config (which has default from IPSAAppConfig)
        "vault_config": vault_config,
        "terraform_dir": args.terraform_dir,
        "ansible_dir": args.ansible_dir,
    }

    # Add GPU configuration if provided
    if hasattr(args, "gpu_device_id") and args.gpu_device_id:
        config_kwargs["gpu_device_id"] = args.gpu_device_id
    if hasattr(args, "backend_gpu_memory_gb") and args.backend_gpu_memory_gb:
        config_kwargs["backend_gpu_memory_gb"] = args.backend_gpu_memory_gb
    if hasattr(args, "ingest_gpu_memory_gb") and args.ingest_gpu_memory_gb:
        config_kwargs["ingest_gpu_memory_gb"] = args.ingest_gpu_memory_gb
    if hasattr(args, "vllm_gpu_memory_gb") and args.vllm_gpu_memory_gb:
        config_kwargs["vllm_gpu_memory_gb"] = args.vllm_gpu_memory_gb
    # vLLM is enabled by default, but can be disabled with --disable-vllm
    if hasattr(args, "enable_vllm"):
        config_kwargs["enable_vllm"] = args.enable_vllm
    
    # Add Tailscale configuration if provided
    if hasattr(args, "enable_tailscale"):
        config_kwargs["enable_tailscale"] = args.enable_tailscale
    # Tailscale auth key is retrieved from Vault during deployment, not from CLI

    config_kwargs.update(app_args)

    return config_class(**config_kwargs)


def main() -> int:
    """Main entry point for application deployment."""
    args = parse_args()

    # Skip validation if explicitly requested or if destroying
    if not args.skip_validation and not args.destroy:
        logger.info("Running pre-deployment server validation...")
        from _utils.server_management.app_deployment import ServerConfig
        
        server = ServerConfig(
            host=args.server_host,
            user=args.server_user,
            port=args.server_port,
            ssh_key_path=args.ssh_key_path,
        )
        
        # Import and run validation
        validate_script = Path(__file__).parent / "validate_server.py"
        if validate_script.exists():
            import importlib.util
            spec = importlib.util.spec_from_file_location("validate_server", validate_script)
            validate_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(validate_module)
            
            is_valid, errors = validate_module.validate_server(server, args.app)
            if not is_valid:
                logger.error("Server validation failed. Fix the issues above before deploying.")
                logger.error("To skip validation, use --skip-validation (not recommended)")
                return 1
            logger.info("Server validation passed. Proceeding with deployment...\n")
        else:
            logger.warning("Validation script not found, skipping validation")

    try:
        config = create_config_from_args(args)

        manager_class = AppRegistry.get_manager_class(args.app)
        if not manager_class:
            raise ValueError(f"No manager found for application: {args.app}")

        manager = manager_class(
            config=config,
            terraform_dir=args.terraform_dir,
            ansible_dir=args.ansible_dir,
        )

        if args.destroy:
            logger.info(f"Destroying {args.app} deployment ({args.environment})...")
            success = manager.destroy()
        else:
            logger.info(
                f"Deploying {args.app} to {args.environment} environment..."
            )
            success = manager.deploy(
                skip_infrastructure=args.skip_infrastructure,
                load_vault_creds=not args.skip_load_vault,
                save_vault_creds=args.save_to_vault,
                overwrite_vault_creds=args.overwrite_vault,
                generate_creds=args.generate_creds,
                overwrite_generated=args.regenerate_creds,
            )

        if success:
            logger.info("Deployment operation completed successfully")
            print("\n" + "="*80)
            print("DEPLOYMENT COMPLETED SUCCESSFULLY")
            print("="*80 + "\n")
            
            # Print service diagnostics
            if hasattr(manager, 'print_service_diagnostics'):
                try:
                    manager.print_service_diagnostics()
                except Exception as e:
                    logger.warning(f"Failed to print service diagnostics: {e}")
        else:
            logger.error("Deployment operation failed")
            print("\n" + "="*80)
            print("DEPLOYMENT FAILED")
            print("="*80 + "\n")
            
            # Print diagnostics even on failure
            if hasattr(manager, 'print_service_diagnostics'):
                try:
                    logger.info("Gathering service diagnostics...")
                    manager.print_service_diagnostics()
                except Exception as e:
                    logger.warning(f"Failed to print service diagnostics: {e}")

        # Flush all output to ensure it's written
        import sys
        sys.stdout.flush()
        sys.stderr.flush()
        
        return 0 if success else 1

    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        print("\n" + "="*80)
        print(f"CONFIGURATION ERROR: {e}")
        print("="*80 + "\n")
        sys.stdout.flush()
        sys.stderr.flush()
        return 1
    except KeyboardInterrupt:
        logger.warning("Deployment interrupted by user")
        print("\n" + "="*80)
        print("DEPLOYMENT INTERRUPTED BY USER")
        print("="*80 + "\n")
        sys.stdout.flush()
        sys.stderr.flush()
        return 130
    except Exception as e:
        logger.error(f"Deployment failed: {e}", exc_info=True)
        print("\n" + "="*80)
        print(f"DEPLOYMENT FAILED: {e}")
        print("="*80 + "\n")
        sys.stdout.flush()
        sys.stderr.flush()
        return 1


if __name__ == "__main__":
    try:
        exit_code = main()
        # Final flush and explicit exit
        sys.stdout.flush()
        sys.stderr.flush()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nDeployment interrupted. Exiting...")
        sys.stdout.flush()
        sys.stderr.flush()
        sys.exit(130)

