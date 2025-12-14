#!/usr/bin/env python3
"""
CI/CD Task Runner

This script performs the same checks as the GitHub Actions CI workflow locally.
It can run tests, linting, type checking, security scans, and build the package.

Usage:
    python run_ci.py                    # Run all checks
    python run_ci.py --test             # Run only tests
    python run_ci.py --lint             # Run only linting
    python run_ci.py --type-check       # Run only type checking
    python run_ci.py --security        # Run only security scans
    python run_ci.py --build            # Run only build
    python run_ci.py --test --lint      # Run multiple specific tasks
"""

import argparse
from pathlib import Path
import subprocess
import sys

# ANSI color codes for terminal output
COLORS = {
    "reset": "\033[0m",
    "bold": "\033[1m",
    "red": "\033[31m",
    "green": "\033[32m",
    "yellow": "\033[33m",
    "blue": "\033[34m",
    "magenta": "\033[35m",
    "cyan": "\033[36m",
}


def print_header(text: str) -> None:
    """Print a formatted header."""
    print(f"\n{COLORS['bold']}{COLORS['cyan']}{'=' * 60}{COLORS['reset']}")
    print(f"{COLORS['bold']}{COLORS['cyan']}{text}{COLORS['reset']}")
    print(f"{COLORS['bold']}{COLORS['cyan']}{'=' * 60}{COLORS['reset']}\n")


def print_success(text: str) -> None:
    """Print a success message."""
    print(f"{COLORS['green']}[OK] {text}{COLORS['reset']}")


def print_error(text: str) -> None:
    """Print an error message."""
    print(f"{COLORS['red']}[FAIL] {text}{COLORS['reset']}")


def print_warning(text: str) -> None:
    """Print a warning message."""
    print(f"{COLORS['yellow']}[WARN] {text}{COLORS['reset']}")


def print_info(text: str) -> None:
    """Print an info message."""
    print(f"{COLORS['blue']}[INFO] {text}{COLORS['reset']}")


def run_command(
    cmd: list[str],
    description: str,
    continue_on_error: bool = False,
    capture_output: bool = False,
) -> tuple[bool, str | None]:
    """
    Run a shell command and return success status and output.

    Args:
        cmd: Command to run as a list of strings
        description: Description of what the command does
        continue_on_error: If True, don't exit on error
        capture_output: If True, capture and return output

    Returns:
        Tuple of (success: bool, output: Optional[str])
    """
    print_info(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}\n")

    try:
        result = subprocess.run(
            cmd,
            check=False,
            capture_output=capture_output,
            text=True,
        )

        if result.returncode == 0:
            print_success(f"{description} completed successfully")
            output = result.stdout if capture_output else None
            return True, output
        print_error(f"{description} failed with exit code {result.returncode}")
        if capture_output and result.stderr:
            print(result.stderr)
        if not continue_on_error:
            sys.exit(result.returncode)
        return False, result.stderr if capture_output else None

    except FileNotFoundError:
        print_error(f"Command not found: {cmd[0]}")
        print_info("Make sure the required tool is installed")
        if not continue_on_error:
            sys.exit(1)
        return False, None
    except Exception as e:
        print_error(f"Error running {description}: {e}")
        if not continue_on_error:
            sys.exit(1)
        return False, None


def check_dependencies() -> None:
    """Check if required dependencies are installed."""
    required_tools = {
        "pytest": "pytest",
        "ruff": "ruff",
        "mypy": "mypy",
        "bandit": "bandit",
        "safety": "safety",
        "build": "python -m build",
    }

    missing = []
    for tool, check_cmd in required_tools.items():
        cmd = check_cmd.split()
        try:
            subprocess.run(
                [*cmd, "--version"],
                capture_output=True,
                check=True,
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            missing.append(tool)

    if missing:
        print_warning(f"Missing tools: {', '.join(missing)}")
        print_info("Install with: pip install -e '.[dev]' safety bandit")
        print_info("Some checks may fail if tools are not installed\n")


def run_tests() -> bool:
    """Run pytest with coverage."""
    print_header("Running Tests with Coverage")

    cmd = [
        "pytest",
        "--cov=python/_utils",
        "--cov-report=xml",
        "--cov-report=html",
        "--cov-report=term-missing",
        "-v",
    ]

    success, _ = run_command(cmd, "Tests with coverage")
    return success


def run_lint() -> bool:
    """Run ruff linting and format checking."""
    print_header("Running Linting Checks")

    # Run ruff check
    cmd_check = ["ruff", "check", "."]
    success_check, _ = run_command(cmd_check, "Ruff lint check")

    # Run ruff format check
    cmd_format = ["ruff", "format", "--check", "."]
    success_format, _ = run_command(cmd_format, "Ruff format check")

    return success_check and success_format


def run_type_check() -> bool:
    """Run mypy type checking."""
    print_header("Running Type Checking")

    cmd = ["mypy", "python"]
    success, _ = run_command(cmd, "Type checking with mypy", continue_on_error=True)
    return success


def run_security() -> bool:
    """Run security scans with bandit and safety."""
    print_header("Running Security Scans")

    # Run bandit
    bandit_cmd = [
        "bandit",
        "-r",
        "python",
        "-f",
        "json",
        "-o",
        "bandit-report.json",
    ]
    success_bandit, _ = run_command(
        bandit_cmd,
        "Bandit security scan",
        continue_on_error=True,
    )

    # If JSON output fails, try without JSON
    if not success_bandit:
        bandit_cmd_simple = ["bandit", "-r", "python"]
        success_bandit, _ = run_command(
            bandit_cmd_simple,
            "Bandit security scan (simple)",
            continue_on_error=True,
        )

    # Run safety check
    safety_cmd = ["safety", "check", "--json"]
    success_safety, _ = run_command(
        safety_cmd,
        "Safety dependency check",
        continue_on_error=True,
    )

    # If JSON output fails, try without JSON
    if not success_safety:
        safety_cmd_simple = ["safety", "check"]
        success_safety, _ = run_command(
            safety_cmd_simple,
            "Safety dependency check (simple)",
            continue_on_error=True,
        )

    return success_bandit and success_safety


def run_build() -> bool:
    """Build the package and validate it."""
    print_header("Building Package")

    # Clean previous builds
    for path in ["build", "dist", "*.egg-info"]:
        import glob
        import shutil

        for item in glob.glob(path):
            if Path(item).exists():
                print_info(f"Cleaning {item}")
                if Path(item).is_dir():
                    shutil.rmtree(item)
                else:
                    Path(item).unlink()

    # Build package
    cmd_build = [sys.executable, "-m", "build"]
    success_build, _ = run_command(cmd_build, "Building package")

    if not success_build:
        return False

    # Check package with twine
    import glob

    dist_files = glob.glob("dist/*")
    if not dist_files:
        print_error("No distribution files found")
        return False

    cmd_check = ["twine", "check", *dist_files]
    success_check, _ = run_command(cmd_check, "Validating package with twine")

    return success_build and success_check


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Run CI/CD tasks locally",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument(
        "--test",
        action="store_true",
        help="Run tests with coverage",
    )
    parser.add_argument(
        "--lint",
        action="store_true",
        help="Run linting checks (ruff)",
    )
    parser.add_argument(
        "--type-check",
        action="store_true",
        help="Run type checking (mypy)",
    )
    parser.add_argument(
        "--security",
        action="store_true",
        help="Run security scans (bandit, safety)",
    )
    parser.add_argument(
        "--build",
        action="store_true",
        help="Build and validate package",
    )
    parser.add_argument(
        "--skip-deps-check",
        action="store_true",
        help="Skip dependency check at startup",
    )

    args = parser.parse_args()

    # If no specific tasks selected, run all
    run_all = not any([args.test, args.lint, args.type_check, args.security, args.build])

    print_header("CI/CD Task Runner")
    print_info("Running local CI checks\n")

    if not args.skip_deps_check:
        check_dependencies()

    results = {}

    if run_all or args.test:
        results["test"] = run_tests()

    if run_all or args.lint:
        results["lint"] = run_lint()

    if run_all or args.type_check:
        results["type_check"] = run_type_check()

    if run_all or args.security:
        results["security"] = run_security()

    if run_all or args.build:
        results["build"] = run_build()

    # Print summary
    print_header("Summary")
    all_passed = all(results.values())
    for task, passed in results.items():
        status = "PASSED" if passed else "FAILED"
        color = COLORS["green"] if passed else COLORS["red"]
        symbol = "[OK]" if passed else "[FAIL]"
        print(f"{color}{symbol} {task.upper()}: {status}{COLORS['reset']}")

    if all_passed:
        print_success("\nAll checks passed!")
        sys.exit(0)
    else:
        print_error("\nSome checks failed. Please review the output above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
