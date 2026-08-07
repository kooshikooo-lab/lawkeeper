"""Tests for the guardrail law-runner framework (Law 16: guards have tests).

Pure tests where possible; the Law 15/16 end-to-end cases use a real git repo
created under tmp_path so git-bound behaviour is exercised without touching the
live repository state.
"""

import shutil
import subprocess
from pathlib import Path

import pytest

from guardrail.core.primitives import CheckResult, Law, Status
from guardrail.core.registry import load_law_classes, load_laws
from guardrail.core.runner import GuardrailRunner, Report
from guardrail.laws.law_01_readme import Law01
from guardrail.laws.law_09_adr import Law09
from guardrail.laws.law_12_read_fully import Law12
from guardrail.laws.law_14_audit_before_commit import Law14
from guardrail.laws.law_15_branch_naming import Law15
from guardrail.laws.law_16_enforcement import Law16

REPO_ROOT = Path(__file__).resolve().parents[1]


def _git(args, cwd):
    subprocess.run(
        ["git", *args],
        cwd=str(cwd), capture_output=True, text=True, check=True,
    )


def _init_repo(tmp_path: Path, branch: str) -> None:
    _git(["init", "-q"], tmp_path)
    _git(["checkout", "-q", "-b", branch], tmp_path)
    _git(["config", "user.email", "test@example.com"], tmp_path)
    _git(["config", "user.name", "test"], tmp_path)
    (tmp_path / "README.md").write_text("# test\n", encoding="utf-8")
    _git(["add", "."], tmp_path)
    _git(["commit", "-q", "-m", "init"], tmp_path)


# ── primitives ────────────────────────────────────────────────────────


class TestCheckResult:
    def test_failure_flag(self):
        assert CheckResult(1, Status.FAIL, "bad").is_failure
        assert not CheckResult(1, Status.PASS, "ok").is_failure
        assert not CheckResult(1, Status.WARN, "meh").is_failure


def test_law_is_abstract():
    with pytest.raises(TypeError):
        Law()  # type: ignore[abstract]


# ── registry ──────────────────────────────────────────────────────────


class TestRegistry:
    def test_law_classes_discovered(self):
        cls = load_law_classes()
        assert set(cls) == {1, 9, 12, 14, 15, 16}

    def test_load_laws_sorted_and_described(self):
        laws = load_laws()
        assert [l.law_id for l in laws] == [1, 9, 12, 14, 15, 16]
        for law in laws:
            assert law.title
            assert law.description

    def test_each_law_is_instance_of_law(self):
        for law in load_laws():
            assert isinstance(law, Law)


# ── runner ────────────────────────────────────────────────────────────


class TestReport:
    def test_summary_counts(self):
        report = Report(
            [
                CheckResult(1, Status.PASS, "ok"),
                CheckResult(1, Status.WARN, "meh"),
                CheckResult(1, Status.FAIL, "bad"),
            ],
            Path("."),
        )
        assert report.summary == {"pass": 1, "warn": 1, "fail": 1, "total": 3}
        assert report.exit_code == 1


class TestRunnerOnGovernedRepo:
    def _scaffold(self, tmp_path: Path) -> Path:
        (tmp_path / "README.md").write_text(
            "# project\n\ndeclares purpose and structure of this repository here.\n",
            encoding="utf-8",
        )
        (tmp_path / "AGENTS.md").write_text("governed\n", encoding="utf-8")
        (tmp_path / "docs").mkdir()
        (tmp_path / "docs/ARCHITECTURE_DECISIONS.md").write_text("# ADR\n", encoding="utf-8")
        (tmp_path / "scripts").mkdir()
        for name in ["validate_commit_msg.py", "validate_pre_commit.py"]:
            (tmp_path / "scripts" / name).write_text("", encoding="utf-8")
        (tmp_path / "scripts/git-hooks").mkdir()
        for name in ["commit-msg", "pre-commit"]:
            (tmp_path / "scripts/git-hooks" / name).write_text("", encoding="utf-8")
        (tmp_path / "tests").mkdir()
        (tmp_path / "tests/test_guard_scripts.py").write_text("", encoding="utf-8")
        (tmp_path / "scripts/guard_branch.py").write_text("", encoding="utf-8")
        (tmp_path / "scripts/guard_governance.py").write_text("", encoding="utf-8")
        (tmp_path / "scripts/compliance_watchdog.py").write_text("", encoding="utf-8")
        (tmp_path / "scripts/merge_gate.py").write_text("", encoding="utf-8")
        (tmp_path / "scripts/validate_imports.py").write_text("", encoding="utf-8")
        (tmp_path / ".guardrail.json").write_text("{}", encoding="utf-8")
        return tmp_path

    def test_all_portable_laws_pass(self, tmp_path):
        root = self._scaffold(tmp_path)
        report = GuardrailRunner(root).run(only={1, 9, 12, 14})
        assert report.exit_code == 0
        assert all(r.status.value == "pass" for r in report.results)

    def test_missing_readme_fails(self, tmp_path):
        root = self._scaffold(tmp_path)
        (root / "README.md").unlink()
        report = GuardrailRunner(root).run(only={1})
        assert report.exit_code == 1
        assert report.results[0].status == Status.FAIL


# ── Law 1 ─────────────────────────────────────────────────────────────


class TestLaw01:
    def test_missing(self, tmp_path):
        res = Law01().check(tmp_path, None)
        assert res[0].status == Status.FAIL

    def test_empty(self, tmp_path):
        (tmp_path / "README.md").write_text("x", encoding="utf-8")
        res = Law01().check(tmp_path, None)
        assert res[0].status == Status.WARN

    def test_present(self, tmp_path):
        (tmp_path / "README.md").write_text("a" * 40, encoding="utf-8")
        res = Law01().check(tmp_path, None)
        assert res[0].status == Status.PASS


# ── Law 9 ─────────────────────────────────────────────────────────────


class TestLaw09:
    def test_missing(self, tmp_path):
        res = Law09().check(tmp_path, None)
        assert res[0].status == Status.FAIL

    def test_present(self, tmp_path):
        (tmp_path / "docs").mkdir()
        (tmp_path / "docs/ARCHITECTURE_DECISIONS.md").write_text("# ADR\n", encoding="utf-8")
        res = Law09().check(tmp_path, None)
        assert res[0].status == Status.PASS


# ── Law 12 ────────────────────────────────────────────────────────────


class TestLaw12:
    def test_missing(self, tmp_path):
        res = Law12().check(tmp_path, None)
        assert res[0].status == Status.FAIL

    def test_present(self, tmp_path):
        (tmp_path / "AGENTS.md").write_text("x\n", encoding="utf-8")
        res = Law12().check(tmp_path, None)
        assert res[0].status == Status.PASS


# ── Law 14 ────────────────────────────────────────────────────────────


class TestLaw14:
    def test_missing(self, tmp_path):
        res = Law14().check(tmp_path, None)
        assert res[0].status == Status.FAIL

    def test_present(self, tmp_path):
        (tmp_path / "scripts").mkdir()
        for name in ["validate_commit_msg.py", "validate_pre_commit.py"]:
            (tmp_path / "scripts" / name).write_text("", encoding="utf-8")
        (tmp_path / "scripts/git-hooks").mkdir()
        for name in ["commit-msg", "pre-commit"]:
            (tmp_path / "scripts/git-hooks" / name).write_text("", encoding="utf-8")
        res = Law14().check(tmp_path, None)
        assert res[0].status == Status.PASS


# ── Law 15 ────────────────────────────────────────────────────────────


class TestLaw15:
    def test_feature_branch_passes(self, tmp_path, monkeypatch):
        _init_repo(tmp_path, "opencode/framework-mvp/desktop")
        (tmp_path / "scripts").mkdir(exist_ok=True)
        shutil.copy(REPO_ROOT / "scripts/guard_branch.py", tmp_path / "scripts/guard_branch.py")
        monkeypatch.chdir(tmp_path)
        res = Law15().check(tmp_path, None)
        assert res[0].status == Status.PASS

    def test_orphan_branch_fails(self, tmp_path, monkeypatch):
        _init_repo(tmp_path, "experiment/foo")
        (tmp_path / "scripts").mkdir(exist_ok=True)
        shutil.copy(REPO_ROOT / "scripts/guard_branch.py", tmp_path / "scripts/guard_branch.py")
        monkeypatch.chdir(tmp_path)
        res = Law15().check(tmp_path, None)
        assert res[0].status == Status.FAIL

    def test_no_guard_script_warns(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        res = Law15().check(tmp_path, None)
        assert res[0].status == Status.WARN


# ── Law 16 ────────────────────────────────────────────────────────────


class TestLaw16:
    def test_missing_guard_script_fails(self, tmp_path):
        res = Law16().check(tmp_path, None)
        assert res[0].status == Status.FAIL
        missing = res[0].details["missing"]
        assert any("guard_branch.py" in p for p in missing)

    def test_present_passes(self, tmp_path):
        root = tmp_path
        for p in [
            "scripts/guard_branch.py",
            "scripts/guard_governance.py",
            "scripts/compliance_watchdog.py",
            "scripts/merge_gate.py",
            "scripts/validate_imports.py",
            "scripts/validate_pre_commit.py",
            "scripts/validate_commit_msg.py",
            "tests/test_guard_scripts.py",
            ".guardrail.json",
        ]:
            path = root / p
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("", encoding="utf-8")
        res = Law16().check(tmp_path, None)
        assert res[0].status == Status.PASS


# ── framework self-hosting smoke test ─────────────────────────────────


class TestFrameworkSelfHost:
    def test_runner_green_on_lawkeeper_repo(self):
        report = GuardrailRunner(REPO_ROOT).run()
        failures = [r for r in report.results if r.status == Status.FAIL]
        assert not failures
        assert report.exit_code == 0
