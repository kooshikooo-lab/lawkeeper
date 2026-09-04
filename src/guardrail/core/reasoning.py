"""Internal-reasoning toggle for the agent.

Law 12 discipline: the reasoning behind a model's actions must be either visible
(for audit and cross-machine handoff) or suppressible (for clean project
artifacts). The toggle lives in .guardrail.json so it is version-controlled and
shared across machines.

    from guardrail.core.reasoning import emit, is_enabled
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path


def is_enabled(config) -> bool:
    """True if the project has opted to record/show internal reasoning."""
    return bool(getattr(config, "show_internal_reasoning", False))


def emit(reason: str, repo_root: Path, config) -> str:
    """Record reasoning to the configured log when enabled.

    Returns the log path when recorded, or "" when reasoning is hidden (nothing
    is written). Lets callers know whether the trace was captured.
    """
    if not is_enabled(config):
        return ""
    rel = getattr(config, "reasoning_log", "docs/reasoning.log")
    log = Path(repo_root) / rel
    log.parent.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with log.open("a", encoding="utf-8") as fh:
        fh.write(f"[{ts}] {reason.rstrip()}\n")
    return str(log)
