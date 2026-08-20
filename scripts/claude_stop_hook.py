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

Deliberately narrow: false positives here are a real, new failure mode
(wasted tokens, an annoying forced continuation on a genuinely finished
answer), so the pattern list starts scoped to the two real failures
already caught, not a broad guess at every possible hedge phrase. Grow
it only from a real caught instance, same discipline the constitution
itself is held to.
"""
from __future__ import annotations

import json
import re
import sys

# Only the ending matters -- this is about how a turn closes, not a
# scan of the whole response (which would false-positive on completely
# unrelated uses of "next" or "going to" earlier in a long answer).
TAIL_CHARS = 600

# ['’]? rather than '?: a straight or typographic apostrophe both need
# to match -- found by checking, not assumed, that responses in this
# session mix both.
_APOS = r"['’]?"

HEDGE_PATTERNS: list[str] = [
    r"\bgoing to\b.{0,80}\bunless you\b",
    rf"\bi{_APOS}ll\b.{{0,80}}\bunless you\b",
    rf"\bi{_APOS}m going to\b.{{0,80}}\bnext\b",
    r"\bnext up is\b",
    rf"\bi{_APOS}m continuing\b(?!\s+to\s+(?:read|show|display))",
]


def check(message: str) -> str | None:
    """Return the matched pattern (for a clear block reason), or None if clean."""
    if not message:
        return None
    tail = message[-TAIL_CHARS:]
    low = tail.lower()
    for pattern in HEDGE_PATTERNS:
        if re.search(pattern, low):
            return pattern
    return None


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
                "permissionDecisionReason": (
                    "Law 22 (lawkeeper AI_CONSTITUTION.md): this response "
                    "ended on a stated future intention with no tool call "
                    f"in this turn (matched: {matched!r}). If the next step "
                    "is technical, take it now, in this turn. If it's "
                    "genuinely directional, ask one real, specific question "
                    "-- don't hedge with a soft 'unless you'd rather...' "
                    "that isn't actually a question."
                ),
            },
            "systemMessage": "Stop hook: Law 22 hedge-phrase pattern detected, forcing continuation.",
        }
        print(json.dumps(result))
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
