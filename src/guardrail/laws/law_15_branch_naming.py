"""Law 15 — Branch governance.

Reuses scripts/guard_branch.py classification (single source of truth). Reports
the current branch's Law 15 namespace; orphan branches are FAIL.
"""
from __future__ import annotations

import importlib.util
import subprocess
from pathlib import Path

from guardrail.core.primitives import CheckResult, Law, Status

GUARD_SCRIPT = "scripts/guard_branch.py"


def _current_branch(repo_root: Path) -> str:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            timeout=5,
        )
        return out.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return ""


def _load_guard_branch(repo_root: Path):
    path = repo_root / GUARD_SCRIPT
    if not path.exists():
        return None
    spec = importlib.util.spec_from_file_location("_law15_guard_branch", path)
    if spec is None or spec.loader is None:
        return None
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception:
        return None
    return module


class Law15(Law):
    law_id = 15
    title = "Branch governance"
    severity = "must"

    @property
    def description(self) -> str:
        return "Branches live in exactly one of: main, opencode/main/<machine>, opencode/<topic>/<machine>, merge/<topic>."

    def check(self, repo_root: Path, config) -> list[CheckResult]:
        guard = _load_guard_branch(repo_root)
        if guard is None:
            return [
                CheckResult(
                    15,
                    Status.WARN,
                    "guard_branch.py not found — Law 15 cannot be enforced here.",
                    {"file": GUARD_SCRIPT},
                )
            ]
        name = _current_branch(repo_root)
        if not name or name == "HEAD":
            return [
                CheckResult(
                    15,
                    Status.PASS,
                    "No branch checked out; Law 15 not applicable.",
                    {"branch": name or "(none)"},
                )
            ]
        namespace = guard.classify(name)
        if namespace is None:
            return [
                CheckResult(
                    15,
                    Status.FAIL,
                    f"Branch '{name}' is an orphan — not in a Law 15 namespace.",
                    {"branch": name},
                )
            ]
        return [
            CheckResult(
                15,
                Status.PASS,
                f"Branch '{name}' is {namespace} (Law 15 compliant).",
                {"branch": name, "namespace": namespace},
            )
        ]
