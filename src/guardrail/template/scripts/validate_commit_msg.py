"""commit-msg validation: governance guard + provisional-work marker + audit declaration.

Used by scripts/git-hooks/commit-msg.
Rules:
  1. Changes to GOVERNANCE_FILES require GOVERNANCE-UPDATE in the message.
  2. Commit messages containing provisional keywords (experimental, spike, temp,
     provisional, draft, wip) must include an AUDIT: marker or an explicit marker.
  3. Commits that modify or add .py files must declare their verification
     (Law 14: Audit before you commit) via a "Tests:" or "Verification:" line.
"""

import re
import subprocess
import sys

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
    """True if a .py file was added or modified — staged (pending commit) or
    in the last commit (staged=False, for validating an already-made commit)."""
    if staged:
        cmd = ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR"]
    else:
        cmd = ["git", "diff", "--name-only", "--diff-filter=ACMR", "HEAD~1", "HEAD"]
    result = subprocess.run(
        cmd, capture_output=True, text=True, encoding="utf-8", errors="replace"
    )
    return any(line.strip().endswith(".py")
               for line in result.stdout.splitlines() if line.strip())


def looks_provisional(msg):
    low = msg.lower()
    return any(kw in low for kw in PROVISIONAL_KEYWORDS)


def main():
    message_file = sys.argv[1] if len(sys.argv) > 1 else None
    msg = read_message(message_file)

    # A real git commit-msg hook always receives the message-file argument
    # (see scripts/git-hooks/commit-msg: `python validate_commit_msg.py
    # "$MSG_FILE"`) and runs before the commit exists, so staged changes are
    # what matters. Without that argument (e.g. CI validating an
    # already-made commit after the fact — governance-guard.yml calls this
    # with no argument), there's nothing staged to check: check the last
    # commit instead.
    #
    # Found broken: this used to be `msg = read_message(message_file) if
    # message_file else ""`, discarding read_message's own git-log fallback
    # and forcing msg="" in CI, while every rule below hardcoded
    # staged=True. Since a fresh CI checkout has nothing staged, every rule
    # silently passed on every commit, regardless of content.
    staged = message_file is not None

    # Rule 1: governance guard
    if governance_changed(staged=staged):
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
    if python_changed(staged=staged) and not VERIFICATION_PATTERN.search(msg):
        print(
            f"BLOCKED: commit changes .py file(s) but does not declare verification.\n"
            f"Law 14 (Audit before you commit) requires a 'Tests:' or 'Verification:' "
            f"line in the commit message, e.g.\n"
            f"    Tests: pytest tests/test_x.py -q (12 passed)\n"
            f"If you genuinely could not verify, declare it explicitly: 'AUDIT: unverified'.",
            file=sys.stderr,
        )
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
