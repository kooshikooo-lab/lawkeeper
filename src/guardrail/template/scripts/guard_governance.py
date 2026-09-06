"""Governance file guard — blocks unauthorized edits to a project's
protected governance files (scan_config.get_governance_files(); by
default docs/AI_CONSTITUTION.md, docs/CONSTRAINTS_AND_PREFERENCES.md,
docs/COMPLIANCE_CHECK.md, docs/ARCHITECTURE_DECISIONS.md,
docs/AI_FAILURE_PATTERNS.md, docs/TEST_THEORY.md, AGENTS.md).

Real bug found (GitHub Copilot review, PR #15): this docstring used to
say "docs/CONSTRAINTS_AND_PREFERENCES.md" specifically -- true when this
guard hardcoded a 1-file list, false since GOVERNANCE_FILES started
reading the shared, corrected multi-file list.

The boot sequence and communications protocol live in
docs/CONSTRAINTS_AND_PREFERENCES.md specifically. It has been rewritten
before based on agent assumptions rather than instructions -- this guard
enforces that any change to a protected file is explicitly authorized.

Real, separate finding (not this docstring's original claim, and not
fixed here): despite the "Used by" claim below, neither
scripts/git-hooks/commit-msg nor .github/workflows/governance-guard.yml
actually invoke this script -- validate_commit_msg.py's own Rule 1
already covers the same check and is what's actually wired in. This
script IS checked for importability (system_audit.py's GUARD_SCRIPTS)
and named in src/guardrail/laws/law_16_enforcement.py, so it isn't
literally dead, but "Used by" below currently overstates its real role.

Used by (as currently checked, not necessarily invoked per-commit):
- system_audit.py's guard-script importability check
- law_16_enforcement.py's guard-script inventory

An edit is authorized if the commit message contains the marker "GOVERNANCE-UPDATE".

Exit codes: 0 = OK (no change, or authorized change), 1 = blocked.
"""

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(subprocess.run(
    ["git", "rev-parse", "--show-toplevel"],
    capture_output=True, text=True, encoding="utf-8", errors="replace"
).stdout.strip() or Path.cwd())

try:
    from scan_config import get_governance_files  # normal `python scripts/x.py` run
except ImportError:
    # Same fallback as compliance_watchdog.py/toolcheck.py: a plain sibling
    # import only works when Python itself put scripts/ on sys.path.
    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    from scan_config import get_governance_files

# Real bug found 2026-09-06 (guardrail fit investigation): this guard only
# ever protected docs/CONSTRAINTS_AND_PREFERENCES.md, while
# validate_commit_msg.py's own separate hardcoded list protected 8 files
# (and Config.DEFAULTS a third, slightly different 8) -- three
# independently-drifting copies of "what's protected." Now reads the same
# shared, corrected list get_governance_files() resolves (real files on
# disk, not stale copies) -- see that function's own docstring for the
# specific drift found.
GOVERNANCE_FILES = get_governance_files(REPO_ROOT)
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
