#!/usr/bin/env python3
"""Claude Code Stop hook: blocks a turn from ending on a stated future
intention with nothing actually done about it.

Real failure, caught live twice in one session (2026-08-20): a response
ended on "going to do X next, unless you'd rather redirect me" -- the
literal last sentence, no tool call in that turn -- and the turn ended,
functionally identical to stopping despite the text claiming otherwise.
Law 22 (docs/AI_CONSTITUTION.md) was amended to forbid this in writing;
this script is the mechanical version of the same rule -- a deterministic
check outside the model, not another paragraph the model has to remember
to apply to itself.

Installed via install_hooks.py into .claude/settings.json's "Stop" hook
list. Reads the just-finished turn's JSON from stdin (Claude Code's real
Stop-hook contract: last_assistant_message is the current turn's final
text, preferred over transcript_path which can lag). Blocks by returning
hookSpecificOutput.permissionDecision: "deny" with a reason naming
exactly what matched, so a block is a real, specific correction, not a
mysterious re-trigger.

Real detection logic now lives in guardrail.core.hedge_check (extracted
2026-08-21) so it's shared with src/guardrail/agent.py's Agent SDK
integration rather than duplicated -- this file is now just the
Claude-Code-CLI-specific stdin/stdout wrapper around that shared logic.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from guardrail.core.hedge_check import check, block_reason  # noqa: E402


def main() -> int:
    raw = sys.stdin.read()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        # Never block on our own parse failure -- a broken hook must fail
        # open, not silently hold every future turn hostage.
        return 0

    message = data.get("last_assistant_message", "") or ""
    matched = check(message)

    if matched:
        result = {
            "hookSpecificOutput": {
                "hookEventName": "Stop",
                "permissionDecision": "deny",
                "permissionDecisionReason": block_reason(matched),
            },
            "systemMessage": "Stop hook: Law 22 hedge-phrase pattern detected, forcing continuation.",
        }
        print(json.dumps(result))
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
