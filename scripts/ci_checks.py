#!/usr/bin/env python3
"""Host-agnostic governance check sequence.

The single source of truth for what "the guard checks pass" means —
callable from any CI system (GitHub Actions, GitLab CI, Bitbucket
Pipelines, Jenkins, a local pre-push hook, ...), not only the GitHub
Actions workflow this repo ships by default.

Before this script existed, the check sequence lived only as a list of
`run:` steps inside `.github/workflows/governance-guard.yml`. Every
individual check is plain, portable Python with zero GitHub dependency —
but because the *sequence* itself was written down nowhere else, a
project using lawkeeper on a non-GitHub host (GitLab, Bitbucket,
self-hosted Gitea, a bare repo with no forge at all) had no CI backstop
at all unless someone manually re-derived the step list by reading the
YAML. Law 7 (one source of truth) applied to the check sequence itself:
this script is now the one place it lives. `governance-guard.yml` is a
thin, optional GitHub-specific trigger wrapper around it — bring your own
equivalent trigger on another host and this script is everything you need.

Note what this deliberately does NOT replace: the local git hooks
(`scripts/git-hooks/`, installed via `install_hooks.py`) are the real,
host-independent protection — they run before a commit even exists,
on any machine, with no CI of any kind required. This script is only
the backstop for the case those hooks were bypassed or never installed.

Usage:
    python scripts/ci_checks.py             # the always-run checks
    python scripts/ci_checks.py --on-push    # also run the push-only
                                              # commit-message check

The --on-push check must run against the actual commit landing on a
branch, not a host's synthetic PR-merge commit (which never carries a
Tests:/Verification: line and often isn't even the commit that ends up
on the trunk) — see validate_commit_msg.py's own comments. Pass
--on-push only from a push-style trigger, never from a pull-request/
merge-request-style one.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# (description, command) — run in order, stop at the first failure, same
# fail-fast semantics as a CI job's step list.
CHECKS: list[tuple[str, list[str]]] = [
    ("Local dependencies present for imported declared packages",
     [sys.executable, "scripts/check_local_dependencies.py", "--warn"]),
    ("Compliance watchdog — constitution laws match",
     [sys.executable, "scripts/compliance_watchdog.py", "--check-laws"]),
    ("Compliance watchdog — no new violations vs baseline",
     [sys.executable, "scripts/compliance_watchdog.py", "--check-baseline"]),
    ("Dependency tool registry (phantom / orphan / unwired)",
     [sys.executable, "scripts/toolcheck.py"]),
    ("System self-audit (Law 16 — enforcement layers active and correct)",
     [sys.executable, "scripts/system_audit.py"]),
    ("Meta-tests for the guard scripts (Law 16.5)",
     [sys.executable, "-m", "pytest", "tests/test_guard_scripts.py", "-q"]),
]

PUSH_ONLY_CHECK = (
    "Block unauthorized governance edits and unmarked provisional work",
    [sys.executable, "scripts/validate_commit_msg.py"],
)


def run(description: str, cmd: list[str]) -> int:
    print(f"\n=== {description} ===")
    result = subprocess.run(cmd, cwd=REPO_ROOT)
    return result.returncode


def main() -> int:
    on_push = "--on-push" in sys.argv

    checks = list(CHECKS)
    if on_push:
        checks.insert(0, PUSH_ONLY_CHECK)  # cheapest, most decisive check first

    for description, cmd in checks:
        code = run(description, cmd)
        if code != 0:
            print(f"\nFAILED: {description}", file=sys.stderr)
            return code

    print("\nALL GOVERNANCE CHECKS PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
