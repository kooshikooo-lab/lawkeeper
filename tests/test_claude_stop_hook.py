"""Tests for claude_stop_hook.py -- the mechanical version of Law 22's
2026-08-20 amendment.

Real regression cases: the two actual hedge-phrase sentences caught live
in one session must be blocked, and legitimate final messages (which
share surface words like "next" or "going to" without being the
self-referential hedge) must NOT be blocked -- a false positive here is
itself a new failure mode (wasted tokens, an annoying forced
continuation), not a safe default.
"""
import json
import subprocess
import sys
from pathlib import Path

from conftest import REPO_ROOT, load_script

hook = load_script("claude_stop_hook.py")

SCRIPT_PATH = REPO_ROOT / "scripts" / "claude_stop_hook.py"


class TestCheckFunction:
    def test_real_instance_one_is_caught(self):
        msg = (
            "Everything's pushed to origin on both repos -- no dangling "
            "local work.\n\nGiven Law 22, I'm continuing rather than "
            "stopping here. Most consequential open thread is the real "
            "bug in Falcun's ground_concept() -- going to dig into that "
            "next unless you'd rather redirect me somewhere else."
        )
        assert hook.check(msg) is not None

    def test_real_instance_two_is_caught(self):
        msg = "Going to dig into that next unless you'd rather redirect me somewhere else."
        assert hook.check(msg) is not None

    def test_curly_apostrophe_variant_is_caught(self):
        msg = "I’m going to check that next unless you’d rather redirect me."
        assert hook.check(msg) is not None

    def test_legitimate_final_message_with_next_is_clean(self):
        msg = (
            "Here's what changed: fixed the retry logic and added tests. "
            "Next, you might want to run the full suite to confirm nothing "
            "else regressed."
        )
        assert hook.check(msg) is None

    def test_legitimate_message_ending_in_a_real_question_is_clean(self):
        msg = (
            "I found two ways to fix this -- a small patch or a larger "
            "refactor. Which would you prefer?"
        )
        assert hook.check(msg) is None

    def test_completed_work_report_is_clean(self):
        msg = (
            "Committed and pushed both changes. Ran the full test suite: "
            "187/187 passed. System audit: ALL CHECKS PASS."
        )
        assert hook.check(msg) is None

    def test_only_the_tail_is_checked(self):
        # "going to" appears early but nowhere near "unless you" within
        # the tail window -- must not false-positive on an unrelated
        # earlier mention.
        padding = "This is unrelated filler text. " * 40
        msg = f"I was going to mention something earlier. {padding}Done -- fully verified, tests pass."
        assert hook.check(msg) is None

    def test_empty_message_is_clean(self):
        assert hook.check("") is None


class TestMainStdinContract:
    def _run(self, payload: dict) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(SCRIPT_PATH)],
            input=json.dumps(payload), capture_output=True, text=True,
            encoding="utf-8", errors="replace",
        )

    def test_hedge_message_blocks_with_deny_and_reason(self):
        result = self._run({"last_assistant_message": "Going to dig into that next unless you'd rather redirect me."})
        assert result.returncode == 0  # blocks via JSON decision, not exit 2, in this implementation
        out = json.loads(result.stdout)
        assert out["hookSpecificOutput"]["permissionDecision"] == "deny"
        assert "Law 22" in out["hookSpecificOutput"]["permissionDecisionReason"]

    def test_clean_message_allows_stop_with_no_output(self):
        result = self._run({"last_assistant_message": "Done. All tests pass."})
        assert result.returncode == 0
        assert result.stdout.strip() == ""

    def test_malformed_json_fails_open(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT_PATH)],
            input="not valid json{{{", capture_output=True, text=True,
            encoding="utf-8", errors="replace",
        )
        assert result.returncode == 0
        assert result.stdout.strip() == ""

    def test_missing_field_fails_open(self):
        result = self._run({"session_id": "abc"})
        assert result.returncode == 0
        assert result.stdout.strip() == ""
