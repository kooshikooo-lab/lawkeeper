"""Real, mechanical Law 22 detection: a response that ends on a stated
future intention with nothing actually done about it.

Extracted 2026-08-21 from scripts/claude_stop_hook.py (originally built
for Claude Code CLI's Stop hook) so the same, real, tested logic is
importable from both that CLI-hook script and
src/guardrail/agent.py's Agent SDK integration -- one real
implementation, not two copies that could silently drift apart (Law 3).

Real failure this exists to catch, caught live twice in one session
(2026-08-20): a response ended on "going to do X next, unless you'd
rather redirect me" -- the literal last sentence, no tool call in that
turn -- and the turn ended, functionally identical to stopping despite
the text claiming otherwise. Law 22 (docs/AI_CONSTITUTION.md) forbids
this in writing; this module is the mechanical version of the same
rule.

Deliberately narrow: false positives here are a real, new failure mode
(wasted tokens, an annoying forced continuation on a genuinely finished
answer), so the pattern list starts scoped to the two real failures
already caught, not a broad guess at every possible hedge phrase. Grow
it only from a real caught instance, same discipline the constitution
itself is held to.
"""
from __future__ import annotations

import re

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


def block_reason(matched: str) -> str:
    """The real, human-readable reason a match should block -- shared so
    both the CLI hook's JSON output and the Agent SDK's hookSpecificOutput
    say the same real thing, not two independently-worded copies."""
    return (
        "Law 22 (lawkeeper AI_CONSTITUTION.md): this response "
        "ended on a stated future intention with no tool call "
        f"in this turn (matched: {matched!r}). If the next step "
        "is technical, take it now, in this turn. If it's "
        "genuinely directional, ask one real, specific question "
        "-- don't hedge with a soft 'unless you'd rather...' "
        "that isn't actually a question."
    )
