"""Run command strings through system PowerShell or the POSIX system shell.

This helper gives automation the same executable lookup and quoting behavior as
an interactive Windows PowerShell session. On Linux and macOS it uses
``/bin/sh -c`` so callers can keep one command string across platforms.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
import subprocess
import sys

POWERSHELL_EXE = Path(r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe")


def build_shell_command(command: str, powershell_exe: Path = POWERSHELL_EXE) -> list[str]:
    """Build the platform shell invocation for a command string.

    Args:
        command: Command string interpreted by the selected system shell.
        powershell_exe: Windows PowerShell executable to use when present.

    Returns:
        Argument vector suitable for :func:`subprocess.run`.

    >>> build_shell_command("echo hello", Path("/missing/powershell"))
    ['/bin/sh', '-c', 'echo hello']
    """
    if powershell_exe.is_file():
        return [
            str(powershell_exe),
            "-NoLogo",
            "-NoProfile",
            "-NonInteractive",
            "-Command",
            command,
        ]
    return ["/bin/sh", "-c", command]


def run_command_capture(
    command: str,
    *,
    timeout: int = 120,
    powershell_exe: Path = POWERSHELL_EXE,
) -> tuple[int, str, str]:
    """Run a command and return its exit code and decoded output.

    Args:
        command: Command string interpreted by PowerShell or ``/bin/sh``.
        timeout: Maximum number of seconds the child may run.
        powershell_exe: Windows PowerShell executable to use when present.

    Returns:
        Tuple containing ``(return_code, stdout, stderr)``.

    >>> run_command_capture("printf hello", timeout=5, powershell_exe=Path("/missing"))  # doctest: +SKIP
    (0, 'hello', '')
    """
    result = subprocess.run(
        build_shell_command(command, powershell_exe),
        capture_output=True,
        text=True,
        timeout=timeout,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    return result.returncode, result.stdout or "", result.stderr or ""


def run_in_powershell(
    command: str,
    *,
    powershell_exe: Path = POWERSHELL_EXE,
) -> int:
    """Run a command with the parent process's standard streams.

    Args:
        command: Command string interpreted by PowerShell or ``/bin/sh``.
        powershell_exe: Windows PowerShell executable to use when present.

    Returns:
        Child process exit code.

    >>> run_in_powershell("exit 0", powershell_exe=Path("/missing"))  # doctest: +SKIP
    0
    """
    result = subprocess.run(
        build_shell_command(command, powershell_exe),
        stdin=sys.stdin,
        stdout=sys.stdout,
        stderr=sys.stderr,
        check=False,
    )
    return result.returncode


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command supplied on the command line.

    Args:
        argv: Command arguments excluding the program name.

    Returns:
        Child exit code, or ``2`` when no command was supplied.

    >>> main([])
    2
    """
    arguments = list(sys.argv[1:] if argv is None else argv)
    if not arguments:
        print("Usage: run_powershell.py <command> [args...]", file=sys.stderr)
        return 2
    return run_in_powershell(" ".join(arguments))


if __name__ == "__main__":
    raise SystemExit(main())
