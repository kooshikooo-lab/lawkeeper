"""UserPreferenceProvider: tracks how a specific user prefers explanations,
and adapts by recording real corrections, not by guessing.

Second concrete consumer of the MemoryProvider interface (the first,
FailurePatternMemoryProvider, is read-only by design). This one actually
uses sync_turn() -- see docs/ADAPTIVE_INTERFACE_PLAN.md for the research
this is based on and why sync_turn matters here specifically.

Scope, stated plainly rather than overclaimed: this tracks explanation-
style corrections (too much jargon / too dumbed-down) and an ADHD-mode
toggle via explicit keyword triggers in what the user actually said --
not a fine-tuned per-user model (the research this is based on,
arXiv:2505.16227, shows lightweight methods already beat heavier ones;
keyword-triggered explicit correction tracking is the honest, minimal
version of that, not a shortcut pretending to be the full technique).
Vocabulary/jargon-familiarity tracking (which specific terms this user
already knows) is deliberately NOT built here -- flagged as a real
follow-up in ADAPTIVE_INTERFACE_PLAN.md, not silently attempted with an
unreliable heuristic.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from .provider import MemoryEntry, MemoryProvider

DEFAULT_STORE_PATH = Path.home() / ".lawkeeper" / "user_preferences.json"

# Keyword triggers for explicit corrections -- deliberately simple and
# inspectable (a person can read this list and know exactly what will and
# won't be detected), not a hidden model. Matched case-insensitively,
# word-boundary-safe (Law 20's own logged lesson: a past bug in this
# codebase's sibling repo came from a substring match without word
# boundaries -- "temp" matching inside "template" -- avoided here on
# purpose, not by luck).
_TOO_MUCH_JARGON_TRIGGERS = [
    r"\btoo much jargon\b", r"\blot of jargon\b", r"\bwhat does that mean\b",
    r"\bin plain (english|language)\b", r"\bexplain (like|as if)\b.*\bfive\b",
]
_TOO_DUMBED_DOWN_TRIGGERS = [
    r"\bdon't dumb (it|this) down\b", r"\bnot dumbed down\b",
    r"\bi('m| am) not (a )?(child|beginner)\b", r"\bi know what\b.*\bis\b",
]
_ADHD_MODE_ON_TRIGGERS = [
    r"\badhd\b.*\bmode\b", r"\bget to the point\b", r"\btoo long\b.*\b(explain|answer|response)\b",
]


def _compile(patterns: list[str]) -> list[re.Pattern]:
    return [re.compile(p, re.IGNORECASE) for p in patterns]


_JARGON_RE = _compile(_TOO_MUCH_JARGON_TRIGGERS)
_DUMBED_DOWN_RE = _compile(_TOO_DUMBED_DOWN_TRIGGERS)
_ADHD_RE = _compile(_ADHD_MODE_ON_TRIGGERS)


def _default_profile() -> dict:
    return {
        "jargon_corrections": 0,
        "dumbed_down_corrections": 0,
        "style": "balanced",  # "simplify_more" | "balanced" | "less_simplify"
        "adhd_mode": False,
    }


class UserPreferenceProvider(MemoryProvider):
    """Persists to a small JSON file (same durable-file pattern as
    ratings.json elsewhere in this ecosystem), not a database -- the
    profile is small and human-readable/editable on purpose, per
    ADAPTIVE_INTERFACE_PLAN.md's point about an auditable, correctable
    model rather than an opaque one."""

    def __init__(self, store_path: Path | None = None) -> None:
        self._store_path = store_path or DEFAULT_STORE_PATH
        self._profile: dict = _default_profile()
        self._initialized = False

    def initialize(self) -> None:
        if self._store_path.exists():
            try:
                loaded = json.loads(self._store_path.read_text(encoding="utf-8"))
                self._profile = {**_default_profile(), **loaded}
            except (json.JSONDecodeError, OSError):
                self._profile = _default_profile()
        else:
            self._profile = _default_profile()
        self._initialized = True

    def _save(self) -> None:
        self._store_path.parent.mkdir(parents=True, exist_ok=True)
        self._store_path.write_text(
            json.dumps(self._profile, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    def prefetch(self, query: str, limit: int = 5) -> list[MemoryEntry]:
        """The current preference profile, not query-filtered -- unlike
        the failure-pattern corpus, a preference profile is small and
        uniformly relevant to every turn, so there is nothing meaningful
        to filter by relevance here."""
        if not self._initialized:
            self.initialize()
        entries = []
        if self._profile["style"] != "balanced":
            entries.append(MemoryEntry(
                id="style", source="user_preferences",
                text=f"Explanation style preference: {self._profile['style']} "
                     f"(from {self._profile['jargon_corrections']} jargon "
                     f"corrections, {self._profile['dumbed_down_corrections']} "
                     f"dumbed-down corrections).",
                relevance=1.0,
            ))
        if self._profile["adhd_mode"]:
            entries.append(MemoryEntry(
                id="adhd_mode", source="user_preferences",
                text="ADHD mode is ON: lead with the next action, number steps, "
                     "cap lists at 5, no preamble/recap/closers, restate state "
                     "each turn, specific time estimates, matter-of-fact errors.",
                relevance=1.0,
            ))
        return entries[:limit]

    def sync_turn(self, query: str, response: str) -> None:
        """Records explicit corrections found in the user's own words.
        Called after a turn -- this is the hook FailurePatternMemoryProvider
        correctly leaves as a no-op (it has nothing to write); this
        provider is the one that actually needs it, closing the loop
        Law 21 exists to enforce instead of leaving it unconsumed."""
        if not self._initialized:
            self.initialize()
        changed = False
        if any(p.search(query) for p in _JARGON_RE):
            self._profile["jargon_corrections"] += 1
            changed = True
        if any(p.search(query) for p in _DUMBED_DOWN_RE):
            self._profile["dumbed_down_corrections"] += 1
            changed = True
        if changed:
            jargon = self._profile["jargon_corrections"]
            dumbed = self._profile["dumbed_down_corrections"]
            if jargon > dumbed:
                self._profile["style"] = "simplify_more"
            elif dumbed > jargon:
                self._profile["style"] = "less_simplify"
            else:
                self._profile["style"] = "balanced"
        if any(p.search(query) for p in _ADHD_RE):
            self._profile["adhd_mode"] = True
            changed = True
        if changed:
            self._save()

    def shutdown(self) -> None:
        if self._initialized:
            self._save()
