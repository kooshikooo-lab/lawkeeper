"""Structured blocker reporting -- never say "not possible," always say
what's needed.

Explicit user requirement (2026-08-20): when a task can't proceed right
now (a missing API key, an uninstalled program, unavailable hardware),
that must never be reported as a dead end -- it must be recorded as a
concrete, actionable note: exactly what's missing and what would unblock
it, so the user can act on it whenever they choose (this session or
later). Two real precedents already existed before this module: the
laptop's SDXL/GPU report ("no NVIDIA GPU, needs 8GB+ VRAM, here are the
options") and consensus_review.py's claude-auth error ("not authenticated
in this subprocess, run from a separately-logged-in terminal or set
ANTHROPIC_API_KEY"). This generalizes that pattern into one place instead
of each script inventing its own wording.

Usage:
    from blockers import report_blocker

    if not os.environ.get("SOME_API_KEY"):
        report_blocker(
            component="image generation",
            missing="SOME_API_KEY environment variable",
            why="the image-gen API call requires authentication",
            how_to_fix="get a key from <provider>, then `export SOME_API_KEY=...`",
        )
        return  # or raise, or skip -- caller decides, this only records+prints

Every call appends a structured entry to BLOCKERS.md in the repo root
(created on first use) -- a durable, reviewable list, not something that
only exists in scrollback and gets lost.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
BLOCKERS_MD = REPO_ROOT / "BLOCKERS.md"
BLOCKERS_JSON = REPO_ROOT / "scripts" / ".blockers.json"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def report_blocker(component: str, missing: str, why: str, how_to_fix: str) -> None:
    """Record and print a real, actionable blocker. Never call this for
    something that's just difficult or that you haven't actually tried --
    only for a genuine, checked prerequisite gap (a real missing key, a
    real missing install, real hardware that was actually checked)."""
    entry = {
        "timestamp": _now(),
        "component": component,
        "missing": missing,
        "why": why,
        "how_to_fix": how_to_fix,
    }
    print(f"BLOCKED (not impossible, needs setup): {component}")
    print(f"  Missing: {missing}")
    print(f"  Why: {why}")
    print(f"  To fix: {how_to_fix}")

    entries = []
    if BLOCKERS_JSON.exists():
        try:
            entries = json.loads(BLOCKERS_JSON.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            entries = []
    entries.append(entry)
    BLOCKERS_JSON.parent.mkdir(parents=True, exist_ok=True)
    BLOCKERS_JSON.write_text(json.dumps(entries, indent=2), encoding="utf-8")

    _rewrite_markdown(entries)


def _rewrite_markdown(entries: list[dict]) -> None:
    """Human-readable BLOCKERS.md, newest first, regenerated from the JSON
    ledger each time so it never drifts out of sync with it."""
    lines = [
        "# Blockers — things that need setup, not things that failed",
        "",
        "Every entry here is a real, checked prerequisite gap (a missing "
        "key, a missing install, unavailable hardware) with exactly what "
        "would unblock it. Nothing here means \"impossible\" — it means "
        "\"needs this specific thing.\"",
        "",
    ]
    for e in reversed(entries):
        lines.append(f"## {e['component']} ({e['timestamp']})")
        lines.append(f"- **Missing:** {e['missing']}")
        lines.append(f"- **Why:** {e['why']}")
        lines.append(f"- **To fix:** {e['how_to_fix']}")
        lines.append("")
    BLOCKERS_MD.write_text("\n".join(lines), encoding="utf-8")


def load_blockers() -> list[dict]:
    """All recorded blockers, for a script/report that wants to check
    what's currently outstanding rather than just append a new one."""
    if not BLOCKERS_JSON.exists():
        return []
    try:
        return json.loads(BLOCKERS_JSON.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
