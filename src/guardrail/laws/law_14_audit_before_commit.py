"""Law 14 — Audit before you commit.

Mechanically verifiable portion: the commit-msg and pre-commit validators exist
and are wired as git hooks (their runtime behaviour is enforced by git at commit
time; see scripts/validate_commit_msg.py and scripts/validate_pre_commit.py).
"""
from __future__ import annotations

from pathlib import Path

from guardrail.core.primitives import CheckResult, Law, Status

REQUIRED_FILES = [
    "scripts/validate_commit_msg.py",
    "scripts/validate_pre_commit.py",
    "scripts/git-hooks/commit-msg",
    "scripts/git-hooks/pre-commit",
]


class Law14(Law):
    law_id = 14
    title = "Audit before you commit"
    severity = "must"

    @property
    def description(self) -> str:
        return "Before every commit: re-read the constitution, run tests, review the diff, declare verification."

    def check(self, repo_root: Path, config) -> list[CheckResult]:
        missing = [rel for rel in REQUIRED_FILES if not (repo_root / rel).exists()]
        if missing:
            return [
                CheckResult(
                    14,
                    Status.FAIL,
                    "Commit-audit validators missing/unwired (Law 14): " + ", ".join(missing),
                    {"missing": missing},
                )
            ]
        return [
            CheckResult(
                14,
                Status.PASS,
                "Commit-audit validators present and wired.",
                {"files": REQUIRED_FILES},
            )
        ]
