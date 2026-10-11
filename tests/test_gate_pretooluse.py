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
from pathlib import Path

import pytest

from conftest import REPO_ROOT

# Imported by name (not conftest.load_script's path loader) so mutmut can
# attribute tests to mutants of scripts/gate_pretooluse.py; the path comes
# from this file's own location so a mutmut copy imports its own mutated copy.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts import gate_pretooluse as gate  # noqa: E402


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

    def test_force_push_remote_only_no_branch_resolves_current_branch(self, monkeypatch):
        """The real regression a second Copilot review round caught:
        `git push --force origin` has exactly one bare positional (the
        remote), no refspec-shaped one at all. An earlier version of
        this scanner treated "origin" itself as the branch target
        (checking is_canonical("origin"), always False) instead of
        falling through to resolve the current branch -- a real
        false-negative that would have silently allowed a force-push
        to the current branch through undetected."""
        monkeypatch.setattr(gate.guard_branch, "run_git", lambda args: ("main", 0))
        risk = gate.inspect_command("git push --force origin")
        assert risk is not None
        assert risk.level == "hardline"
        assert risk.branch == "main"

    def test_force_push_remote_only_on_feature_branch_not_flagged(self, monkeypatch):
        monkeypatch.setattr(gate.guard_branch, "run_git",
                             lambda args: ("opencode/mesh-repair/laptop", 0))
        assert gate.inspect_command("git push --force origin") is None


# ── --all/--mirror: implicit multi-ref pushes (Copilot review, PR #19 round 2) ──

class TestMultiRefPushIsAsk:
    """--all/--mirror update every ref under refs/heads (or the whole
    repo, for --mirror) without naming any of them in the command text --
    a canonical branch could be among them with nothing for a static
    scanner to match against. Neither a confident hardline nor a safe
    allow; routed to ask."""

    def test_force_push_all_is_ask(self):
        risk = gate.inspect_command("git push --force --all origin")
        assert risk is not None
        assert risk.level == "ask"

    def test_force_push_mirror_is_ask(self):
        risk = gate.inspect_command("git push --force --mirror origin")
        assert risk is not None
        assert risk.level == "ask"

    def test_ordinary_push_all_without_force_is_not_flagged(self):
        assert gate.inspect_command("git push --all origin") is None

    def test_dry_run_push_all_force_is_never_flagged(self):
        assert gate.inspect_command("git push --dry-run --force --all origin") is None


class TestHardlineBranchDelete:
    def test_delete_main_is_hardline(self):
        risk = gate.inspect_command("git branch -D main")
        assert risk.level == "hardline"
        assert risk.branch == "main"

    def test_delete_feature_branch_is_not_flagged(self):
        assert gate.inspect_command("git branch -D opencode/mesh-repair/laptop") is None

    def test_soft_delete_flag_on_canonical_branch_is_still_hardline(self):
        # -d (lowercase) on git branch is the safe, merged-only delete;
        # still routed through the same delete-flag set intentionally
        # (git refuses an unmerged -d anyway), and still hardline-denied
        # against a canonical branch -- renamed from a name that claimed
        # "not flagged" while asserting hardline (Copilot review, PR #19).
        risk = gate.inspect_command("git branch -d main")
        assert risk.level == "hardline"


# ── refspec forms Copilot's review found this scanner missing (PR #19) ──

class TestRefspecFormsCopilotFound:
    """A prior version stripped only the leading +/: character and
    compared the ENTIRE remainder against is_canonical(), which only
    recognizes bare branch names -- so "+main:main" became the literal
    string "main:main" (never matches "main"), and ":refs/heads/main"
    became "refs/heads/main" (also never matches). Both silently let a
    canonical-branch force-update/delete through. Found by GitHub
    Copilot's review of this PR, not caught by the original test suite."""

    def test_src_colon_dst_refspec_with_leading_force_marker(self):
        risk = gate.inspect_command("git push origin +main:main")
        assert risk is not None
        assert risk.level == "hardline"
        assert risk.branch == "main"

    def test_fully_qualified_delete_refspec(self):
        risk = gate.inspect_command("git push origin :refs/heads/main")
        assert risk is not None
        assert risk.level == "hardline"
        assert risk.branch == "main"

    def test_src_colon_dst_refspec_with_explicit_force_flag(self):
        risk = gate.inspect_command("git push --force origin HEAD:main")
        assert risk is not None
        assert risk.level == "hardline"
        assert risk.branch == "main"

    def test_src_colon_dst_to_a_non_canonical_dst_is_not_flagged(self):
        # The destination, not the source, is what lands on the remote --
        # pushing local main to a remote feature branch is not the same
        # danger as the reverse.
        assert gate.inspect_command("git push --force origin main:opencode/mesh-repair/laptop") is None

    def test_fully_qualified_branch_delete(self):
        risk = gate.inspect_command("git branch -D refs/heads/main")
        assert risk is not None
        assert risk.level == "hardline"
        assert risk.branch == "main"

    def test_variable_embedded_mid_token_after_refspec_normalization(self):
        # "refs/heads/$BRANCH" only exposes the variable once the
        # refs/heads/ prefix is stripped -- the raw token doesn't start
        # with "$" at all.
        risk = gate.inspect_command("git push --force origin refs/heads/$BRANCH")
        assert risk is not None
        assert risk.level == "ask"

    def test_variable_embedded_after_a_literal_prefix_is_still_caught(self):
        # A variable that never reaches the start of the token even
        # after normalization (e.g. interpolated into a longer name).
        risk = gate.inspect_command("git push --force origin +HEAD:pre-$SUFFIX")
        assert risk is not None
        assert risk.level == "ask"

    def test_hardline_outranks_ask_across_multiple_targets_in_one_command(self):
        # A command with two refspecs -- one unresolvable, one a
        # confirmed canonical match -- must still deny, not ask, even
        # though the unresolvable one could be scanned first.
        risk = gate.inspect_command("git push --force origin $UNKNOWN main")
        assert risk is not None
        assert risk.level == "hardline"
        assert risk.branch == "main"


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


# ── directory tracking: `cd <dir> &&` / `git -C <dir>` (handoff 2026-10-07) ──

import subprocess  # noqa: E402


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


class TestTargetCheckoutResolution:
    def test_cd_into_main_checkout_force_push_is_hardline(self, two_checkouts):
        _, main = two_checkouts
        risk = gate.inspect_command(f"cd {main} && git push --force")
        assert risk is not None and risk.level == "hardline" and risk.branch == "main"

    def test_git_dash_C_main_checkout_force_push_is_hardline(self, two_checkouts):
        _, main = two_checkouts
        risk = gate.inspect_command(f"git -C {main} push --force")
        assert risk is not None and risk.level == "hardline"

    def test_git_dash_C_with_explicit_main_target_is_hardline(self, two_checkouts):
        _, main = two_checkouts
        risk = gate.inspect_command(f"git -C {main} push --force origin main")
        assert risk is not None and risk.level == "hardline"

    def test_cd_into_feature_checkout_from_main_is_allowed(self, two_checkouts, monkeypatch):
        feat, main = two_checkouts
        monkeypatch.chdir(main)  # session folder is on main: plain push would be denied
        assert gate.inspect_command("git push --force").level == "hardline"
        assert gate.inspect_command(f"cd {feat} && git push --force") is None
        assert gate.inspect_command(f"git -C {feat} push --force") is None

    def test_unresolvable_cd_makes_unnamed_force_push_ask(self, two_checkouts):
        risk = gate.inspect_command('cd "$TARGET" && git push --force')
        assert risk is not None and risk.level == "ask"

    def test_cd_dash_and_pushd_make_unnamed_force_push_ask(self, two_checkouts):
        for cmd in ("cd - && git push --force", "pushd /tmp && git push --force"):
            risk = gate.inspect_command(cmd)
            assert risk is not None and risk.level == "ask", cmd

    def test_plain_push_without_force_unaffected(self, two_checkouts):
        _, main = two_checkouts
        assert gate.inspect_command(f"cd {main} && git push") is None
        assert gate.inspect_command(f"git -C {main} push origin main") is None


# ── mutation-driven additions (mutmut run, 2026-10-11) ─────────────────
# Each group pins behavior a surviving mutant showed was unpinned: the
# verdict level/branch/reason exactly as the human sees them, the argument
# parsers' edge cases, and the Windows path translation (exercised on every
# platform by faking os.name).

import os  # noqa: E402
import types  # noqa: E402

_ALL_REASON = ("a force/delete push with --all/--mirror, which can update multiple refs "
               "(including a canonical branch) without naming any of them explicitly")
_VAR_SUFFIX = "(shell variable/substitution)"


class TestVerdictsExact:
    def test_risk_stores_its_three_fields(self):
        r = gate.Risk("ask", "b", "why")
        assert (r.level, r.branch, r.reason) == ("ask", "b", "why")

    def test_multi_ref_force_is_ask_with_reason(self):
        for cmd in ("git push --force --all", "git push --delete origin --mirror"):
            r = gate.inspect_command(cmd)
            assert (r.level, r.branch, r.reason) == ("ask", None, _ALL_REASON), cmd

    def test_unresolvable_component_without_branch_is_ask(self):
        r = gate.inspect_command("git push --force $REMOTE")
        assert (r.level, r.branch) == ("ask", None)
        assert r.reason == ("a force/delete push with no explicit branch and an unresolvable "
                            "(shell variable/substitution) component")

    def test_unresolvable_current_branch_is_ask(self, monkeypatch):
        monkeypatch.setattr(gate, "_current_branch", lambda cwd=None: None)
        r = gate.inspect_command("git push --force")
        assert (r.level, r.branch) == ("ask", None)
        assert r.reason == ("a force/delete push with no explicit branch, and the current branch "
                            "could not be resolved (unresolvable directory change, or not a git checkout)")

    def test_canonical_current_branch_reason(self, monkeypatch):
        monkeypatch.setattr(gate, "_current_branch", lambda cwd=None: "main")
        r = gate.inspect_command("git push --force")
        assert (r.level, r.branch) == ("hardline", "main")
        assert r.reason == "a force/delete push with no explicit refspec, on canonical branch 'main'"

    def test_explicit_canonical_target_reason(self):
        r = gate.inspect_command("git push --force origin main")
        assert r.reason == "a force/delete push targeting canonical branch 'main'"

    def test_unresolvable_target_reason(self):
        r = gate.inspect_command("git push --force origin $B")
        assert (r.level, r.branch) == ("ask", None)
        assert r.reason == f"a force/delete push whose target '$B' could not be resolved {_VAR_SUFFIX}"

    def test_branch_delete_reasons(self):
        r = gate.inspect_command("git branch -D main")
        assert (r.level, r.branch) == ("hardline", "main")
        assert r.reason == "a branch delete targeting canonical branch 'main'"
        r = gate.inspect_command("git branch -D $B")
        assert (r.level, r.branch) == ("ask", None)
        assert r.reason == f"a branch delete whose target '$B' could not be resolved {_VAR_SUFFIX}"

    def test_branch_without_delete_flag_is_not_inspected(self):
        assert gate.inspect_command("git branch main") is None
        assert gate.inspect_command("git branch -a") is None

    def test_push_delete_flag_alone_is_risky(self):
        r = gate.inspect_command("git push --delete origin main")
        assert (r.level, r.branch) == ("hardline", "main")

    def test_non_push_git_command_is_no_opinion(self):
        assert gate.inspect_command("git status") is None
        assert gate.inspect_command("git status && git log") is None

    def test_hardline_outranks_an_earlier_ask(self):
        r = gate.inspect_command("git push --force $X && git push --force origin main")
        assert r.level == "hardline"

    def test_first_ask_is_kept_over_a_later_ask(self):
        r = gate.inspect_command("git push --force $X && git push --force origin $Y")
        assert r.level == "ask" and "unresolvable" in r.reason

    def test_a_valueless_git_option_does_not_hide_a_later_push(self):
        assert gate.inspect_command("git --version && git push -f origin main").level == "hardline"


class TestTokenisation:
    def test_quoted_arguments_are_unquoted(self):
        assert gate.inspect_command("git push --force 'origin' \"main\"").level == "hardline"

    def test_absolute_git_path_is_recognised(self):
        assert gate.inspect_command("/usr/bin/git push -f origin main").level == "hardline"
        # Known gap (card blind_spot): shlex posix mode eats backslashes, so an
        # unquoted C:\...\git path is not recognised by inspect_command.

    def test_basename(self):
        assert gate._basename("/a/b/git") == "git"
        assert gate._basename("a\\b\\git") == "git"
        assert gate._basename("git") == "git"

    def test_backtick_substitution_is_unresolvable(self):
        r = gate.inspect_command("git push --force origin `echo main`")
        assert r.level == "ask"

    def test_refspec_parsing(self):
        assert gate._parse_push_refspec("main") == ("main", False)
        assert gate._parse_push_refspec("a:b") == ("b", False)
        assert gate._parse_push_refspec("a:b:main") == ("b:main", False)
        assert gate._parse_push_refspec(":main") == ("main", True)
        assert gate._parse_push_refspec("+main") == ("main", True)


class TestCurrentBranch:
    def test_branch_name_returned_only_on_success(self, monkeypatch):
        for out, code, want in (("feat", 0, "feat"), ("garbage", 1, None),
                                ("", 0, None), ("HEAD", 0, None), ("head", 0, "head")):
            monkeypatch.setattr(gate.guard_branch, "run_git", lambda a, o=out, c=code: (o, c))
            assert gate._current_branch() == want, (out, code)

    def test_dash_C_prefix_is_used_when_a_directory_is_given(self, monkeypatch):
        seen = []
        monkeypatch.setattr(gate.guard_branch, "run_git", lambda a: seen.append(a) or ("x", 0))
        gate._current_branch("/some/dir")
        gate._current_branch()
        assert seen[0][:2] == ["-C", "/some/dir"] and seen[1][0] == "rev-parse"


class TestJoinDir:
    def test_unresolvable_targets(self):
        U = gate._UNKNOWN_DIR
        assert gate._join_dir(U, "x") is U
        assert gate._join_dir(None, "") is U
        assert gate._join_dir(None, "-") is U
        assert gate._join_dir(None, "~") is U
        assert gate._join_dir(None, "~/x") is U
        assert gate._join_dir(None, "$X") is U
        assert gate._join_dir("/b", "`x`") is U

    def test_resolvable_targets(self):
        assert gate._join_dir(None, "rel") == "rel"
        assert gate._join_dir("base", "rel") == os.path.join("base", "rel")
        assert gate._join_dir("base", "C:/x") == "C:/x"
        assert gate._join_dir("base", "c:/x") == "c:/x"
        assert gate._join_dir("base", os.path.abspath("x")) == os.path.abspath("x")


class TestMsysToNative:
    @staticmethod
    def _fake_os(monkeypatch, name):
        monkeypatch.setattr(gate, "os", types.SimpleNamespace(name=name, path=os.path, environ=os.environ))

    def test_translates_drive_paths_on_windows(self, monkeypatch):
        self._fake_os(monkeypatch, "nt")
        assert gate._msys_to_native("/e/lawkeeper") == "E:/lawkeeper"
        assert gate._msys_to_native("/E/x") == "E:/x"
        assert gate._msys_to_native("/e") == "E:/"
        assert gate._msys_to_native("/e/") == "E:/"

    def test_leaves_other_shapes_alone(self, monkeypatch):
        self._fake_os(monkeypatch, "nt")
        for p in ("/ee/x", "rel/x", "C:/x", "/", ""):
            assert gate._msys_to_native(p) == p

    def test_noop_off_windows(self, monkeypatch):
        self._fake_os(monkeypatch, "posix")
        assert gate._msys_to_native("/e/lawkeeper") == "/e/lawkeeper"


class TestParseGitInvocation:
    def test_dash_C_reroots_and_chains(self, tmp_path):
        base = str(tmp_path)
        sub, args, cwd = gate._parse_git_invocation(["git", "-C", "sub", "push", "-f"], base)
        assert (sub, args, cwd) == ("push", ["-f"], os.path.join(base, "sub"))
        _, _, cwd = gate._parse_git_invocation(["git", "-C", base, "-C", "b", "push"], None)
        assert cwd == os.path.join(base, "b")

    def test_option_forms_and_cursor_advance(self):
        U = gate._UNKNOWN_DIR
        for toks in (["git", "--git-dir=/g", "push", "x"], ["git", "--git-dir", "/g", "push", "x"],
                     ["git", "--work-tree=/w", "push", "x"], ["git", "--work-tree", "/w", "push", "x"]):
            sub, args, cwd = gate._parse_git_invocation(toks, "/b")
            assert (sub, args) == ("push", ["x"]) and cwd is U, toks
        for toks in (["git", "-c", "a=b", "push", "x"], ["git", "--no-pager", "push", "x"],
                     ["git", "--namespace", "n", "push", "x"]):
            sub, args, cwd = gate._parse_git_invocation(toks, "/b")
            assert (sub, args, cwd) == ("push", ["x"], "/b"), toks

    def test_no_subcommand(self):
        assert gate._parse_git_invocation(["git", "--no-pager"], None) is None
        assert gate._parse_git_invocation(["git", "-C"], None) is None
        assert gate._parse_git_invocation(["git"], None) is None


class TestDirectoryTrackingEdges:
    def test_chdir_and_chained_relative_cd(self, two_checkouts):
        _, main = two_checkouts
        parent, leaf = main.rsplit("/", 1)
        assert gate.inspect_command(f"chdir {main} && git push --force").level == "hardline"
        assert gate.inspect_command(f"cd {parent} && cd {leaf} && git push --force").level == "hardline"

    def test_popd_cd_without_arg_and_cd_with_two_args_are_unknown(self, two_checkouts):
        for cmd in ("popd && git push --force", "cd && git push --force",
                    "cd a b && git push --force"):
            assert gate.inspect_command(cmd).level == "ask", cmd


class TestOverrideEnv:
    def test_exact_match_only(self, monkeypatch):
        monkeypatch.delenv("GUARD_BRANCH_ALLOW_FORCE", raising=False)
        monkeypatch.delenv("GUARD_BRANCH_ALLOW_DELETE", raising=False)
        assert gate._overridden(None) is False and gate._overridden("") is False
        assert gate._overridden("main") is False
        monkeypatch.setenv("GUARD_BRANCH_ALLOW_DELETE", "main")
        assert gate._overridden("main") is True and gate._overridden("other") is False
        monkeypatch.delenv("GUARD_BRANCH_ALLOW_DELETE")
        monkeypatch.setenv("GUARD_BRANCH_ALLOW_FORCE", "main")
        assert gate._overridden("main") is True
