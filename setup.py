#!/usr/bin/env python3
"""
Unified cross-platform setup and activation script for _utils.

This script handles:
1. Virtual environment setup (create, install dependencies)
2. Virtual environment activation (detects platform and shell)

Usage:
    # Setup (creates venv and installs dependencies)
    python setup.py

    # Activate (activates the venv in current shell)
    python setup.py activate
    # or use the convenience alias:
    source setup.py activate  # Unix
    . setup.py activate       # Windows PowerShell (if configured)
"""

import os
from pathlib import Path
import platform
import subprocess
import sys


def print_status(message: str, status: str = "info") -> None:
    """Print colored status messages."""
    colors = {
        "info": "\033[36m",  # Cyan
        "success": "\033[32m",  # Green
        "warning": "\033[33m",  # Yellow
        "error": "\033[31m",  # Red
        "reset": "\033[0m",  # Reset
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
            "error",
        )
        return False

    print_status(
        f"[OK] Python version check passed: {version.major}.{version.minor}.{version.micro}",
        "success",
    )
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
        print_status("[OK] Virtual environment already exists", "success")
        return True

    print_status("Creating virtual environment...", "info")
    returncode, _stdout, stderr = run_command([sys.executable, "-m", "venv", ".venv"])

    if returncode != 0:
        print_status(f"Error creating virtual environment: {stderr}", "error")
        return False

    print_status("[OK] Virtual environment created", "success")
    return True


def get_venv_python() -> Path:
    """Get the path to the virtual environment Python executable."""
    system = platform.system()
    venv_path = Path(".venv")

    if system == "Windows":
        return venv_path / "Scripts" / "python.exe"
    return venv_path / "bin" / "python"


def get_venv_pip() -> Path:
    """Get the path to the virtual environment pip executable."""
    system = platform.system()
    venv_path = Path(".venv")

    if system == "Windows":
        return venv_path / "Scripts" / "pip.exe"
    return venv_path / "bin" / "pip"


def upgrade_pip(venv_python: Path) -> bool:
    """Upgrade pip in the virtual environment."""
    print_status("Upgrading pip...", "info")
    returncode, _stdout, stderr = run_command(
        [str(venv_python), "-m", "pip", "install", "--upgrade", "pip"]
    )

    if returncode != 0:
        print_status(f"Warning: pip upgrade failed: {stderr}", "warning")
        return False

    print_status("[OK] pip upgraded", "success")
    return True


def install_package(venv_pip: Path) -> bool:
    """Install package with all dependencies from requirements.txt."""
    print_status("Installing package with all dependencies...", "info")

    # Check if requirements.txt exists
    if Path("requirements.txt").exists():
        returncode, _stdout, stderr = run_command(
            [str(venv_pip), "install", "-r", "requirements.txt"], check=False
        )
    else:
        # Fallback to editable install with dev extras
        returncode, _stdout, stderr = run_command(
            [str(venv_pip), "install", "-e", "."], check=False
        )

    if returncode != 0:
        print_status(f"Error installing package: {stderr}", "error")
        return False

    print_status("[OK] Package installed", "success")
    return True


def install_precommit(venv_python: Path) -> bool:
    """Install pre-commit hooks."""
    print_status("Installing pre-commit hooks...", "info")

    # Check if pre-commit is available
    returncode, _, _ = run_command([str(venv_python), "-m", "pre_commit", "--version"], check=False)
    if returncode != 0:
        print_status("Warning: pre-commit not available, skipping hook installation", "warning")
        return False

    returncode, _stdout, stderr = run_command(
        [str(venv_python), "-m", "pre_commit", "install"], check=False
    )

    if returncode != 0:
        print_status(f"Warning: pre-commit installation failed: {stderr}", "warning")
        return False

    print_status("[OK] Pre-commit hooks installed", "success")
    return True


def get_activate_script() -> Path | None:
    """Get the path to the activation script based on platform and shell."""
    system = platform.system()
    venv_path = Path(".venv")

    if not venv_path.exists():
        return None

    # Detect shell
    shell = os.environ.get("SHELL", "").lower()

    if system == "Windows":
        # Check for PowerShell
        if "powershell" in os.environ.get("PSMODULEPATH", "").lower() or "pwsh" in shell:
            activate = venv_path / "Scripts" / "Activate.ps1"
            if activate.exists():
                return activate
        # Fallback to batch file
        activate = venv_path / "Scripts" / "activate.bat"
        if activate.exists():
            return activate
    # Unix-like systems
    elif "fish" in shell:
        activate = venv_path / "bin" / "activate.fish"
        if activate.exists():
            return activate
    elif "csh" in shell or "tcsh" in shell:
        activate = venv_path / "bin" / "activate.csh"
        if activate.exists():
            return activate
    else:
        # Default to bash/zsh
        activate = venv_path / "bin" / "activate"
        if activate.exists():
            return activate

    return None


def activate_venv() -> int:
    """Activate the virtual environment."""
    venv_path = Path(".venv")

    if not venv_path.exists():
        print_status("Error: Virtual environment not found. Run 'python setup.py' first.", "error")
        return 1

    activate_script = get_activate_script()

    if not activate_script:
        print_status("Error: Could not find activation script", "error")
        return 1

    system = platform.system()

    print_status("Activating virtual environment...", "info")
    print_status(f"Found activation script: {activate_script}", "info")

    # Print activation instructions (we can't actually activate from Python)
    print_status("\nTo activate the virtual environment, run:", "info")

    if system == "Windows":
        if activate_script.suffix == ".ps1":
            print("  .venv\\Scripts\\Activate.ps1")
            print("\nOr in PowerShell:")
            print("  & .venv\\Scripts\\Activate.ps1")
        else:
            print("  .venv\\Scripts\\activate.bat")
    else:
        print(f"  source {activate_script}")

    print_status("\nNote: This script cannot activate the venv in your current shell.", "warning")
    print_status("You must run the activation command above in your shell.", "warning")

    return 0


def setup_venv() -> int:
    """Setup the virtual environment."""
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

    # Print activation instructions
    print_status("\n[OK] Development environment setup complete!\n", "success")
    print_status("To activate the virtual environment:", "info")

    system = platform.system()
    if system == "Windows":
        print("  PowerShell: .venv\\Scripts\\Activate.ps1")
        print("  Command Prompt: .venv\\Scripts\\activate.bat")
    else:
        print("  Bash/Zsh: source .venv/bin/activate")
        print("  Fish: source .venv/bin/activate.fish")

    print_status("\nOr use: python setup.py activate", "info")
    print_status("\nTo run tests: pytest", "info")
    print_status("To run linting: ruff check .", "info")
    print_status("To format code: ruff format .", "info")
    print()

    return 0


def main() -> int:
    """Main function."""
    if len(sys.argv) > 1 and sys.argv[1] == "activate":
        return activate_venv()
    return setup_venv()


if __name__ == "__main__":
    sys.exit(main())
