"""commit-msg validation: governance guard + provisional-work marker + audit declaration.

Used by scripts/git-hooks/commit-msg.
Rules:
  1. Changes to GOVERNANCE_FILES require GOVERNANCE-UPDATE in the message.
  2. Commit messages containing provisional keywords (experimental, spike, temp,
     provisional, draft, wip) must include an AUDIT: marker or an explicit marker.
  3. Commits that modify or add .py files must declare their verification
     (Law 14: Audit before you commit) via a "Tests:" or "Verification:" line.
  4. Commits touching configured human-facing paths must declare a
     "Human-check:" line (Law 23: a metric is not the request) -- what was
     directly viewed/read/run, compared to what the user actually asked
     for. Paths are declared per-project in .guardrail.json's
     human_facing_paths key; empty/absent means this rule never fires.
"""

import fnmatch
import json
import re
import subprocess
import sys
from pathlib import Path

GOVERNANCE_FILES = [
    "docs/CONSTRAINTS_AND_PREFERENCES.md",
    "docs/AI_CONSTITUTION.md",
    "docs/REMINDERS.md",
    "docs/ARCHITECTURE_DECISIONS.md",
    "docs/ARCHITECTURE_CHECKLIST.md",
    "docs/COMPLIANCE_CHECK.md",
    "docs/AI_FAILURE_PATTERNS.md",
    "AGENTS.md",
]

PROVISIONAL_KEYWORDS = [
    "experimental", "spike", "temp", "temporary", "provisional", "draft",
    "wip", "work in progress", "exploratory", "poc", "proof of concept",
    "unverified", "unchecked", "placeholder",
]

GOVERNANCE_MARKER = "GOVERNANCE-UPDATE"
AUDIT_MARKER = "AUDIT:"
VERIFICATION_PATTERN = re.compile(r"^(Tests?|Verification):\s*\S", re.IGNORECASE | re.MULTILINE)
HUMAN_CHECK_PATTERN = re.compile(r"^Human-check:\s*\S", re.IGNORECASE | re.MULTILINE)


def read_message(message_file):
    if message_file:
        try:
            with open(message_file, "r", encoding="utf-8", errors="replace") as f:
                return f.read()
        except OSError:
            return ""
    result = subprocess.run(
        ["git", "log", "-1", "--format=%B"],
        capture_output=True, text=True, encoding="utf-8", errors="replace"
    )
    return result.stdout


def governance_changed(staged=False):
    for f in GOVERNANCE_FILES:
        if staged:
            result = subprocess.run(
                ["git", "diff", "--cached", "HEAD", "--", f],
                capture_output=True, text=True, encoding="utf-8", errors="replace"
            )
        else:
            result = subprocess.run(
                ["git", "diff", "HEAD~1", "HEAD", "--", f],
                capture_output=True, text=True, encoding="utf-8", errors="replace"
            )
        if result.stdout.strip():
            return True
    return False


def python_changed(staged=True):
    """True if any staged .py file was added or modified."""
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR"],
        capture_output=True, text=True, encoding="utf-8", errors="replace"
    )
    return any(line.strip().endswith(".py")
               for line in result.stdout.splitlines() if line.strip())


def load_human_facing_patterns():
    """Glob patterns for human-facing paths, from .guardrail.json.

    Self-contained rather than importing compliance_watchdog.py (Law 3
    tension, deliberately: this file is invoked directly by a git hook and
    must not depend on cross-script imports working from an arbitrary cwd
    -- the ~8-line duplication is the safer choice here, same judgment
    compliance_watchdog.py's own load_guardrail_config already made for
    itself). Absent/empty means this rule never fires -- a project that
    hasn't opted in isn't affected.
    """
    try:
        path = Path(".guardrail.json")
        if path.exists():
            cfg = json.loads(path.read_text(encoding="utf-8"))
            return [str(p) for p in cfg.get("human_facing_paths", [])]
    except (OSError, ValueError):
        pass
    return []


def human_facing_changed(staged=True):
    """True if any staged file matches a configured human-facing glob."""
    patterns = load_human_facing_patterns()
    if not patterns:
        return False
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR"],
        capture_output=True, text=True, encoding="utf-8", errors="replace"
    )
    files = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    return any(fnmatch.fnmatch(f, pat) for f in files for pat in patterns)


_PROVISIONAL_PATTERN = re.compile(
    r"\b(?:" + "|".join(re.escape(kw) for kw in PROVISIONAL_KEYWORDS) + r")\b",
    re.IGNORECASE,
)


def looks_provisional(msg):
    """True if msg contains a whole provisional keyword (word-boundary match).

    A plain substring check (`kw in low`) previously matched "temp" inside
    ordinary words like "template" -- e.g. a commit touching a `template/`
    directory was falsely flagged as provisional work. `\\b` word boundaries
    fix this while still matching keyword variants (temp/temporary) and
    multi-word phrases (work in progress) as whole units.
    """
    return bool(_PROVISIONAL_PATTERN.search(msg))


def main():
    message_file = sys.argv[1] if len(sys.argv) > 1 else None
    msg = read_message(message_file) if message_file else ""

    # Rule 1: governance guard
    if governance_changed(staged=True):
        if GOVERNANCE_MARKER not in msg:
            print(
                f"BLOCKED: a protected governance file was modified without "
                f"'{GOVERNANCE_MARKER}' in the commit message.\n"
                f"Protected files: {', '.join(GOVERNANCE_FILES)}\n"
                f"If the edit is authorized, include '{GOVERNANCE_MARKER}' in the message.",
                file=sys.stderr,
            )
            return 1
        print(f"OK: governance change with {GOVERNANCE_MARKER}.")

    # Rule 2: provisional work marker
    if looks_provisional(msg) and AUDIT_MARKER not in msg:
        print(
            f"BLOCKED: commit message looks provisional but is missing '{AUDIT_MARKER}'.\n"
            f"Provisional keywords: {', '.join(PROVISIONAL_KEYWORDS)}\n"
            f"Add '{AUDIT_MARKER}' to the message if this work is exploratory/provisional.",
            file=sys.stderr,
        )
        return 1

    # Rule 3: audit declaration (Law 14) for Python commits
    if python_changed(staged=True) and not VERIFICATION_PATTERN.search(msg):
        print(
            f"BLOCKED: commit changes .py file(s) but does not declare verification.\n"
            f"Law 14 (Audit before you commit) requires a 'Tests:' or 'Verification:' "
            f"line in the commit message, e.g.\n"
            f"    Tests: pytest tests/test_x.py -q (12 passed)\n"
            f"If you genuinely could not verify, declare it explicitly: 'AUDIT: unverified'.",
            file=sys.stderr,
        )
        return 1

    # Rule 4: human-facing check declaration (Law 23)
    if human_facing_changed(staged=True) and not HUMAN_CHECK_PATTERN.search(msg):
        print(
            f"BLOCKED: commit touches a configured human-facing path but does not "
            f"declare a direct check.\n"
            f"Law 23 (a metric is not the request) requires a 'Human-check:' line "
            f"stating what you actually opened/read/ran, compared to what was asked, "
            f"e.g.\n"
            f"    Human-check: opened dashboard.html in browser, rate/kill buttons "
            f"render and work; matches 'unify watch+rate+kill' from the plan\n"
            f"Tests passing or a build succeeding is not a substitute -- state what "
            f"you actually looked at.",
            file=sys.stderr,
        )
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
