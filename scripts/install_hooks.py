"""Install the lawkeeper git hooks (cross-platform).

Sets core.hooksPath to the versioned `scripts/git-hooks` directory so hook
updates merge with the repo. Safe to re-run after every pull.

Usage:  python -m guardrail.install_hooks     (installed package)
        python scripts/install_hooks.py        (from repo root)
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

STOP_HOOK_COMMAND = "python ${CLAUDE_PROJECT_DIR}/scripts/claude_stop_hook.py"


def install_claude_stop_hook(root: Path) -> str:
    """Register scripts/claude_stop_hook.py in .claude/settings.json's Stop
    hook list -- mechanical version of Law 22's amendment (a response may
    not end on a stated future action with no tool call in that turn).

    Merges into any existing settings.json rather than overwriting it --
    a real project may already have other hooks/settings configured.
    Idempotent: re-running does not duplicate the entry.
    """
    settings_path = root / ".claude" / "settings.json"
    settings_path.parent.mkdir(parents=True, exist_ok=True)

    if settings_path.exists():
        try:
            settings = json.loads(settings_path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as e:
            return f"SKIPPED: .claude/settings.json exists but is not valid JSON ({e}) -- fix it by hand first."
    else:
        settings = {}

    hooks = settings.setdefault("hooks", {})
    stop_list = hooks.setdefault("Stop", [])

    already_installed = any(
        entry.get("command") == STOP_HOOK_COMMAND for entry in stop_list if isinstance(entry, dict)
    )
    if not already_installed:
        stop_list.append({"type": "command", "command": STOP_HOOK_COMMAND, "timeout": 10})

    settings_path.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")
    return f"Claude Code Stop hook {'already registered' if already_installed else 'registered'} in {settings_path}"


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

    print(install_claude_stop_hook(root))

    print("Run `python scripts/system_audit.py` to verify the full enforcement stack.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
