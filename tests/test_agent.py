"""Tests for guardrail.agent -- the Agent SDK Stop-hook integration.

Real network/live-session calls are blocked on a real ANTHROPIC_API_KEY
this environment doesn't have (see BLOCKERS.md) -- not attempted here.
What's tested: the Stop-hook callback's own logic (reused, tested
detection via guardrail.core.hedge_check, exercised through the async
callback contract itself) and build_governed_options' real wiring,
with claude_agent_sdk itself mocked so this test suite doesn't require
it as a hard dependency.
"""
import asyncio
import sys
from types import ModuleType
from unittest.mock import MagicMock

from guardrail.agent import _extract_response_text, law22_stop_hook


class TestExtractResponseText:
    def test_extracts_last_assistant_message_when_present(self):
        assert _extract_response_text({"last_assistant_message": "hello"}) == "hello"

    def test_falls_back_through_candidate_fields_in_order(self):
        assert _extract_response_text({"message": "hi"}) == "hi"
        assert _extract_response_text({"response": "hi"}) == "hi"
        assert _extract_response_text({"text": "hi"}) == "hi"

    def test_prefers_earlier_candidates(self):
        data = {"last_assistant_message": "real", "message": "wrong"}
        assert _extract_response_text(data) == "real"

    def test_returns_empty_string_not_none_when_nothing_matches(self):
        assert _extract_response_text({"unrelated_field": "x"}) == ""
        assert _extract_response_text({}) == ""

    def test_ignores_non_string_values(self):
        assert _extract_response_text({"last_assistant_message": 123}) == ""


class TestLaw22StopHook:
    def test_hedge_phrase_blocks_with_real_reason(self):
        input_data = {
            "last_assistant_message": "Going to dig into that next unless you'd rather redirect me.",
            "session_id": "s1", "cwd": "/tmp", "hook_event_name": "Stop",
        }
        result = asyncio.run(law22_stop_hook(input_data, "tool-1", None))
        assert result["hookSpecificOutput"]["permissionDecision"] == "deny"
        assert "Law 22" in result["hookSpecificOutput"]["permissionDecisionReason"]

    def test_clean_message_allows_with_empty_dict(self):
        input_data = {
            "last_assistant_message": "Done. All tests pass.",
            "session_id": "s1", "cwd": "/tmp", "hook_event_name": "Stop",
        }
        result = asyncio.run(law22_stop_hook(input_data, "tool-1", None))
        assert result == {}

    def test_unknown_input_shape_fails_open_not_crash(self):
        # Real, honest scenario this test exists for: the field-name
        # guess in _extract_response_text is unverified (see agent.py's
        # own docstring) -- if it's wrong, this must fail open (allow),
        # never crash the whole agent session.
        result = asyncio.run(law22_stop_hook({"session_id": "s1"}, "tool-1", None))
        assert result == {}


class TestBuildGovernedOptions:
    def test_wires_law22_stop_hook_by_default(self, monkeypatch):
        fake_module = ModuleType("claude_agent_sdk")
        fake_module.ClaudeAgentOptions = MagicMock(side_effect=lambda **kw: kw)
        fake_module.HookMatcher = MagicMock(side_effect=lambda **kw: kw)
        monkeypatch.setitem(sys.modules, "claude_agent_sdk", fake_module)

        from guardrail.agent import build_governed_options
        options = build_governed_options()

        assert "Stop" in options["hooks"]
        matcher = options["hooks"]["Stop"][0]
        assert matcher["hooks"] == [law22_stop_hook]

    def test_explicit_hooks_override_replaces_default(self, monkeypatch):
        fake_module = ModuleType("claude_agent_sdk")
        fake_module.ClaudeAgentOptions = MagicMock(side_effect=lambda **kw: kw)
        fake_module.HookMatcher = MagicMock(side_effect=lambda **kw: kw)
        monkeypatch.setitem(sys.modules, "claude_agent_sdk", fake_module)

        from guardrail.agent import build_governed_options
        custom_hooks = {"PreToolUse": ["something else"]}
        options = build_governed_options(hooks=custom_hooks)

        assert options["hooks"] == custom_hooks
