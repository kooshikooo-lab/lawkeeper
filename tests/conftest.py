"""Shared pytest fixtures/helpers for lawkeeper's test suite.

``load_script`` was previously defined locally inside
``test_guard_scripts.py`` -- moved here so any test file can import
scripts/ modules without duplicating the loader (Law 3: never duplicate).
"""

import importlib.util
import subprocess
from pathlib import Path

import pytest

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


def _mk_repo(path, branch):
    subprocess.run(["git", "init", "-q", "-b", branch, str(path)], check=True)
    subprocess.run(["git", "-C", str(path), "-c", "user.name=t", "-c", "user.email=t@t",
                    "commit", "-q", "--allow-empty", "-m", "x"], check=True)
    return str(path).replace("\\", "/")


@pytest.fixture
def two_checkouts(tmp_path, monkeypatch):
    """Session folder on a feature branch; a second checkout on main."""
    feat = _mk_repo(tmp_path / "feat", "agent/topic/desktop")
    main = _mk_repo(tmp_path / "main", "main")
    monkeypatch.chdir(feat)
    return feat, main
