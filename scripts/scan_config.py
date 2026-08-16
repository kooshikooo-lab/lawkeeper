"""Shared scan-path resolution for Lawkeeper's own guard scripts
(compliance_watchdog.py, check_local_dependencies.py).

Fixes a real bug: both scripts used to hardcode `backend/` and
`woodwind_designer/` - directories from the Windwright project this
repo was originally extracted from. Lawkeeper's own compliance tools
never scanned Lawkeeper's own src/guardrail/ as a result - a governance
tool that couldn't see itself. One shared resolver instead of two
separately-hardcoded (and separately buggy) copies.
"""
from __future__ import annotations

import json
from pathlib import Path


def get_scan_paths(repo_root: Path) -> list[Path]:
    """Directories to scan for compliance/dependency checks, in priority order:

    1. `.guardrail.json`'s "scan_paths" (explicit project config - what
       `lawkeeper init` lets a project tell its own tooling to scan,
       written by the project owner, not guessed).
    2. Auto-detected package directories under `src/`, for projects using
       the common src-layout (this repo included). Deliberately does NOT
       guess the package name from pyproject.toml's [project].name - this
       repo is the reason why: its distribution name is "lawkeeper" but
       the actual package directory is `src/guardrail/` (a documented,
       deliberate rename - see pyproject.toml's package-data comment).
       Guessing `src/<project.name>` would have missed it entirely, the
       same "governance tool that can't see itself" bug all over again.
       Instead, every direct subdirectory of `src/` containing an
       `__init__.py` is treated as a real package and scanned.
    3. `scripts/` and `tests/` at the repo root, since those exist in most
       Lawkeeper-governed projects regardless of source layout.

    Never falls back to another, unrelated project's directories - that
    was the actual bug being fixed here.
    """
    guardrail_json = repo_root / ".guardrail.json"
    if guardrail_json.exists():
        try:
            cfg = json.loads(guardrail_json.read_text(encoding="utf-8"))
            configured = cfg.get("scan_paths")
            if configured:
                return [repo_root / p for p in configured]
        except (OSError, ValueError):
            pass

    paths: list[Path] = []
    src_dir = repo_root / "src"
    if src_dir.is_dir():
        for entry in sorted(src_dir.iterdir()):
            if entry.is_dir() and (entry / "__init__.py").exists():
                paths.append(entry)

    for extra in ("scripts", "tests"):
        p = repo_root / extra
        if p.exists() and p not in paths:
            paths.append(p)

    return paths


def get_oversized_allowlist(repo_root: Path) -> set[str]:
    """Files allowed to exceed the module-size check without failing.

    Was hardcoded to a list of Windwright ('backend/', 'woodwind_designer/')
    file paths that can never match anything under this repo's own scan
    paths - a dead allowlist protecting nothing. Configurable via
    `.guardrail.json`'s "oversized_allowlist" (repo-root-relative paths);
    empty by default.
    """
    guardrail_json = repo_root / ".guardrail.json"
    if guardrail_json.exists():
        try:
            cfg = json.loads(guardrail_json.read_text(encoding="utf-8"))
            return set(cfg.get("oversized_allowlist", []))
        except (OSError, ValueError):
            pass
    return set()
