"""Lawkeeper's Agent SDK integration -- Stage 1 of the downloadable
prototype plan (docs/LAWKEEPER_PROTOTYPE_PLAN.md).

Wraps Anthropic's real, official Agent SDK (`pip install
claude-agent-sdk`) with lawkeeper's own governance, starting with the
Law 22 Stop hook. Real, confirmed 2026-08-21: the SDK provides its own
native async-callback hook system (see guardrail.core.hedge_check for
the shared detection logic), not the subprocess/stdin-JSON contract
Claude Code CLI uses -- this module is real, new integration code, not
a port of scripts/claude_stop_hook.py.

Honest, stated uncertainty, not glossed over: the exact field name
carrying the just-finished response text on a real Stop event, in the
Agent SDK specifically, was not confirmed against SDK documentation
before writing this (the docs read covered the general hook contract
-- shared fields session_id/cwd/hook_event_name -- but not the Stop
event's own specific input shape in detail). This module defensively
checks a few plausible field names and is designed to be easy to
correct once a real, live Stop event's actual input_data can be
inspected -- which requires a real ANTHROPIC_API_KEY this environment
does not have (see BLOCKERS.md). Do not treat the current field-name
guess as verified; `_extract_response_text` exists specifically so
fixing this later is a one-function change, not a rewrite.

Usage (once a real API key is available):
    import asyncio
    from guardrail.agent import build_governed_options
    from claude_agent_sdk import ClaudeSDKClient

    async def main():
        options = build_governed_options()
        async with ClaudeSDKClient(options=options) as client:
            await client.query("your task here")
            async for message in client.receive_response():
                print(message)

    asyncio.run(main())
"""
from __future__ import annotations

from typing import Any

from guardrail.core.hedge_check import block_reason, check

# Plausible field names for the just-finished response text on a real
# Stop event -- ordered by how likely each is, given Claude Code CLI's
# own contract (last_assistant_message) as the closest known reference.
# Real verification pending a live session; see the module docstring.
_RESPONSE_TEXT_FIELD_CANDIDATES = (
    "last_assistant_message",
    "message",
    "response",
    "text",
)


def _extract_response_text(input_data: dict[str, Any]) -> str:
    """Best-effort extraction of the response text to check -- returns
    "" (never raises) if no known field is present, which fails the
    hedge check open (no match on empty string) rather than crashing
    the whole agent session on an unexpected input shape. Real, honest
    limitation: which field is actually correct is unverified (see
    module docstring) -- this function is the one place to fix once
    it's known."""
    for field in _RESPONSE_TEXT_FIELD_CANDIDATES:
        value = input_data.get(field)
        if isinstance(value, str) and value:
            return value
    return ""


async def law22_stop_hook(input_data: dict[str, Any], tool_use_id, context) -> dict:
    """Real Agent SDK Stop-hook callback, per the SDK's documented
    signature (async def hook(input_data, tool_use_id, context) -> dict).
    Reuses the exact same detection logic already tested and proven in
    scripts/claude_stop_hook.py's Claude Code CLI version, via the
    shared guardrail.core.hedge_check module -- not a reimplementation.
    """
    message = _extract_response_text(input_data)
    matched = check(message)

    if matched:
        return {
            "hookSpecificOutput": {
                "hookEventName": "Stop",
                "permissionDecision": "deny",
                "permissionDecisionReason": block_reason(matched),
            },
            "systemMessage": "Lawkeeper Stop hook: Law 22 hedge-phrase pattern detected, forcing continuation.",
        }

    return {}


def build_governed_options(**overrides: Any):
    """Build a real ClaudeAgentOptions instance with lawkeeper's Law 22
    Stop hook wired in. Deferred import of claude_agent_sdk so this
    module can be imported and tested (the hook logic above) without
    the SDK installed -- real for the test suite, which mocks the SDK
    boundary rather than requiring it as a hard dependency of every
    lawkeeper install.
    """
    from claude_agent_sdk import ClaudeAgentOptions, HookMatcher

    hooks = {"Stop": [HookMatcher(hooks=[law22_stop_hook])]}
    # Real, explicit merge: a caller-supplied "hooks" override replaces
    # ours entirely rather than silently merging, since silently
    # combining two hook dicts could hide which one actually wins for a
    # given event -- an explicit override is a real, visible choice,
    # not an accidental one.
    if "hooks" in overrides:
        hooks = overrides.pop("hooks")

    return ClaudeAgentOptions(hooks=hooks, **overrides)
