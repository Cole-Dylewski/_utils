#!/usr/bin/env python3
"""
Cross-platform virtual environment setup script for _utils.

This script works on Linux, macOS, and Windows to:
1. Check Python version
2. Create a virtual environment (.venv)
3. Install the package with development dependencies
4. Install pre-commit hooks

Usage:
    python setup-venv.py
    # or
    python3 setup-venv.py
"""

import os
import sys
import subprocess
import platform
from pathlib import Path


def print_status(message: str, status: str = "info") -> None:
    """Print colored status messages."""
    colors = {
        "info": "\033[36m",      # Cyan
        "success": "\033[32m",   # Green
        "warning": "\033[33m",   # Yellow
        "error": "\033[31m",     # Red
        "reset": "\033[0m",      # Reset
    }
    
    # Windows doesn't support ANSI colors in older terminals
    if platform.system() == "Windows" and not os.getenv("TERM"):
        print(message)
    else:
        color = colors.get(status, colors["info"])
        reset = colors["reset"]
        print(f"{color}{message}{reset}")


def check_python_version() -> bool:
    """Check if Python version is 3.10 or higher."""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 10):
        print_status(
            f"Error: Python 3.10 or higher is required. Found: {version.major}.{version.minor}.{version.micro}",
            "error"
        )
        return False
    
    print_status(f"✓ Python version check passed: {version.major}.{version.minor}.{version.micro}", "success")
    return True


def run_command(command: list[str], check: bool = True) -> tuple[int, str, str]:
    """Run a command and return the result."""
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=check,
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.CalledProcessError as e:
        return e.returncode, e.stdout, e.stderr
    except FileNotFoundError:
        return 1, "", f"Command not found: {command[0]}"


def create_venv() -> bool:
    """Create virtual environment if it doesn't exist."""
    venv_path = Path(".venv")
    
    if venv_path.exists():
        print_status("✓ Virtual environment already exists", "success")
        return True
    
    print_status("Creating virtual environment...", "info")
    returncode, stdout, stderr = run_command([sys.executable, "-m", "venv", ".venv"])
    
    if returncode != 0:
        print_status(f"Error creating virtual environment: {stderr}", "error")
        return False
    
    print_status("✓ Virtual environment created", "success")
    return True


def get_venv_python() -> Path:
    """Get the path to the virtual environment Python executable."""
    system = platform.system()
    venv_path = Path(".venv")
    
    if system == "Windows":
        return venv_path / "Scripts" / "python.exe"
    else:
        return venv_path / "bin" / "python"


def get_venv_pip() -> Path:
    """Get the path to the virtual environment pip executable."""
    system = platform.system()
    venv_path = Path(".venv")
    
    if system == "Windows":
        return venv_path / "Scripts" / "pip.exe"
    else:
        return venv_path / "bin" / "pip"


def upgrade_pip(venv_python: Path) -> bool:
    """Upgrade pip in the virtual environment."""
    print_status("Upgrading pip...", "info")
    returncode, stdout, stderr = run_command([str(venv_python), "-m", "pip", "install", "--upgrade", "pip"])
    
    if returncode != 0:
        print_status(f"Warning: pip upgrade failed: {stderr}", "warning")
        return False
    
    print_status("✓ pip upgraded", "success")
    return True


def install_package(venv_pip: Path) -> bool:
    """Install package with development dependencies."""
    print_status("Installing package with development dependencies...", "info")
    returncode, stdout, stderr = run_command(
        [str(venv_pip), "install", "-e", ".[dev]"],
        check=False
    )
    
    if returncode != 0:
        print_status(f"Error installing package: {stderr}", "error")
        return False
    
    print_status("✓ Package installed", "success")
    return True


def install_precommit(venv_python: Path) -> bool:
    """Install pre-commit hooks."""
    print_status("Installing pre-commit hooks...", "info")
    
    # Check if pre-commit is available
    returncode, _, _ = run_command([str(venv_python), "-m", "pre_commit", "--version"], check=False)
    if returncode != 0:
        print_status("Warning: pre-commit not available, skipping hook installation", "warning")
        return False
    
    returncode, stdout, stderr = run_command([str(venv_python), "-m", "pre_commit", "install"], check=False)
    
    if returncode != 0:
        print_status(f"Warning: pre-commit installation failed: {stderr}", "warning")
        return False
    
    print_status("✓ Pre-commit hooks installed", "success")
    return True


def print_activation_instructions() -> None:
    """Print instructions for activating the virtual environment."""
    system = platform.system()
    
    print_status("\n✓ Development environment setup complete!\n", "success")
    print_status("To activate the virtual environment:", "info")
    
    if system == "Windows":
        print_status("  PowerShell:", "info")
        print("    .venv\\Scripts\\Activate.ps1")
        print_status("  Command Prompt:", "info")
        print("    .venv\\Scripts\\activate.bat")
    else:
        print_status("  Bash/Zsh:", "info")
        print("    source .venv/bin/activate")
        print_status("  Fish:", "info")
        print("    source .venv/bin/activate.fish")
        print_status("  Csh:", "info")
        print("    source .venv/bin/activate.csh")
    
    print_status("\nTo run tests:", "info")
    print("  pytest")
    
    print_status("\nTo run linting:", "info")
    print("  ruff check .")
    
    print_status("\nTo format code:", "info")
    print("  ruff format .")
    
    print_status("\nTo run all quality checks:", "info")
    print("  make quality")
    print("  # or on Windows: python -m ruff check . && python -m mypy python")
    print()


def main() -> int:
    """Main setup function."""
    print_status("Setting up _utils development environment...\n", "info")
    
    # Check Python version
    if not check_python_version():
        return 1
    
    # Create virtual environment
    if not create_venv():
        return 1
    
    # Get paths to venv executables
    venv_python = get_venv_python()
    venv_pip = get_venv_pip()
    
    if not venv_python.exists():
        print_status(f"Error: Virtual environment Python not found at {venv_python}", "error")
        return 1
    
    # Upgrade pip
    upgrade_pip(venv_python)
    
    # Install package
    if not install_package(venv_pip):
        return 1
    
    # Install pre-commit hooks
    install_precommit(venv_python)
    
    # Print instructions
    print_activation_instructions()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

