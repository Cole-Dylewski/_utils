"""
Command-line interface for _utils package.

Provides convenient CLI commands for development, testing, and common operations.
"""

from pathlib import Path
import subprocess
import sys
from typing import Optional

try:
    import click
except ImportError:
    click = None


if click is None:
    # Fallback if click is not installed
    def _no_click_error() -> None:
        """Print error message when click is not installed."""
        print("Error: click is required for CLI. Install with: pip install click")
        sys.exit(1)

    def cli() -> None:
        """CLI entry point (fallback)."""
        _no_click_error()
else:

    @click.group()
    @click.version_option(version="0.1.0", prog_name="_utils")
    def cli() -> None:
        """_utils - Professional utility library CLI."""

    @cli.command()
    @click.option("--verbose", "-v", is_flag=True, help="Verbose output")
    @click.option("--coverage", is_flag=True, help="Show coverage report")
    @click.option("--fail-fast", is_flag=True, help="Stop on first failure")
    def test(verbose: bool, coverage: bool, fail_fast: bool) -> None:
        """Run tests."""
        cmd = ["pytest", "python/tests"]
        if verbose:
            cmd.append("-v")
        if coverage:
            cmd.extend(["--cov=python/_utils", "--cov-report=term-missing"])
        if fail_fast:
            cmd.append("-x")
        try:
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError:
            sys.exit(1)

    @cli.command()
    @click.option("--fix", is_flag=True, help="Auto-fix issues")
    @click.option("--check", is_flag=True, help="Check only, don't fix")
    def lint(fix: bool, check: bool) -> None:
        """Run linting with ruff."""
        cmd = ["ruff", "check", "python"]
        if fix and not check:
            cmd.append("--fix")
        try:
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError:
            sys.exit(1)

    @cli.command()
    def format_code() -> None:
        """Format code with ruff."""
        cmd = ["ruff", "format", "python"]
        try:
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError:
            sys.exit(1)

    @cli.command()
    @click.option("--strict", is_flag=True, help="Enable strict mode")
    def typecheck(strict: bool) -> None:
        """Run type checking with mypy."""
        cmd = ["mypy", "python/_utils"]
        if strict:
            cmd.extend(["--strict", "--no-implicit-optional"])
        try:
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError:
            sys.exit(1)

    @cli.command()
    def security() -> None:
        """Run security checks (bandit and safety)."""
        click.echo("Running Bandit security scan...")
        try:
            subprocess.run(["bandit", "-r", "python/_utils"], check=True)
        except subprocess.CalledProcessError:
            click.echo("Bandit found security issues", err=True)
            sys.exit(1)

        click.echo("Running Safety dependency check...")
        try:
            subprocess.run(["safety", "check"], check=True)
        except subprocess.CalledProcessError:
            click.echo("Safety found vulnerable dependencies", err=True)
            sys.exit(1)

        click.echo("Security checks passed!")

    @cli.command()
    @click.option("--all", "check_all", is_flag=True, help="Run all checks")
    def check(check_all: bool) -> None:
        """Run all code quality checks."""
        if check_all:
            click.echo("Running all checks...")
            ctx = click.get_current_context()
            ctx.invoke(lint)
            ctx.invoke(format_code)
            ctx.invoke(typecheck)
            ctx.invoke(test)
            ctx.invoke(security)
        else:
            click.echo("Use --all to run all checks")

    @cli.command()
    @click.option("--output", "-o", type=click.Path(), help="Output directory")
    def docs(output: Optional[str]) -> None:
        """Build documentation."""
        cmd = ["mkdocs", "build"]
        if output:
            cmd.extend(["--site-dir", output])
        try:
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError:
            click.echo("Documentation build failed", err=True)
            sys.exit(1)
        click.echo("Documentation built successfully!")

    @cli.command()
    def serve_docs() -> None:
        """Serve documentation locally."""
        cmd = ["mkdocs", "serve"]
        try:
            subprocess.run(cmd, check=True)
        except KeyboardInterrupt:
            click.echo("\nDocumentation server stopped")
        except subprocess.CalledProcessError:
            click.echo("Failed to start documentation server", err=True)
            sys.exit(1)

    @cli.group()
    def coverage() -> None:
        """Coverage reporting commands."""

    @coverage.command()
    @click.option("--html", is_flag=True, help="Generate HTML report")
    @click.option("--xml", is_flag=True, help="Generate XML report")
    def report(html: bool, xml: bool) -> None:
        """Generate coverage report."""
        cmd = ["pytest", "--cov=python/_utils", "--cov-report=term"]
        if html:
            cmd.append("--cov-report=html")
        if xml:
            cmd.append("--cov-report=xml")
        try:
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError:
            sys.exit(1)

    @cli.command()
    def version() -> None:
        """Show version information."""
        try:
            from _utils import __version__

            click.echo(f"_utils version: {__version__}")
        except ImportError:
            click.echo("_utils version: 0.1.0 (development)")

    @cli.command()
    @click.argument("module", required=False)
    def info(module: Optional[str]) -> None:
        """Show package information."""
        click.echo("_utils - Professional utility library")
        click.echo("=" * 50)
        click.echo("\nModules:")
        click.echo("  - aws: AWS service integrations")
        click.echo("  - alpaca: Alpaca trading API clients")
        click.echo("  - utils: General utilities")
        click.echo("  - sql: Database operations")
        click.echo("  - server_management: Infrastructure automation")
        click.echo("\nFor more information, see:")
        click.echo("  - Documentation: https://github.com/Cole-Dylewski/_utils")
        click.echo("  - README: README.md")


def main() -> None:
    """Main entry point for CLI."""
    if click is None:
        print("Error: click is required for CLI. Install with: pip install click")
        sys.exit(1)
    cli()


if __name__ == "__main__":
    main()
