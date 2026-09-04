"""Law 18 — Tests must be governed.

Structural enforcement: the governed-test infrastructure must exist — the governed
runner (scripts/governed_test.py), the theory-card directory (test_governance/
cards/), and the theory reference (docs/TEST_THEORY.md). The runner itself does
the runtime enforcement (refuses to run a test without a card, demands
classification on failure, supports --mutate and adversarial-review state).

This is the repo-agnostic portion: a project that declares it has tests (a tests/
directory) must govern them. A project with no tests/ is exempt.
"""
from __future__ import annotations

from pathlib import Path

from guardrail.core.primitives import CheckResult, Law, Status

REQUIRED_FILES = [
    "scripts/governed_test.py",
    "docs/TEST_THEORY.md",
]
REQUIRED_DIRS = [
    "test_governance/cards",
]


class Law18(Law):
    law_id = 18
    title = "Tests must be governed"
    severity = "must"

    @property
    def description(self) -> str:
        return "Every test has a theory card (oracle, threshold, blind spot, trust level); results are untrusted until adversarially reviewed."

    def check(self, repo_root: Path, config) -> list[CheckResult]:
        has_tests = (repo_root / "tests").is_dir()
        if not has_tests:
            return [
                CheckResult(
                    18,
                    Status.PASS,
                    "No tests/ directory — Law 18 not applicable.",
                    {"tests_dir": False},
                )
            ]
        missing = [f for f in REQUIRED_FILES if not (repo_root / f).exists()]
        missing += [d for d in REQUIRED_DIRS if not (repo_root / d).is_dir()]
        if missing:
            return [
                CheckResult(
                    18,
                    Status.FAIL,
                    "Test-governance infrastructure missing (Law 18): " + ", ".join(missing),
                    {"missing": missing},
                )
            ]
        return [
            CheckResult(
                18,
                Status.PASS,
                "Test-governance infrastructure present: governed runner, theory cards, reference.",
                {"files": REQUIRED_FILES, "dirs": REQUIRED_DIRS},
            )
        ]
