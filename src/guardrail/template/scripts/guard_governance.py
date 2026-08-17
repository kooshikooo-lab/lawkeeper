"""Governance file guard — blocks unauthorized edits to docs/CONSTRAINTS_AND_PREFERENCES.md.

The boot sequence and communications protocol live in this one file. It has been
rewritten before based on agent assumptions rather than instructions. This guard
enforces that any change to it is explicitly authorized.

Used by:
- commit-msg hook (scripts/git-hooks/commit-msg) on every commit
- CI workflow (.github/workflows/governance-guard.yml) on every push

An edit is authorized if the commit message contains the marker "GOVERNANCE-UPDATE".

Exit codes: 0 = OK (no change, or authorized change), 1 = blocked.
"""

import subprocess
import sys

GOVERNANCE_FILES = [
    # The boot sequence + communications protocol live here. Instruction-only.
    "docs/CONSTRAINTS_AND_PREFERENCES.md",
]
MARKER = "GOVERNANCE-UPDATE"


def run_git(args):
    try:
        result = subprocess.run(
            ["git"] + args, capture_output=True, text=True,
            encoding="utf-8", errors="replace"
        )
        return result.stdout, result.returncode
    except Exception:
        return "", 1


def commit_message(message_file=None):
    if message_file:
        try:
            with open(message_file, "r", encoding="utf-8", errors="replace") as f:
                return f.read()
        except OSError:
            return ""
    out, _ = run_git(["log", "-1", "--format=%B"])
    return out.strip()


def governance_changed(staged=False):
    for f in GOVERNANCE_FILES:
        if staged:
            out, _ = run_git(["diff", "--cached", "HEAD", "--", f])
        else:
            out, _ = run_git(["diff", "HEAD~1", "HEAD", "--", f])
        if out.strip():
            return True
    return False


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Governance file guard")
    parser.add_argument("--staged", action="store_true",
                        help="check the staged diff (for commit-msg hook)")
    parser.add_argument("--message-file",
                        help="read commit message from this file (hook passes it)")
    args = parser.parse_args()

    msg = commit_message(args.message_file)
    if governance_changed(staged=args.staged):
        if MARKER in msg:
            print(f"OK: governance file changed with {MARKER} authorization.")
            return 0
        print(
            f"BLOCKED: a protected governance file was modified without {MARKER} "
            f"in the commit message.\n"
            f"Protected: {', '.join(GOVERNANCE_FILES)}\n"
            f"This file is instruction-only. If the edit is authorized, include "
            f"'{MARKER}' in the commit message.",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
