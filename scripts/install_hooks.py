"""Install the lawkeeper git hooks (cross-platform).

Sets core.hooksPath to the versioned `scripts/git-hooks` directory so hook
updates merge with the repo. Safe to re-run after every pull.

Usage:  python -m guardrail.install_hooks     (installed package)
        python scripts/install_hooks.py        (from repo root)
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main() -> int:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, encoding="utf-8", errors="replace"
        )
    except OSError as e:
        print(f"git not found: {e}", file=sys.stderr)
        return 2
    root = Path(out.stdout.strip())
    if not root:
        print("Not a git repo.", file=sys.stderr)
        return 1
    hooks_dir = root / "scripts" / "git-hooks"
    for required in ("pre-commit", "commit-msg", "pre-push"):
        hook_path = hooks_dir / required
        if not hook_path.is_file():
            print(f"Hook source missing: {hook_path}", file=sys.stderr)
            return 1
        # Belt-and-suspenders: git silently no-ops a non-executable hook
        # (just a soft warning, the commit still goes through). Force the
        # bit here too, not just at scaffold time, so a fresh `git clone`
        # or a manual copy that dropped +x can't leave enforcement
        # silently disabled.
        mode = hook_path.stat().st_mode
        if not (mode & 0o111):
            hook_path.chmod(mode | 0o111)
    rel = "scripts/git-hooks"
    proc = subprocess.run(["git", "config", "core.hooksPath", rel])
    if proc.returncode != 0:
        print("git config core.hooksPath failed", file=sys.stderr)
        return 1
    print(f"lawkeeper hooks ACTIVE via core.hooksPath={rel}")
    print("Edits to docs/AI_CONSTITUTION.md and protected governance files require GOVERNANCE-UPDATE.")
    print("Run `python scripts/system_audit.py` to verify the full enforcement stack.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
