"""Executor layer for lawkeeper (ADR-006).

Runs a governed ``Task`` and returns a framework-agnostic ``ExecutorResult``.
Backends (subprocess, OpenAI-compatible) sit behind one ``Executor`` protocol
so callers never depend on a specific backend.

This module intentionally does NOT import the framework core (Law/Status/
CheckResult). Mapping ``ExecutorResult`` to the framework's ``CheckResult`` is
the adapter's job and lives at the wiring point (see EXECUTOR_CONTRACT.md).
"""
from __future__ import annotations

import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Protocol


@dataclass
class Task:
    """A unit of governed work to execute."""

    id: str
    command: str | list[str]
    cwd: Optional[Path] = None
    timeout_s: float = 60.0
    env: dict = field(default_factory=dict)
    expected_exit: Optional[int] = None  # None = accept any exit code


@dataclass
class ExecutorResult:
    """Backend-neutral outcome of executing a Task."""

    exit_code: int
    stdout: str
    stderr: str
    duration_s: float
    timed_out: bool = False

    @property
    def status(self) -> str:
        """Coarse PASS/FAIL/ERROR verdict, independent of the framework.

        - timed out -> ERROR
        - exit code 0 -> PASS
        - non-zero, or mismatch with ``Task.expected_exit`` (caller checks) -> FAIL
        """
        if self.timed_out:
            return "ERROR"
        return "PASS" if self.exit_code == 0 else "FAIL"

    @property
    def combined_output(self) -> str:
        return (self.stdout or "") + ("\n" + self.stderr if self.stderr else "")


class Executor(Protocol):
    """Interface every backend implements (see ADR-006)."""

    def execute(self, task: Task, context: str = "") -> ExecutorResult:
        """Run ``task`` and return its result. ``context`` is free-form."""


class SubprocessExecutor:
    """Default backend: runs ``task.command`` in a subprocess with a timeout."""

    def __init__(self, shell: bool = False) -> None:
        self._shell = shell

    def execute(self, task: Task, context: str = "") -> ExecutorResult:
        started = time.monotonic()
        timed_out = False
        command = task.command if isinstance(task.command, (list, tuple)) else str(task.command)
        try:
            completed = subprocess.run(
                command,
                cwd=str(task.cwd) if task.cwd else None,
                shell=self._shell,
                timeout=task.timeout_s,
                capture_output=True,
                text=True,
                env=task.env or None,
                check=False,
            )
            exit_code = completed.returncode
            stdout = completed.stdout or ""
            stderr = completed.stderr or ""
        except subprocess.TimeoutExpired as exc:
            timed_out = True
            exit_code = -1
            stdout = exc.stdout or ""
            stderr = exc.stderr or ""
        except OSError as exc:
            exit_code = -2
            stdout = ""
            stderr = str(exc)
        duration = time.monotonic() - started
        return ExecutorResult(
            exit_code=exit_code,
            stdout=stdout,
            stderr=stderr,
            duration_s=duration,
            timed_out=timed_out,
        )
