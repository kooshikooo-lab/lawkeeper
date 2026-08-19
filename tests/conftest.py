"""Shared pytest fixtures/helpers for lawkeeper's test suite.

``load_script`` was previously defined locally inside
``test_guard_scripts.py`` -- moved here so any test file can import
scripts/ modules without duplicating the loader (Law 3: never duplicate).
"""

import importlib.util
import subprocess
from pathlib import Path

REPO_ROOT = Path(subprocess.run(
    ["git", "rev-parse", "--show-toplevel"],
    capture_output=True, text=True, encoding="utf-8", errors="replace"
).stdout.strip() or Path(__file__).resolve().parents[1])


def load_script(name: str):
    """Import a scripts/ module by path (they are not a package)."""
    path = REPO_ROOT / "scripts" / name
    spec = importlib.util.spec_from_file_location(f"guardtest_{name[:-3]}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
