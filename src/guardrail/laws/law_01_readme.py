"""Law 1 — Architecture over features.

A project must declare its purpose and structure (README) before features.
"""
from __future__ import annotations

from pathlib import Path

from guardrail.core.primitives import CheckResult, Law, Status


class Law01(Law):
    law_id = 1
    title = "Architecture over features"
    severity = "must"

    @property
    def description(self) -> str:
        return "A project's structure and interfaces are decided first; features conform to them."

    def check(self, repo_root: Path, config) -> list[CheckResult]:
        readme = repo_root / "README.md"
        if not readme.exists():
            return [
                CheckResult(
                    1,
                    Status.FAIL,
                    "README.md missing — project purpose/structure undeclared (Law 1).",
                    {"file": "README.md"},
                )
            ]
        text = readme.read_text(encoding="utf-8", errors="replace")
        if len(text.strip()) < 40:
            return [
                CheckResult(
                    1,
                    Status.WARN,
                    "README.md is nearly empty — document purpose and structure.",
                    {"file": "README.md", "chars": len(text)},
                )
            ]
        return [
            CheckResult(
                1,
                Status.PASS,
                "README.md declares project purpose and structure.",
                {"file": "README.md"},
            )
        ]
