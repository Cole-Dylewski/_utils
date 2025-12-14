"""
Server Diagnostic Task

Comprehensive diagnostic script that connects via SSH and performs a full
diagnostic of all services, configurations, and system health on a Linux server.
Supports application-specific diagnostics via modular diagnostic modules.
"""

import argparse
import logging
from pathlib import Path
import subprocess
import sys
from typing import Any

# Add parent directory to path to import _utils
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import diagnostic registry (this will auto-register IPSA diagnostic)
from _utils.server_management.diagnostics import DiagnosticRegistry

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def run_remote_command(
    host: str,
    user: str,
    command: str,
    port: int = 22,
    ssh_key_path: str | None = None,
    timeout: int = 30,
) -> tuple[int, str, str]:
    """
    Run a command on remote server via SSH.

    :param host: Server hostname or IP
    :param user: SSH user
    :param command: Command to run
    :param port: SSH port
    :param ssh_key_path: Path to SSH private key
    :param timeout: Command timeout in seconds
    :return: Tuple of (returncode, stdout, stderr)
    """
    ssh_cmd = [
        "ssh",
        "-p",
        str(port),
        "-o",
        "StrictHostKeyChecking=no",
        "-o",
        "ConnectTimeout=10",
    ]

    if ssh_key_path:
        ssh_cmd.extend(["-i", ssh_key_path])

    ssh_cmd.append(f"{user}@{host}")
    ssh_cmd.append(command)

    try:
        result = subprocess.run(
            ssh_cmd,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return 1, "", f"Command timed out after {timeout}s"
    except Exception as e:
        return 1, "", str(e)


def check_system_info(host: str, user: str, port: int, ssh_key_path: str | None) -> dict[str, str]:
    """Check basic system information."""
    logger.info("=== System Information ===")

    info = {}
    commands = {
        "hostname": "hostname",
        "os_release": (
            "cat /etc/os-release 2>/dev/null | grep -E '^(NAME|VERSION)=' || "
            "cat /etc/redhat-release 2>/dev/null || echo 'Unknown'"
        ),
        "kernel": "uname -r",
        "arch": "uname -m",
        "uptime": "uptime",
        "timezone": ("timedatectl show --property=Timezone --value 2>/dev/null || date +%Z"),
    }

    for key, cmd in commands.items():
        returncode, stdout, _stderr = run_remote_command(host, user, cmd, port, ssh_key_path)
        if returncode == 0:
            info[key] = stdout.strip()
            logger.info(f"  {key}: {info[key]}")
        else:
            info[key] = "Unknown"
            logger.warning(f"  {key}: Unable to determine")

    return info


def check_system_resources(
    host: str, user: str, port: int, ssh_key_path: str | None
) -> dict[str, Any]:
    """Check system resources."""
    logger.info("=== System Resources ===")

    resources = {}

    # Disk space
    cmd = "df -h / | tail -1 | awk '{print $2, $3, $4, $5}'"
    returncode, stdout, stderr = run_remote_command(host, user, cmd, port, ssh_key_path)
    if returncode == 0:
        parts = stdout.strip().split()
        if len(parts) >= 4:
            resources["disk"] = {
                "total": parts[0],
                "used": parts[1],
                "available": parts[2],
                "use_percent": parts[3],
            }
            logger.info(
                f"  Disk: Total={resources['disk']['total']}, "
                f"Available={resources['disk']['available']}, "
                f"Used={resources['disk']['use_percent']}"
            )

    # Memory
    cmd = "free -h | grep Mem | awk '{print $2, $3, $4, $7}'"
    returncode, stdout, stderr = run_remote_command(host, user, cmd, port, ssh_key_path)
    if returncode == 0:
        parts = stdout.strip().split()
        if len(parts) >= 4:
            resources["memory"] = {
                "total": parts[0],
                "used": parts[1],
                "free": parts[2],
                "available": parts[3],
            }
            logger.info(
                f"  Memory: Total={resources['memory']['total']}, "
                f"Available={resources['memory']['available']}"
            )

    # CPU
    cmd = "nproc"
    returncode, stdout, stderr = run_remote_command(host, user, cmd, port, ssh_key_path)
    if returncode == 0:
        resources["cpu_cores"] = stdout.strip()
        logger.info(f"  CPU Cores: {resources['cpu_cores']}")

    # Load average
    cmd = "uptime | awk -F'load average:' '{print $2}'"
    returncode, stdout, _stderr = run_remote_command(host, user, cmd, port, ssh_key_path)
    if returncode == 0:
        resources["load_average"] = stdout.strip()
        logger.info(f"  Load Average: {resources['load_average']}")

    return resources


def check_docker_containers(
    host: str, user: str, port: int, ssh_key_path: str | None
) -> list[dict[str, str]]:
    """Check Docker containers status."""
    logger.info("=== Docker Containers ===")

    containers = []

    # List all containers
    cmd = (
        "docker ps -a --format "
        "'{{.Names}}|{{.Image}}|{{.Status}}|{{.Ports}}' 2>/dev/null || echo ''"
    )
    returncode, stdout, _stderr = run_remote_command(host, user, cmd, port, ssh_key_path)

    if returncode == 0 and stdout.strip():
        for line in stdout.strip().split("\n"):
            if "|" in line:
                parts = line.split("|")
                if len(parts) >= 3:
                    container = {
                        "name": parts[0],
                        "image": parts[1],
                        "status": parts[2],
                        "ports": parts[3] if len(parts) > 3 else "",
                    }
                    containers.append(container)
                    status_icon = "✓" if "Up" in container["status"] else "✗"
                    logger.info(
                        f"  {status_icon} {container['name']}: {container['status']} "
                        f"({container['image']})"
                    )
    else:
        logger.warning("  No containers found or Docker not accessible")

    return containers


def check_systemd_services(
    host: str,
    user: str,
    port: int,
    ssh_key_path: str | None,
    app_services: list[str] | None = None,
) -> list[dict[str, str]]:
    """
    Check systemd services status.

    :param host: Server hostname or IP
    :param user: SSH user
    :param port: SSH port
    :param ssh_key_path: Path to SSH private key
    :param app_services: Optional list of app-specific service names to check
    :return: List of service status dictionaries
    """
    logger.info("=== Systemd Services ===")

    services = []

    # List all services (generic check for common services)
    cmd = (
        "systemctl list-units --type=service --all --no-pager "
        "--format '{{.Unit}}|{{.Load}}|{{.Active}}|{{.Sub}}' 2>/dev/null || echo ''"
    )
    returncode, stdout, stderr = run_remote_command(host, user, cmd, port, ssh_key_path)

    if returncode == 0 and stdout.strip():
        for line in stdout.strip().split("\n"):
            if "|" in line:
                parts = line.split("|")
                if len(parts) >= 3:
                    service = {
                        "name": parts[0],
                        "load": parts[1],
                        "active": parts[2],
                        "sub": parts[3] if len(parts) > 3 else "",
                    }
                    # Only include active services or app-specific services
                    if service["active"] == "active" or (
                        app_services and service["name"] in app_services
                    ):
                        services.append(service)
                        status_icon = "✓" if service["active"] == "active" else "✗"
                        logger.info(
                            f"  {status_icon} {service['name']}: {service['active']} "
                            f"({service['sub']})"
                        )

    # Check for application-specific services
    if app_services:
        for svc in app_services:
            # Skip if already found
            if any(s["name"] == svc for s in services):
                continue
            cmd = f"systemctl is-active {svc} 2>/dev/null || echo 'inactive'"
            returncode, stdout, _stderr = run_remote_command(host, user, cmd, port, ssh_key_path)
            if returncode == 0:
                status = stdout.strip()
                if status != "inactive":
                    service = {
                        "name": svc,
                        "active": status,
                        "load": "loaded",
                        "sub": "running" if status == "active" else status,
                    }
                    services.append(service)
                    status_icon = "✓" if status == "active" else "✗"
                    logger.info(f"  {status_icon} {svc}: {status}")

    return services


def check_network_ports(
    host: str,
    user: str,
    port: int,
    ssh_key_path: str | None,
    ports_to_check: list[int] | None = None,
) -> dict[int, dict[str, str]]:
    """
    Check network ports and their listeners.

    :param host: Server hostname or IP
    :param user: SSH user
    :param port: SSH port
    :param ssh_key_path: Path to SSH private key
    :param ports_to_check: Optional list of ports to check (defaults to common ports)
    :return: Dictionary of port information
    """
    logger.info("=== Network Ports ===")

    ports_info = {}
    if ports_to_check is None:
        # Default common ports
        ports_to_check = [22, 80, 443, 5432, 8000, 8080]

    for check_port in ports_to_check:
        # Check if port is listening
        cmd = (
            f"ss -tuln 2>/dev/null | grep -q ':{check_port} ' && "
            f"echo 'listening' || echo 'not_listening'"
        )
        returncode, stdout, stderr = run_remote_command(host, user, cmd, port, ssh_key_path)

        is_listening = "listening" in stdout.lower() if returncode == 0 else False

        # Get process info if listening
        process_info = ""
        if is_listening:
            cmd = f"ss -tulnp 2>/dev/null | grep ':{check_port} ' | head -1"
            returncode, stdout, _stderr = run_remote_command(host, user, cmd, port, ssh_key_path)
            if returncode == 0:
                process_info = stdout.strip()

        ports_info[check_port] = {
            "listening": is_listening,
            "process": process_info,
        }

        status_icon = "✓" if is_listening else "○"
        logger.info(
            f"  {status_icon} Port {check_port}: {'LISTENING' if is_listening else 'not listening'}"
        )

    return ports_info


def check_dependencies(
    host: str, user: str, port: int, ssh_key_path: str | None
) -> dict[str, dict[str, str]]:
    """Check installed dependencies."""
    logger.info("=== Dependencies ===")

    deps = {}

    dependencies = {
        "docker": "docker --version",
        "python3": "python3 --version",
        "node": "node --version",
        "npm": "npm --version",
        "git": "git --version",
        "uv": "/root/.cargo/bin/uv --version 2>/dev/null || echo 'not found'",
    }

    for dep_name, cmd in dependencies.items():
        returncode, stdout, _stderr = run_remote_command(host, user, cmd, port, ssh_key_path)
        if returncode == 0 and stdout.strip() and "not found" not in stdout.lower():
            version = stdout.strip()
            deps[dep_name] = {"installed": True, "version": version}
            logger.info(f"  ✓ {dep_name}: {version}")
        else:
            deps[dep_name] = {"installed": False}
            logger.warning(f"  ✗ {dep_name}: not found")

    return deps


def generate_report(
    system_info: dict,
    resources: dict,
    containers: list[dict],
    services: list[dict],
    ports: dict,
    health: dict,
    configs: dict,
    logs: dict,
    deps: dict,
    fs_info: dict,
    app_name: str | None = None,
) -> str:
    """Generate a comprehensive diagnostic report."""
    report = []
    report.append("=" * 80)
    report.append("COMPREHENSIVE SERVER DIAGNOSTIC REPORT")
    if app_name:
        report.append(f"Application: {app_name.upper()}")
    report.append("=" * 80)
    report.append("")

    # System Information
    report.append("## System Information")
    report.append(f"Hostname: {system_info.get('hostname', 'Unknown')}")
    report.append(f"OS: {system_info.get('os_release', 'Unknown')}")
    report.append(f"Kernel: {system_info.get('kernel', 'Unknown')}")
    report.append(f"Architecture: {system_info.get('arch', 'Unknown')}")
    report.append(f"Uptime: {system_info.get('uptime', 'Unknown')}")
    report.append("")

    # Resources
    report.append("## System Resources")
    if "disk" in resources:
        report.append(
            f"Disk: {resources['disk'].get('available', 'Unknown')} available "
            f"({resources['disk'].get('use_percent', 'Unknown')} used)"
        )
    if "memory" in resources:
        report.append(f"Memory: {resources['memory'].get('available', 'Unknown')} available")
    if "cpu_cores" in resources:
        report.append(f"CPU Cores: {resources['cpu_cores']}")
    report.append("")

    # Docker Containers
    report.append("## Docker Containers")
    if containers:
        for container in containers:
            status = "✓" if "Up" in container.get("status", "") else "✗"
            report.append(f"{status} {container['name']}: {container['status']}")
    else:
        report.append("No containers found")
    report.append("")

    # Systemd Services
    report.append("## Systemd Services")
    if services:
        for service in services:
            status = "✓" if service.get("active") == "active" else "✗"
            report.append(f"{status} {service['name']}: {service['active']}")
    else:
        report.append("No application services found")
    report.append("")

    # Network Ports
    report.append("## Network Ports")
    for port_num, port_info in sorted(ports.items()):
        status = "✓" if port_info.get("listening") else "○"
        report.append(
            f"{status} Port {port_num}: "
            f"{'LISTENING' if port_info.get('listening') else 'not listening'}"
        )
    report.append("")

    # Health Checks
    if health:
        report.append("## Application Health")
        for app, health_info in health.items():
            status = "✓" if health_info.get("status") in ["healthy", "reachable"] else "✗"
            report.append(f"{status} {app}: {health_info.get('status', 'unknown')}")
        report.append("")

    # Dependencies
    report.append("## Dependencies")
    for dep_name, dep_info in deps.items():
        status = "✓" if dep_info.get("installed") else "✗"
        version = dep_info.get("version", "not installed")
        report.append(f"{status} {dep_name}: {version}")
    report.append("")

    # Configuration Files
    if configs:
        report.append("## Configuration Files")
        for config_file, config_info in configs.items():
            status = "✓" if config_info.get("exists") else "✗"
            if config_info.get("exists"):
                report.append(
                    f"{status} {config_file}: {config_info.get('size', 'N/A')}, "
                    f"{config_info.get('permissions', 'N/A')}"
                )
            else:
                report.append(f"{status} {config_file}: not found")
        report.append("")

    # File System
    if fs_info:
        report.append("## File System")
        for path, fs_data in fs_info.items():
            status = "✓" if fs_data.get("exists") else "✗"
            report.append(f"{status} {path}: {fs_data.get('size', 'N/A')}")
        report.append("")

    # Logs Summary
    if logs:
        report.append("## Recent Logs Summary")
        for log_name, log_lines in logs.items():
            error_count = sum(
                1
                for line in log_lines
                if "error" in line.lower() or "failed" in line.lower() or "fatal" in line.lower()
            )
            if error_count > 0:
                report.append(f"⚠ {log_name}: {error_count} error(s) in recent logs")
            else:
                report.append(f"✓ {log_name}: No recent errors")
        report.append("")

    report.append("=" * 80)
    report.append("END OF REPORT")
    report.append("=" * 80)

    return "\n".join(report)


def diagnose_server(
    host: str,
    user: str,
    port: int = 22,
    ssh_key_path: str | None = None,
    app_name: str | None = None,
    app_path: str | None = None,
    output_file: str | None = None,
) -> bool:
    """
    Perform comprehensive server diagnostic.

    :param host: Server hostname or IP
    :param user: SSH user
    :param port: SSH port
    :param ssh_key_path: Path to SSH private key
    :param app_name: Optional application name for app-specific diagnostics
    :param app_path: Optional application path (overrides app default)
    :param output_file: Optional file to save report
    :return: True if diagnostic completed successfully
    """
    logger.info(f"Starting comprehensive diagnostic for {user}@{host}:{port}")
    if app_name:
        logger.info(f"Application: {app_name}")
    logger.info("=" * 80)

    try:
        # Test SSH connection
        logger.info("Testing SSH connection...")
        returncode, _stdout, stderr = run_remote_command(
            host, user, "echo 'SSH connection successful'", port, ssh_key_path
        )
        if returncode != 0:
            logger.error(f"SSH connection failed: {stderr}")
            return False
        logger.info("✓ SSH connection successful\n")

        # Load app-specific diagnostic if app_name provided
        app_diagnostic = None
        app_services = None
        ports_to_check = None

        if app_name:
            app_diagnostic = DiagnosticRegistry.create_diagnostic(app_name, run_remote_command)
            if app_diagnostic:
                logger.info(f"Loaded diagnostic module for: {app_name}")
                app_services = app_diagnostic.get_systemd_services()
                ports_to_check = app_diagnostic.get_ports_to_check()
                if app_path is None:
                    app_path = app_diagnostic.get_app_path()
            else:
                logger.warning(
                    f"No diagnostic module found for '{app_name}', running generic diagnostics only"
                )

        # Run generic diagnostic checks
        system_info = check_system_info(host, user, port, ssh_key_path)
        logger.info("")

        resources = check_system_resources(host, user, port, ssh_key_path)
        logger.info("")

        containers = check_docker_containers(host, user, port, ssh_key_path)
        logger.info("")

        services = check_systemd_services(host, user, port, ssh_key_path, app_services=app_services)
        logger.info("")

        ports = check_network_ports(host, user, port, ssh_key_path, ports_to_check=ports_to_check)
        logger.info("")

        deps = check_dependencies(host, user, port, ssh_key_path)
        logger.info("")

        # Run app-specific diagnostic checks if available
        health = {}
        configs = {}
        logs = {}
        fs_info = {}

        if app_diagnostic:
            health = app_diagnostic.check_application_health(host, user, port, ssh_key_path)
            logger.info("")

            configs = app_diagnostic.check_configuration_files(
                host, user, port, ssh_key_path, app_path=app_path
            )
            logger.info("")

            logs = app_diagnostic.check_logs(host, user, port, ssh_key_path)
            logger.info("")

            fs_info = app_diagnostic.check_file_system(
                host, user, port, ssh_key_path, app_path=app_path
            )
            logger.info("")

        # Generate report
        report = generate_report(
            system_info,
            resources,
            containers,
            services,
            ports,
            health,
            configs,
            logs,
            deps,
            fs_info,
            app_name=app_name,
        )

        logger.info("=" * 80)
        logger.info("DIAGNOSTIC REPORT")
        logger.info("=" * 80)
        print("\n" + report + "\n")

        # Save to file if requested
        if output_file:
            try:
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write(report)
                logger.info(f"Report saved to: {output_file}")
            except Exception as e:
                logger.exception(f"Failed to save report: {e}")

        return True

    except Exception as e:
        logger.error(f"Diagnostic failed: {e}", exc_info=True)
        return False


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Comprehensive server diagnostic tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic diagnostic (generic, no app-specific checks)
  %(prog)s --server-host demobox --server-user cole

  # IPSA-specific diagnostic
  %(prog)s --server-host demobox --server-user cole --app ipsa

  # With SSH key
  %(prog)s --server-host demobox --server-user cole --app ipsa --ssh-key-path ~/.ssh/id_rsa

  # Save report to file
  %(prog)s --server-host demobox --server-user cole --app ipsa --output report.txt

  # Custom application path
  %(prog)s --server-host demobox --server-user cole --app ipsa --app-path /opt/custom-ipsa
        """,
    )

    parser.add_argument(
        "--server-host",
        required=True,
        help="Server hostname or IP address",
    )
    parser.add_argument(
        "--server-user",
        required=True,
        help="SSH user",
    )
    parser.add_argument(
        "--server-port",
        type=int,
        default=22,
        help="SSH port (default: 22)",
    )
    parser.add_argument(
        "--ssh-key-path",
        help="Path to SSH private key",
    )
    parser.add_argument(
        "--app",
        choices=[*DiagnosticRegistry.list_apps(), "none"],
        help=f"Application name for app-specific diagnostics. "
        f"Available: {', '.join(DiagnosticRegistry.list_apps())}. "
        f"Use 'none' for generic diagnostics only.",
    )
    parser.add_argument(
        "--app-path",
        help="Application path on server (overrides app default)",
    )
    parser.add_argument(
        "--output",
        help="Save diagnostic report to file",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output report as JSON (future feature)",
    )

    args = parser.parse_args()

    app_name = None if args.app == "none" or args.app is None else args.app

    success = diagnose_server(
        host=args.server_host,
        user=args.server_user,
        port=args.server_port,
        ssh_key_path=args.ssh_key_path,
        app_name=app_name,
        app_path=args.app_path,
        output_file=args.output,
    )

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
