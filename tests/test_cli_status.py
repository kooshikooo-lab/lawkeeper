"""Tests for guardrail.cli.cmd_status() and the 2026-09-06 project_name fix.

No test coverage existed for cmd_status() at all before this pass (found
while wiring up the last of the 6 decorative Config fields, guardrail fit
investigation task 4) -- writing real coverage for it surfaced a second,
separate real bug: guardrail.cli._repo_root()'s `start: Path = Path.cwd()`
default is evaluated once at module-import time, not per-call (a classic
Python eager-default-argument bug), so a test that imports guardrail.cli
and then chdir's to an isolated tmp_path would have silently resolved
against the wrong (real) repo instead of the test's own directory. Fixed
alongside project_name itself; both are exercised together here since the
project_name fix is what made writing a real test for cmd_status() happen
in the first place.
"""

import argparse
import json
import subprocess

from guardrail import cli


def _init_repo(tmp_path, monkeypatch):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "t@t.com"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=tmp_path, check=True)
    monkeypatch.chdir(tmp_path)


class TestRepoRootIsResolvedFreshPerCall:
    def test_no_arg_resolves_the_real_current_directory_not_a_stale_one(
        self, tmp_path, monkeypatch
    ):
        """Real regression test for the eager-default bug: guardrail.cli
        is already imported (by this test module, and likely earlier by
        pytest's own collection of other test files) before this test's
        chdir runs -- if _repo_root()'s default were still `Path.cwd()`
        evaluated at import time, this would resolve to wherever pytest
        started, not tmp_path."""
        _init_repo(tmp_path, monkeypatch)
        assert cli._repo_root() == tmp_path.resolve()


class TestCmdStatusProjectName:
    def test_governed_repo_shows_the_real_project_name(self, tmp_path, monkeypatch, capsys):
        """Real bug found 2026-09-06: this line used to print only the
        literal word "project:" followed by governed/ungoverned status --
        project_name was written into .guardrail.json by `lawkeeper init`
        but never read back anywhere, including here."""
        _init_repo(tmp_path, monkeypatch)
        (tmp_path / ".guardrail.json").write_text(
            json.dumps({"project_name": "orbital-study"}), encoding="utf-8"
        )
        code = cli.cmd_status(argparse.Namespace())
        out = capsys.readouterr().out
        assert code == 0
        assert "orbital-study" in out
        assert "(governed)" in out

    def test_ungoverned_repo_reports_ungoverned_without_a_name(
        self, tmp_path, monkeypatch, capsys
    ):
        _init_repo(tmp_path, monkeypatch)
        code = cli.cmd_status(argparse.Namespace())
        out = capsys.readouterr().out
        assert code == 0
        assert "NOT governed by lawkeeper" in out

    def test_missing_project_name_falls_back_to_the_default(self, tmp_path, monkeypatch, capsys):
        """A .guardrail.json written before project_name existed, or one
        that simply omits it, must fail safe to Config's own default
        rather than crash or print a blank name."""
        _init_repo(tmp_path, monkeypatch)
        (tmp_path / ".guardrail.json").write_text(json.dumps({}), encoding="utf-8")
        code = cli.cmd_status(argparse.Namespace())
        out = capsys.readouterr().out
        assert code == 0
        assert "my-project" in out  # Config.DEFAULTS["project_name"]

    def test_not_a_git_repo_fails_before_reading_any_config(self, tmp_path, monkeypatch, capsys):
        monkeypatch.chdir(tmp_path)
        code = cli.cmd_status(argparse.Namespace())
        out = capsys.readouterr().out
        assert code == 1
        assert "not inside a git repository" in out
