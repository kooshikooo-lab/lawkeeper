"""End-to-end smoke test for `lawkeeper init`.

Every other test in this suite imports guardrail/scripts directly from the
source checkout. That's fine for testing logic, but it means none of them
would ever notice if the PACKAGED version of lawkeeper is broken — which is
exactly what happened before this test existed: `pyproject.toml` declared
package-data relative to a `template/` folder that didn't live inside the
package, so a real `pip install`-ed wheel shipped with zero template files,
and `lawkeeper init` reported success while writing nothing but an empty
.guardrail.json.

This test closes that gap by doing what a real user does: build a wheel,
install it into a clean, isolated environment, and run `lawkeeper init`
against an actual git repo. It only passes if governance files really
land on disk.

This test is slow (it invokes `python -m build` and creates a venv) and
network-independent (build/venv use only what's already installed locally).
Run it explicitly in CI or before a release; it's excluded from the default
fast loop via the `slow` marker below if your CI wants to skip it day-to-day.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import venv
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]

pytestmark = pytest.mark.slow


def _run(cmd, cwd=None, check=True):
    result = subprocess.run(
        cmd, cwd=cwd, capture_output=True, text=True,
        encoding="utf-8", errors="replace",
    )
    if check and result.returncode != 0:
        raise AssertionError(
            f"command failed: {' '.join(cmd)}\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
    return result


@pytest.fixture(scope="module")
def installed_lawkeeper(tmp_path_factory):
    """Build a real wheel from this repo and pip-install it into a fresh venv.

    Returns the path to the venv's `lawkeeper` executable.
    """
    if shutil.which("git") is None:
        pytest.skip("git not available")

    work = tmp_path_factory.mktemp("lawkeeper-build")
    dist_dir = work / "dist"

    build_result = subprocess.run(
        [sys.executable, "-m", "build", "--wheel", "-o", str(dist_dir)],
        cwd=REPO_ROOT, capture_output=True, text=True,
        encoding="utf-8", errors="replace",
    )
    if build_result.returncode != 0:
        pytest.skip(
            f"`python -m build` unavailable or failed "
            f"(pip install build to run this test): {build_result.stderr[-500:]}"
        )

    wheels = list(dist_dir.glob("*.whl"))
    assert wheels, "build produced no wheel"

    venv_dir = work / "venv"
    venv.create(venv_dir, with_pip=True)
    venv_python = venv_dir / "bin" / "python"
    venv_lawkeeper = venv_dir / "bin" / "lawkeeper"
    if not venv_python.exists():  # Windows layout
        venv_python = venv_dir / "Scripts" / "python.exe"
        venv_lawkeeper = venv_dir / "Scripts" / "lawkeeper.exe"

    _run([str(venv_python), "-m", "pip", "install", "-q", str(wheels[0])])
    assert venv_lawkeeper.exists(), "lawkeeper entry point was not installed"
    return venv_lawkeeper


class TestInitFromRealInstall:
    """Run `lawkeeper init` the way an actual user would: after `pip install`,
    not from inside this source checkout."""

    def test_init_writes_the_constitution(self, installed_lawkeeper, tmp_path):
        repo = tmp_path / "project"
        repo.mkdir()
        _run(["git", "init", "-q"], cwd=repo)

        result = _run([str(installed_lawkeeper), "init", "."], cwd=repo)

        assert (repo / "docs" / "AI_CONSTITUTION.md").is_file(), (
            "lawkeeper init reported success but did not write the "
            "constitution — this is the exact silent-failure bug this "
            "test exists to catch"
        )
        assert (repo / "scripts" / "install_hooks.py").is_file()
        assert (repo / ".guardrail.json").is_file()
        assert "scaffolding written" in result.stdout

    def test_init_refuses_outside_a_git_repo(self, installed_lawkeeper, tmp_path):
        not_a_repo = tmp_path / "no-git-here"
        not_a_repo.mkdir()

        result = _run(
            [str(installed_lawkeeper), "init", "."],
            cwd=not_a_repo, check=False,
        )

        assert result.returncode != 0
        assert not (not_a_repo / ".guardrail.json").exists(), (
            "lawkeeper must never scaffold into a directory it could not "
            "confirm is a git repo root"
        )

    def test_init_refuses_to_silently_reinit(self, installed_lawkeeper, tmp_path):
        repo = tmp_path / "project2"
        repo.mkdir()
        _run(["git", "init", "-q"], cwd=repo)
        _run([str(installed_lawkeeper), "init", "."], cwd=repo)

        second = _run([str(installed_lawkeeper), "init", "."], cwd=repo, check=False)
        assert second.returncode != 0, "re-running init without --force must refuse"

        forced = _run(
            [str(installed_lawkeeper), "init", ".", "--force"], cwd=repo, check=False,
        )
        assert forced.returncode == 0, "--force must actually work"
