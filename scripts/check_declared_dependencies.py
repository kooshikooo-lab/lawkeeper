#!/usr/bin/env python3
"""Law 13 — Missing dependencies are bugs.

Verifies every dependency declared in pyproject.toml actually imports in
this environment. A declared-but-uninstalled dependency is a bug of the
same severity as a failing test, not something to silently skip around.

Not currently wired into any git hook (a standalone, manually/CI-run tool,
same pattern as compliance_watchdog.py and mine_failure_patterns.py) --
whether to make it commit-blocking is a separate decision, not made here.

Usage:
    python scripts/check_declared_dependencies.py
"""

from __future__ import annotations

import importlib
import re
import sys
import tomllib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PYPROJECT = REPO_ROOT / "pyproject.toml"

# PyPI distribution name -> actual importable module name, for the common
# cases where they differ. Extend as new mismatches are found -- this is
# not exhaustive, it's the known cases for this project's own dependencies
# plus the most common ones generally.
IMPORT_NAME_OVERRIDES = {
    "pyyaml": "yaml",
    "pillow": "PIL",
    "beautifulsoup4": "bs4",
    "python-dotenv": "dotenv",
    "scikit-learn": "sklearn",
    "opencv-python": "cv2",
}


def _package_name(requirement: str) -> str:
    """Strip a version specifier / extras marker off a requirement string."""
    name = re.split(r"[<>=!~\[; ]", requirement.strip())[0]
    return name.strip()


def _import_name(package_name: str) -> str:
    lower = package_name.lower()
    if lower in IMPORT_NAME_OVERRIDES:
        return IMPORT_NAME_OVERRIDES[lower]
    return package_name.replace("-", "_")


def check_group(requirements: list[str], label: str) -> list[str]:
    """Return the list of requirement strings that fail to import."""
    missing = []
    for req in requirements:
        pkg = _package_name(req)
        if not pkg:
            continue
        mod = _import_name(pkg)
        try:
            importlib.import_module(mod)
        except ImportError:
            missing.append(req)
    return missing


def main() -> int:
    if not PYPROJECT.exists():
        print(f"BLOCKED: {PYPROJECT} not found.", file=sys.stderr)
        return 1

    with open(PYPROJECT, "rb") as f:
        data = tomllib.load(f)

    project = data.get("project", {})
    required = project.get("dependencies", [])
    optional = project.get("optional-dependencies", {})

    missing_required = check_group(required, "dependencies")

    exit_code = 0
    if missing_required:
        print("BLOCKED — declared required dependencies are not installed (Law 13):", file=sys.stderr)
        for req in missing_required:
            print(f"  - {req}", file=sys.stderr)
        print("Fix: pip install -e . (or the specific package(s) above).", file=sys.stderr)
        exit_code = 1
    else:
        print(f"OK: all {len(required)} required dependencies import cleanly.")

    for extra_name, reqs in optional.items():
        missing = check_group(reqs, extra_name)
        if missing:
            print(f"NOTE: optional extra '{extra_name}' has uninstalled packages: {', '.join(missing)}")
            print(f"      (not blocking — install with: pip install -e .[{extra_name}])")
        else:
            print(f"OK: optional extra '{extra_name}' ({len(reqs)} package(s)) all import cleanly.")

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
