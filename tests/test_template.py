"""Meta-test: the shipped template must match the live project skeleton.

The template that `lawkeeper init` installs must stay in lock-step with the
live repo's own scripts/docs/hooks, otherwise the framework would self-install
something different from what it runs. (Law 16.5 spirit.)
"""

import shutil
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
ROOT = REPO_ROOT
# The shipped template lives INSIDE the package (src/guardrail/template) so
# that setuptools package-data can actually include it in a built wheel.
# A template/ folder at the repo root (sibling of src/) looks convenient in
# a source checkout but silently does not ship — that was the root cause of
# `lawkeeper init` succeeding with zero files once installed from a wheel.
TEMPLATE = REPO_ROOT / "src" / "guardrail" / "template"
# Opt-in tree, installed only by `lawkeeper init --with-tools` (ADR-009):
# general LLM-orchestration tools, not governance enforcement, kept out of
# the default scaffold. Ships from the same package via a second
# package-data entry (pyproject.toml) — see cli.py's _extras_template_root.
TEMPLATE_EXTRAS = REPO_ROOT / "src" / "guardrail" / "template_extras"
EXTRAS_TOOL_FILES = ["ai_review.py", "consensus_review.py", "team_chat.py"]

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

    def test_validate_commit_msg_sync(self):
        self._check("scripts/validate_commit_msg.py", "scripts/validate_commit_msg.py")

    def test_guard_governance_sync(self):
        self._check("scripts/guard_governance.py", "scripts/guard_governance.py")

    # test_install_hooks_sync deliberately NOT added here yet: verified
    # 2026-09-04 that scripts/install_hooks.py and its template copy have
    # already drifted for real (install_claude_stop_hook() exists only in
    # the dev copy) -- see docs/ARCHITECTURE_REVIEW_2026-09-04.md, item 2.
    # Whether the template should ship that function is a real, undecided
    # call, not something to settle silently by adding a test that forces
    # one side to change.

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


class TestTemplateExtrasSplit:
    """ADR-009: ai_review.py/consensus_review.py/team_chat.py are general
    tools, not governance enforcement — they must ship from the opt-in
    template_extras/ tree only, never from the default template/ tree, so
    a plain `lawkeeper init` stays governance-only (matching the package's
    stated purpose, per docs/ARCHITECTURE_REVIEW_2026-09-04.md item 3)."""

    def test_extras_tree_has_the_tools(self):
        for f in EXTRAS_TOOL_FILES:
            assert (TEMPLATE_EXTRAS / "scripts" / f).is_file(), (
                f"template_extras/scripts/{f} missing — --with-tools would "
                f"silently install fewer files than expected"
            )

    def test_base_template_does_not_have_the_tools(self):
        for f in EXTRAS_TOOL_FILES:
            assert not (TEMPLATE / "scripts" / f).exists(), (
                f"scripts/{f} found back in the default template/ tree — "
                f"this would re-bundle a general tool into every plain "
                f"`lawkeeper init`, undoing ADR-009's split"
            )

    def test_consensus_review_sibling_import_will_resolve(self):
        """consensus_review.py does `from blockers import report_blocker`
        as a sibling import (sys.path.insert of its own dir only) — this
        only works because _extras_template_root's files land in the same
        destination directory as the base template's blockers.py. Real
        regression this guards: if blockers.py were ever removed from the
        base template, --with-tools would install a script that crashes
        on import."""
        assert (TEMPLATE / "scripts" / "blockers.py").is_file()
        assert (TEMPLATE_EXTRAS / "scripts" / "consensus_review.py").is_file()
