"""Meta-test: the shipped template must match the live project skeleton.

The template that `lawkeeper init` installs must stay in lock-step with the
live repo's own scripts/docs/hooks, otherwise the framework would self-install
something different from what it runs. (Law 16.5 spirit.)
"""

import shutil
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
ROOT = REPO_ROOT
TEMPLATE = REPO_ROOT / "template"

ROOT_DIRS = ["scripts", "scripts/git-hooks"]
ROOT_SCRIPT_FILES = [
    "scripts/guard_branch.py",
    "scripts/merge_gate.py",
    "scripts/system_audit.py",
    "scripts/validate_pre_commit.py",
    "scripts/validate_commit_msg.py",
    "scripts/guard_governance.py",
    "scripts/compliance_watchdog.py",
    "scripts/install_hooks.py",
    "scripts/governed_test.py",
]
ROOT_DOCS = [
    "docs/AI_CONSTITUTION.md",
    "docs/COMPLIANCE_CHECK.md",
    "docs/ARCHITECTURE_DECISIONS.md",
    "docs/AI_FAILURE_PATTERNS.md",
    "docs/TEST_THEORY.md",
]
HOOKS = ["pre-commit", "commit-msg", "pre-push"]


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="replace")


class TestTemplateSync:
    """Root live scripts must equal template scripts."""

    def _check(self, rel_root: str, rel_template: str):
        r = ROOT / rel_root
        t = TEMPLATE / rel_template
        assert r.exists(), f"missing root file {rel_root}"
        assert t.exists(), f"missing template file {rel_template}"
        assert _read(r) == _read(t), f"drift between {rel_root} and {rel_template}"

    def test_guard_branch_sync(self):
        self._check("scripts/guard_branch.py", "scripts/guard_branch.py")

    def test_merge_gate_sync(self):
        self._check("scripts/merge_gate.py", "scripts/merge_gate.py")

    def test_system_audit_sync(self):
        self._check("scripts/system_audit.py", "scripts/system_audit.py")

    def test_watchdog_sync(self):
        self._check("scripts/compliance_watchdog.py", "scripts/compliance_watchdog.py")

    def test_validate_pre_commit_sync(self):
        self._check("scripts/validate_pre_commit.py", "scripts/validate_pre_commit.py")

    def test_constitution_sync(self):
        self._check("docs/AI_CONSTITUTION.md", "docs/AI_CONSTITUTION.md")

    def test_test_theory_sync(self):
        self._check("docs/TEST_THEORY.md", "docs/TEST_THEORY.md")

    def test_governed_test_sync(self):
        self._check("scripts/governed_test.py", "scripts/governed_test.py")

    def test_hooks_sync(self):
        for h in HOOKS:
            self._check(f"scripts/git-hooks/{h}", f"scripts/git-hooks/{h}")


class TestTemplateCompleteness:
    """The template must contain the full starter kit."""

    def test_template_has_constitution(self):
        assert (TEMPLATE / "docs/AI_CONSTITUTION.md").is_file()

    def test_template_has_hooks(self):
        for h in HOOKS:
            assert (TEMPLATE / "scripts/git-hooks" / h).is_file()

    def test_template_has_ci(self):
        assert (TEMPLATE / ".github/workflows/governance-guard.yml").is_file()

    def test_template_has_guard_scripts(self):
        for s in ["guard_branch.py", "merge_gate.py", "system_audit.py"]:
            assert (TEMPLATE / "scripts" / s).is_file()
