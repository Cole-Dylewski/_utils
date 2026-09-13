"""Tests for the cross-platform command runner task."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import subprocess
from types import ModuleType

import pytest


def load_runner() -> ModuleType:
    """Load the task module without requiring ``tasks`` to be a package.

    Returns:
        Loaded ``run_powershell`` module.

    >>> load_runner().__name__
    'run_powershell'
    """
    path = Path(__file__).parents[2] / "tasks" / "run_powershell.py"
    spec = importlib.util.spec_from_file_location("run_powershell", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load command runner from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


RUNNER = load_runner()


def test_build_shell_command_prefers_existing_powershell(tmp_path: Path) -> None:
    """Use system PowerShell when the configured executable exists."""
    executable = tmp_path / "powershell.exe"
    executable.touch()

    command = RUNNER.build_shell_command("Write-Output ok", executable)

    assert command == [
        str(executable),
        "-NoLogo",
        "-NoProfile",
        "-NonInteractive",
        "-Command",
        "Write-Output ok",
    ]


def test_build_shell_command_falls_back_to_posix_shell(tmp_path: Path) -> None:
    """Use ``/bin/sh`` when Windows PowerShell is unavailable."""
    command = RUNNER.build_shell_command("printf ok", tmp_path / "missing.exe")

    assert command == ["/bin/sh", "-c", "printf ok"]


def test_run_command_capture_returns_child_result(monkeypatch: pytest.MonkeyPatch) -> None:
    """Return the child's code and text streams without altering them."""
    completed = subprocess.CompletedProcess(["shell"], 7, "output", "error")
    monkeypatch.setattr(RUNNER.subprocess, "run", lambda *args, **kwargs: completed)

    result = RUNNER.run_command_capture("ignored", powershell_exe=Path("/missing"))

    assert result == (7, "output", "error")


def test_main_requires_a_command(capsys: pytest.CaptureFixture[str]) -> None:
    """Reject an empty invocation with a conventional CLI usage code."""
    assert RUNNER.main([]) == 2
    assert "Usage:" in capsys.readouterr().err


def test_main_joins_arguments(monkeypatch: pytest.MonkeyPatch) -> None:
    """Preserve the reference runner's multi-argument CLI behavior."""
    commands: list[str] = []

    def fake_run(command: str, **_kwargs: object) -> int:
        commands.append(command)
        return 3

    monkeypatch.setattr(RUNNER, "run_in_powershell", fake_run)

    assert RUNNER.main(["echo", "hello"]) == 3
    assert commands == ["echo hello"]
