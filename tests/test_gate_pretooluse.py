"""Tests for gate_pretooluse.py -- the live PreToolUse gate on Bash
commands that would force-push over or delete a canonical branch.

Uses the real guard_branch.py classification (same convention as
test_guard_scripts.py: "main" is real-canonical in this repo, an
unrelated feature-shaped name is not) rather than mocking it -- these
tests exercise real classification behavior, not a stand-in for it.
"""
import json
import subprocess
import sys

import pytest

from conftest import REPO_ROOT, load_script

gate = load_script("gate_pretooluse.py")


# ── inspect_command: hardline tier -- no ask path exists for these ─────

class TestHardlineForcePush:
    def test_force_push_to_main_is_hardline(self):
        risk = gate.inspect_command("git push --force origin main")
        assert risk is not None
        assert risk.level == "hardline"
        assert risk.branch == "main"

    def test_short_flag_force_push_to_main_is_hardline(self):
        risk = gate.inspect_command("git push -f origin main")
        assert risk.level == "hardline"

    def test_force_with_lease_to_main_is_hardline(self):
        risk = gate.inspect_command("git push --force-with-lease origin main")
        assert risk.level == "hardline"

    def test_plus_prefix_refspec_to_main_is_hardline(self):
        risk = gate.inspect_command("git push origin +main")
        assert risk.level == "hardline"
        assert risk.branch == "main"

    def test_colon_refspec_delete_of_main_is_hardline(self):
        risk = gate.inspect_command("git push origin :main")
        assert risk.level == "hardline"
        assert risk.branch == "main"

    def test_force_push_to_feature_branch_is_not_flagged(self):
        risk = gate.inspect_command("git push --force origin opencode/mesh-repair/laptop")
        assert risk is None

    def test_ordinary_push_is_never_flagged(self):
        assert gate.inspect_command("git push origin main") is None
        assert gate.inspect_command("git push") is None

    def test_chained_command_is_still_inspected(self):
        """A hardline-dangerous command hidden after && must not slip
        through just because it isn't the first command on the line."""
        risk = gate.inspect_command("npm test && git push --force origin main")
        assert risk is not None
        assert risk.level == "hardline"

    def test_force_push_with_no_explicit_branch_resolves_current_branch(self, monkeypatch):
        monkeypatch.setattr(gate.guard_branch, "run_git", lambda args: ("main", 0))
        risk = gate.inspect_command("git push --force")
        assert risk is not None
        assert risk.level == "hardline"
        assert risk.branch == "main"

    def test_force_push_with_no_explicit_branch_on_feature_branch_not_flagged(self, monkeypatch):
        monkeypatch.setattr(gate.guard_branch, "run_git",
                             lambda args: ("opencode/mesh-repair/laptop", 0))
        assert gate.inspect_command("git push --force") is None


class TestHardlineBranchDelete:
    def test_delete_main_is_hardline(self):
        risk = gate.inspect_command("git branch -D main")
        assert risk.level == "hardline"
        assert risk.branch == "main"

    def test_delete_feature_branch_is_not_flagged(self):
        assert gate.inspect_command("git branch -D opencode/mesh-repair/laptop") is None

    def test_soft_delete_flag_without_force_delete_not_flagged(self):
        # -d (lowercase) on git branch is the safe, merged-only delete;
        # still routed through the same delete-flag set intentionally
        # (git refuses an unmerged -d anyway) but must not crash.
        risk = gate.inspect_command("git branch -d main")
        assert risk.level == "hardline"


# ── --dry-run: git's own no-mutation guarantee, never flagged ───────────

class TestDryRunNeverFlagged:
    """Found live: a real end-to-end test of this hook
    (`git push --force --dry-run origin main`, run to safely verify the
    hook without risking a real push) got hardline-denied before this
    exemption existed. --dry-run structurally cannot mutate the remote,
    so blocking it was a pure false positive, not extra safety."""

    def test_dry_run_force_push_to_main_is_never_flagged(self):
        assert gate.inspect_command("git push --force --dry-run origin main") is None

    def test_short_flag_dry_run_force_push_to_main_is_never_flagged(self):
        assert gate.inspect_command("git push -f -n origin main") is None

    def test_dry_run_delete_refspec_of_main_is_never_flagged(self):
        assert gate.inspect_command("git push --dry-run origin :main") is None

    def test_dry_run_does_not_exempt_a_chained_real_push(self):
        """Not a bypass: a real push chained after a dry-run one is still
        inspected independently, on its own merits."""
        risk = gate.inspect_command("git push --dry-run origin main && git push --force origin main")
        assert risk is not None
        assert risk.level == "hardline"

    def test_dry_run_does_not_exempt_branch_delete(self):
        """--dry-run only exists as a git-push concept; git branch -D has
        no equivalent no-mutation flag, so this must not accidentally
        exempt branch deletion too."""
        risk = gate.inspect_command("git branch -D --dry-run main")
        assert risk is not None
        assert risk.level == "hardline"


# ── ask tier -- genuine uncertainty, never silently allowed ─────────────

class TestAskTierAmbiguousTargets:
    def test_force_push_to_shell_variable_branch_is_ask_not_silent_allow(self):
        risk = gate.inspect_command("git push --force origin $BRANCH")
        assert risk is not None
        assert risk.level == "ask"

    def test_force_push_with_command_substitution_is_ask(self):
        risk = gate.inspect_command('git push --force origin "$(git branch --show-current)"')
        assert risk is not None
        assert risk.level == "ask"

    def test_force_push_no_branch_current_branch_unresolvable_is_ask(self, monkeypatch):
        monkeypatch.setattr(gate.guard_branch, "run_git", lambda args: ("", 1))
        risk = gate.inspect_command("git push --force")
        assert risk is not None
        assert risk.level == "ask"

    def test_branch_delete_shell_variable_target_is_ask(self):
        risk = gate.inspect_command("git branch -D $BRANCH")
        assert risk is not None
        assert risk.level == "ask"


# ── the override -- deliberate, out-of-band, set before the session ────

class TestHardlineOverride:
    def test_hardline_denied_without_override(self, monkeypatch):
        monkeypatch.delenv("GUARD_BRANCH_ALLOW_FORCE", raising=False)
        decision = gate.decide("Bash", {"command": "git push --force origin main"})
        assert decision is not None
        assert decision[0] == "deny"

    def test_hardline_allowed_with_matching_preset_override(self, monkeypatch):
        monkeypatch.setenv("GUARD_BRANCH_ALLOW_FORCE", "main")
        assert gate.decide("Bash", {"command": "git push --force origin main"}) is None

    def test_override_for_a_different_branch_does_not_leak_through(self, monkeypatch):
        monkeypatch.setenv("GUARD_BRANCH_ALLOW_FORCE", "some-other-branch")
        decision = gate.decide("Bash", {"command": "git push --force origin main"})
        assert decision is not None
        assert decision[0] == "deny"

    def test_ask_tier_has_no_override_concept_at_all(self, monkeypatch):
        """The override only ever applies to a resolved hardline branch --
        an ask-tier result (branch=None) is never eligible for it, by
        construction of _overridden's falsy-branch check."""
        monkeypatch.setenv("GUARD_BRANCH_ALLOW_FORCE", "main")
        decision = gate.decide("Bash", {"command": "git push --force origin $BRANCH"})
        assert decision is not None
        assert decision[0] == "ask"


# ── decide(): the Bash-only gate and the wire-facing verdict shape ──────

class TestDecide:
    def test_non_bash_tool_is_never_inspected(self):
        assert gate.decide("Write", {"command": "git push --force origin main"}) is None
        assert gate.decide("Edit", {"file_path": "x.py"}) is None

    def test_missing_command_key_does_not_crash(self):
        assert gate.decide("Bash", {}) is None

    def test_safe_command_returns_no_opinion(self):
        assert gate.decide("Bash", {"command": "ls -la"}) is None
        assert gate.decide("Bash", {"command": "pytest tests/ -q"}) is None


# ── end-to-end: real stdin/stdout JSON, the actual Claude Code contract ─

class TestMainStdinStdoutContract:
    def _run(self, stdin_payload: dict) -> tuple[int, dict | None]:
        proc = subprocess.run(
            [sys.executable, str(REPO_ROOT / "scripts" / "gate_pretooluse.py")],
            input=json.dumps(stdin_payload), capture_output=True, text=True,
            encoding="utf-8", errors="replace",
        )
        out = proc.stdout.strip()
        return proc.returncode, (json.loads(out) if out else None)

    def test_safe_command_prints_nothing_and_exits_zero(self):
        code, out = self._run({"tool_name": "Bash", "tool_input": {"command": "ls -la"}})
        assert code == 0
        assert out is None

    def test_hardline_command_denies_with_the_real_hook_output_shape(self, monkeypatch):
        code, out = self._run({"tool_name": "Bash", "tool_input": {"command": "git push --force origin main"}})
        assert code == 0
        assert out["hookSpecificOutput"]["hookEventName"] == "PreToolUse"
        assert out["hookSpecificOutput"]["permissionDecision"] == "deny"
        assert "main" in out["hookSpecificOutput"]["permissionDecisionReason"]

    def test_malformed_stdin_fails_open_not_closed(self):
        proc = subprocess.run(
            [sys.executable, str(REPO_ROOT / "scripts" / "gate_pretooluse.py")],
            input="not valid json{{{", capture_output=True, text=True,
            encoding="utf-8", errors="replace",
        )
        assert proc.returncode == 0
        assert proc.stdout.strip() == ""

    def test_empty_stdin_fails_open(self):
        proc = subprocess.run(
            [sys.executable, str(REPO_ROOT / "scripts" / "gate_pretooluse.py")],
            input="", capture_output=True, text=True, encoding="utf-8", errors="replace",
        )
        assert proc.returncode == 0
        assert proc.stdout.strip() == ""
