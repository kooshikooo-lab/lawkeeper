"""Tests for guardrail.core.hedge_check -- the real, shared Law 22
detection logic.

Extracted 2026-08-21 from scripts/claude_stop_hook.py so it's shared
between that CLI-hook wrapper and src/guardrail/agent.py's Agent SDK
integration, instead of duplicated. These tests mirror
tests/test_claude_stop_hook.py's TestCheckFunction cases exactly (same
real historical failures, same negative cases) since both consumers now
depend on this one real implementation -- a regression here would break
both.
"""
from guardrail.core.hedge_check import check, block_reason


class TestCheck:
    def test_real_instance_one_is_caught(self):
        msg = (
            "Everything's pushed to origin on both repos -- no dangling "
            "local work.\n\nGiven Law 22, I'm continuing rather than "
            "stopping here. Most consequential open thread is the real "
            "bug in Falcun's ground_concept() -- going to dig into that "
            "next unless you'd rather redirect me somewhere else."
        )
        assert check(msg) is not None

    def test_real_instance_two_is_caught(self):
        msg = "Going to dig into that next unless you'd rather redirect me somewhere else."
        assert check(msg) is not None

    def test_curly_apostrophe_variant_is_caught(self):
        msg = "I’m going to check that next unless you’d rather redirect me."
        assert check(msg) is not None

    def test_legitimate_final_message_with_next_is_clean(self):
        msg = (
            "Here's what changed: fixed the retry logic and added tests. "
            "Next, you might want to run the full suite to confirm nothing "
            "else regressed."
        )
        assert check(msg) is None

    def test_completed_work_report_is_clean(self):
        msg = "Committed and pushed both changes. Ran the full test suite: 187/187 passed."
        assert check(msg) is None

    def test_empty_message_is_clean(self):
        assert check("") is None

    def test_only_tail_is_checked(self):
        padding = "This is unrelated filler text. " * 40
        msg = f"I was going to mention something earlier. {padding}Done -- fully verified, tests pass."
        assert check(msg) is None


class TestBlockReason:
    def test_names_law_22_and_the_matched_pattern(self):
        matched = r"\bgoing to\b.{0,80}\bunless you\b"
        reason = block_reason(matched)
        assert "Law 22" in reason
        # block_reason uses !r (repr) formatting, so the pattern appears
        # escaped, not verbatim -- assert against its repr, not the raw string.
        assert repr(matched) in reason
