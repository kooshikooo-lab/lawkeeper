"""Law 12 — Read before you act.

Structural readiness for the coordination protocol: every session must have a
machine-readable working agreement (AGENTS.md) to re-read before acting.
"""
from __future__ import annotations

from pathlib import Path

from guardrail.core.primitives import CheckResult, Law, Status


class Law12(Law):
    law_id = 12
    title = "Read before you act"
    severity = "must"

    @property
    def description(self) -> str:
        return "Every session re-reads state, reminders, and pending team messages before acting."

    def check(self, repo_root: Path, config) -> list[CheckResult]:
        agents = repo_root / "AGENTS.md"
        if not agents.exists():
            return [
                CheckResult(
                    12,
                    Status.FAIL,
                    "AGENTS.md missing — no working agreement for the session to re-read (Law 12).",
                    {"file": "AGENTS.md"},
                )
            ]
        return [
            CheckResult(
                12,
                Status.PASS,
                "AGENTS.md present.",
                {"file": "AGENTS.md"},
            )
        ]
