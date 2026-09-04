"""Tests for scripts/system_audit.py's check_import_boundaries().

Real bug class this guards against: a tool that exists but silently stops
being wired in (e.g. .importlinter present but never actually run, or
lint-imports uninstalled and the failure swallowed) is worse than no tool at
all -- it creates the appearance of an enforced boundary with none actually
active. See .importlinter's own header comment and the real user directive
it quotes (shared_memory/user-quality-standard-escalation-and-cross-repo-
sharing-2026-09-04.md).
"""

from __future__ import annotations

import textwrap
from pathlib import Path

from conftest import load_script

system_audit = load_script("system_audit.py")


class TestCheckImportBoundariesNoConfig:
    def test_no_importlinter_file_is_not_applicable(self, tmp_path, monkeypatch):
        monkeypatch.setattr(system_audit, "REPO_ROOT", tmp_path)
        assert system_audit.check_import_boundaries() == []


class TestCheckImportBoundariesMissingTool:
    def test_config_exists_but_lint_imports_not_installed(self, tmp_path, monkeypatch):
        (tmp_path / ".importlinter").write_text("[importlinter]\n", encoding="utf-8")
        monkeypatch.setattr(system_audit, "REPO_ROOT", tmp_path)
        monkeypatch.setattr(system_audit.shutil, "which", lambda _name: None)
        problems = system_audit.check_import_boundaries()
        assert len(problems) == 1
        assert "not installed" in problems[0]
        assert "pip install import-linter" in problems[0]


class TestCheckImportBoundariesRealRepo:
    """Runs the real lint-imports binary against THIS repo's real
    .importlinter -- a live regression check, not a mock, matching this
    suite's own preference for real subprocess/reference behavior (see
    test_executor.yaml's oracle) over asserting against the tool's own
    reported values."""

    def test_this_repos_own_contracts_currently_pass(self):
        # Deliberately does NOT monkeypatch REPO_ROOT -- uses the real one,
        # so this test fails for real if someone breaks the layering these
        # contracts lock in (core/laws/memory importing cli.py; laws<->core
        # going the wrong direction; memory depending on core/laws).
        assert system_audit.check_import_boundaries() == []


class TestCheckImportBoundariesCatchesRealViolation:
    """Adversarial: builds a real, separate two-module package with a real
    forbidden import and confirms lint-imports actually reports it -- not
    assumed from the tool's own docs. Mirrors the manual verification done
    while writing .importlinter (temporarily breaking primitives.py's real
    import graph, confirming the failure, then reverting)."""

    def test_a_real_forbidden_import_is_caught(self, tmp_path, monkeypatch):
        pkg = tmp_path / "fakepkg"
        pkg.mkdir()
        (pkg / "__init__.py").write_text("", encoding="utf-8")
        (pkg / "inner.py").write_text("from fakepkg import outer\n", encoding="utf-8")
        (pkg / "outer.py").write_text("", encoding="utf-8")

        (tmp_path / ".importlinter").write_text(
            textwrap.dedent(
                """\
                [importlinter]
                root_packages =
                    fakepkg

                [importlinter:contract:inner-never-imports-outer]
                name = inner never imports outer
                type = forbidden
                source_modules =
                    fakepkg.inner
                forbidden_modules =
                    fakepkg.outer
                """
            ),
            encoding="utf-8",
        )

        monkeypatch.setattr(system_audit, "REPO_ROOT", tmp_path)
        monkeypatch.chdir(tmp_path)
        monkeypatch.syspath_prepend(str(tmp_path))

        problems = system_audit.check_import_boundaries()

        assert len(problems) == 1
        assert "broken contract" in problems[0]
        assert "fakepkg.inner" in problems[0]
        assert "fakepkg.outer" in problems[0]
