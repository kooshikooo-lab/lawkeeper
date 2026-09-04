"""Law 16 — The enforcement system must itself be enforced.

Verifies the enforcement apparatus is present: the guard scripts, the guard-
script test suite, and the project config. (Runtime enforcement is verified by
python scripts/system_audit.py; the guards' own tests live in tests/.)
"""
from __future__ import annotations

from pathlib import Path

from guardrail.core.primitives import CheckResult, Law, Status

GUARD_SCRIPTS = [
    "scripts/guard_branch.py",
    "scripts/guard_governance.py",
    "scripts/compliance_watchdog.py",
    "scripts/merge_gate.py",
    "scripts/validate_imports.py",
    "scripts/validate_pre_commit.py",
    "scripts/validate_commit_msg.py",
]
REQUIRED_TESTS = [
    "tests/test_guard_scripts.py",
    "tests/test_adversarial_review_checker.py",
    "tests/test_code_compliance_checker.py",
]
CONFIG_FILE = ".guardrail.json"

REQUIRED = GUARD_SCRIPTS + REQUIRED_TESTS + [CONFIG_FILE]


class Law16(Law):
    law_id = 16
    title = "The enforcement system must itself be enforced"
    severity = "must"

    @property
    def description(self) -> str:
        return "Guards are mechanically enforced by local hooks + CI + system self-audit + tested guard scripts."

    def check(self, repo_root: Path, config) -> list[CheckResult]:
        missing = [rel for rel in REQUIRED if not (repo_root / rel).exists()]
        if missing:
            return [
                CheckResult(
                    16,
                    Status.FAIL,
                    "Enforcement system incomplete (Law 16): " + ", ".join(missing),
                    {"missing": missing},
                )
            ]
        return [
            CheckResult(
                16,
                Status.PASS,
                "Enforcement system present: guards, tests, and config.",
                {"files": REQUIRED},
            )
        ]
