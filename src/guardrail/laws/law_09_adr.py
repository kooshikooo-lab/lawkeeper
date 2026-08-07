"""Law 9 — Document architectural decisions.

Every significant architectural decision is an ADR in
docs/ARCHITECTURE_DECISIONS.md.
"""
from __future__ import annotations

from pathlib import Path

from guardrail.core.primitives import CheckResult, Law, Status


class Law09(Law):
    law_id = 9
    title = "Document architectural decisions"
    severity = "should"

    @property
    def description(self) -> str:
        return "Every significant architectural decision is an ADR in docs/ARCHITECTURE_DECISIONS.md."

    def check(self, repo_root: Path, config) -> list[CheckResult]:
        adr = repo_root / "docs/ARCHITECTURE_DECISIONS.md"
        if not adr.exists():
            return [
                CheckResult(
                    9,
                    Status.FAIL,
                    "docs/ARCHITECTURE_DECISIONS.md missing — architectural decisions undocumented (Law 9).",
                    {"file": "docs/ARCHITECTURE_DECISIONS.md"},
                )
            ]
        text = adr.read_text(encoding="utf-8", errors="replace").strip()
        if not text:
            return [
                CheckResult(
                    9,
                    Status.WARN,
                    "docs/ARCHITECTURE_DECISIONS.md is empty — record at least one ADR.",
                    {"file": "docs/ARCHITECTURE_DECISIONS.md"},
                )
            ]
        return [
            CheckResult(
                9,
                Status.PASS,
                "docs/ARCHITECTURE_DECISIONS.md records architectural decisions.",
                {"file": "docs/ARCHITECTURE_DECISIONS.md"},
            )
        ]
