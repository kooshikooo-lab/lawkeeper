"""End-to-end tests for lawkeeper using real git repos.

Covers the approved e2e plan (tests/e2e_PLAN.md):
  1. own commits      — scaffold a governed repo, commit, `lawkeeper run` passes
  2. bugs             — missing README, orphan branch -> FAIL
  3. commit-msg gate  — .py change without Tests:/Verification: is blocked
  4. pre-commit gate  — bare except / wrong placement is blocked
  5. conflicts        — merge_gate predicts conflict (rc1) and clean (rc0)

These run real git in tmp_path. They do not touch the live repo's branches.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from guardrail.core import Status
from guardrail.core.runner import GuardrailRunner

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = REPO_ROOT / "scripts"


def _git(cwd, *args):
    return subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        check=True,
    )


def _git_repo(tmp_path: Path) -> Path:
    _git(tmp_path, "init", "-b", "main", "-q")
    _git(tmp_path, "config", "user.email", "t@example.com")
    _git(tmp_path, "config", "user.name", "test")
    return tmp_path


# Files every governed repo needs for the portable laws to pass, plus the real
# guard_branch.py (Law 15 reuses its classifier).
GUARDED_GUARD_SCRIPT = "guard_branch.py"
STUB_GUARD_SCRIPTS = [
    "guard_governance.py",
    "compliance_watchdog.py",
    "merge_gate.py",
    "validate_imports.py",
    "validate_pre_commit.py",
    "validate_commit_msg.py",
    "system_audit.py",
    "toolcheck.py",
    "check_local_dependencies.py",
    "install_hooks.py",
]


def _scaffold_governed(tmp_path: Path) -> Path:
    repo = _git_repo(tmp_path)
    _git(repo, "checkout", "-b", "opencode/e2e/desktop")
    (repo / "README.md").write_text(
        "# project\n\nPurpose and structure of this repo are declared here.\n",
        encoding="utf-8",
    )
    (repo / "AGENTS.md").write_text("Working agreement for the session.\n", encoding="utf-8")
    (repo / "docs").mkdir()
    (repo / "docs/ARCHITECTURE_DECISIONS.md").write_text("# ADR\n", encoding="utf-8")
    scripts = repo / "scripts"
    scripts.mkdir()
    (scripts / GUARDED_GUARD_SCRIPT).write_bytes(
        (SCRIPTS / GUARDED_GUARD_SCRIPT).read_bytes()
    )
    for name in STUB_GUARD_SCRIPTS:
        (scripts / name).write_text("", encoding="utf-8")
    hooks = scripts / "git-hooks"
    hooks.mkdir()
    for name in ["pre-commit", "commit-msg", "pre-push"]:
        (hooks / name).write_text("", encoding="utf-8")
    (repo / "tests").mkdir()
    (repo / "tests/test_guard_scripts.py").write_text("", encoding="utf-8")
    (repo / "test_governance/cards").mkdir(parents=True)
    (repo / "test_governance/cards/test_guard_scripts.yaml").write_text(
        "test_id: test_guard_scripts\n"
        "theory: guard scripts must be tested (Law 16).\n"
        "oracle:\n"
        "  type: invariant\n"
        "  independence: independent\n"
        "acceptance: guard rules hold\n"
        "blind_spot: simulated inputs only\n"
        "trust_level: T2\n"
        "adversarial_review: none\n"
        "failure_meaning:\n"
        "  failed: a guard rule regressed\n"
        "  crash: import failure\n"
        "  pass: guards correct\n"
        "debug:\n"
        "  - check the guard script\n",
        encoding="utf-8",
    )
    (repo / "scripts/governed_test.py").write_text("", encoding="utf-8")
    (repo / "docs/TEST_THEORY.md").write_text("# theory\n", encoding="utf-8")
    (repo / ".guardrail.json").write_text("{}", encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "chore: e2e governed scaffold\n\nTests: n/a")
    return repo


# ── 1. own commits: governed repo passes ─────────────────────────────


class TestGovernedRepo:
    def test_lawkeeper_run_is_green(self, tmp_path):
        root = _scaffold_governed(tmp_path)
        report = GuardrailRunner(root).run()
        assert report.exit_code == 0
        assert report.failures() == []

    def test_law_l15_feature_branch_passes(self, tmp_path):
        root = _scaffold_governed(tmp_path)
        report = GuardrailRunner(root).run(only={15})
        assert report.results[0].status == Status.PASS


# ── 2. bugs: lawkeeper catches bad state ─────────────────────────────


class TestBugs:
    def test_missing_readme_fails(self, tmp_path):
        root = _scaffold_governed(tmp_path)
        (root / "README.md").unlink()
        report = GuardrailRunner(root).run(only={1})
        assert report.exit_code == 1
        assert report.results[0].status == Status.FAIL

    def test_orphan_branch_fails(self, tmp_path):
        root = _scaffold_governed(tmp_path)
        _git(root, "checkout", "-b", "experiment/bad")
        report = GuardrailRunner(root).run(only={15})
        assert report.exit_code == 1
        assert report.results[0].status == Status.FAIL

    def test_missing_adr_fails(self, tmp_path):
        root = _scaffold_governed(tmp_path)
        (root / "docs/ARCHITECTURE_DECISIONS.md").unlink()
        report = GuardrailRunner(root).run(only={9})
        assert report.exit_code == 1


# ── 3. commit-msg gate (Law 14) ────────────────────────────────────────


class TestCommitMsgGate:
    def _run_validator(self, repo, message_file):
        msg = (repo / ".git") / message_file
        return subprocess.run(
            [sys.executable, str(SCRIPTS / "validate_commit_msg.py"), str(msg)],
            cwd=str(repo), capture_output=True, text=True,
        )

    def test_py_change_without_tests_is_blocked(self, tmp_path):
        repo = _git_repo(tmp_path)
        (repo / "foo.py").write_text("x = 1\n", encoding="utf-8")
        _git(repo, "add", "foo.py")
        (repo / ".git" / "bad").write_text("fix bug\n", encoding="utf-8")
        result = self._run_validator(repo, "bad")
        assert result.returncode == 1
        out = result.stdout + result.stderr
        assert "Tests:" in out or "Verification:" in out

    def test_py_change_with_tests_passes(self, tmp_path):
        repo = _git_repo(tmp_path)
        (repo / "foo.py").write_text("x = 1\n", encoding="utf-8")
        _git(repo, "add", "foo.py")
        (repo / ".git" / "good").write_text("fix bug\n\nTests: python -m pytest\n", encoding="utf-8")
        result = self._run_validator(repo, "good")
        assert result.returncode == 0


# ── 4. pre-commit gate ────────────────────────────────────────────────


class TestPreCommitGate:
    def _run_precommit(self, repo):
        # validate_pre_commit shells out to scripts/validate_imports.py when
        # staged .py files exist, so provide it in the tmp repo.
        shutil.copy(SCRIPTS / "validate_imports.py", repo / "scripts" / "validate_imports.py")
        return subprocess.run(
            [sys.executable, str(SCRIPTS / "validate_pre_commit.py")],
            cwd=str(repo), capture_output=True, text=True,
        )

    def test_bare_except_is_blocked(self, tmp_path):
        repo = _git_repo(tmp_path)
        (repo / "scripts").mkdir()
        (repo / "foo.py").write_text("try:\n    pass\nexcept:\n    pass\n", encoding="utf-8")
        _git(repo, "add", "foo.py")
        result = self._run_precommit(repo)
        assert result.returncode == 1
        assert "bare except" in (result.stdout + result.stderr)

    def test_clean_file_is_accepted(self, tmp_path):
        repo = _git_repo(tmp_path)
        (repo / "scripts").mkdir()
        (repo / "foo.py").write_text("x = 1\n", encoding="utf-8")
        _git(repo, "add", "foo.py")
        result = self._run_precommit(repo)
        assert result.returncode == 0


# ── 5. conflicts: merge_gate predicts conflict / clean ─────────────────


class TestMergeGateConflicts:
    def _run(self, repo, base, head):
        return subprocess.run(
            [sys.executable, str(SCRIPTS / "merge_gate.py"), base, head],
            cwd=str(repo), capture_output=True, text=True,
        )

    def _two_siblings(self, tmp_path):
        repo = _git_repo(tmp_path)
        (repo / "f.txt").write_text("a\n", encoding="utf-8")
        _git(repo, "add", ".")
        _git(repo, "commit", "-q", "-m", "base")
        _git(repo, "checkout", "-qb", "opencode/a/desktop")
        (repo / "f.txt").write_text("B\n", encoding="utf-8")
        _git(repo, "add", ".")
        _git(repo, "commit", "-q", "-m", "a")
        _git(repo, "checkout", "-q", "main")
        (repo / "f.txt").write_text("C\n", encoding="utf-8")
        _git(repo, "add", ".")
        _git(repo, "commit", "-q", "-m", "c")
        return repo

    def test_conflict_is_predicted(self, tmp_path):
        repo = self._two_siblings(tmp_path)
        result = self._run(repo, "main", "opencode/a/desktop")
        assert result.returncode == 1
        assert "CONFLICT" in (result.stdout + result.stderr)

    def test_clean_merge_passes(self, tmp_path):
        repo = _git_repo(tmp_path)
        (repo / "f.txt").write_text("a\n", encoding="utf-8")
        _git(repo, "add", ".")
        _git(repo, "commit", "-q", "-m", "base")
        _git(repo, "checkout", "-qb", "opencode/a/desktop")
        (repo / "g.txt").write_text("g\n", encoding="utf-8")
        _git(repo, "add", ".")
        _git(repo, "commit", "-q", "-m", "a")
        _git(repo, "checkout", "-q", "main")
        (repo / "h.txt").write_text("h\n", encoding="utf-8")
        _git(repo, "add", ".")
        _git(repo, "commit", "-q", "-m", "h")
        result = self._run(repo, "main", "opencode/a/desktop")
        assert result.returncode == 0
