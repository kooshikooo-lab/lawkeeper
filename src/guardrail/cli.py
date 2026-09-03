"""lawkeeper CLI — make any git project constitution-governed.

Commands:
  lawkeeper init [DIR]   scaffold full governance into a project (constitution,
                        hooks, guards, CI, template files)
  lawkeeper status       show which enforcement layers are active (human-safe)
  lawkeeper version
"""

from __future__ import annotations

import argparse
import importlib.resources
import subprocess
import sys
from pathlib import Path

from guardrail import __version__

# Resolved via importlib.resources rather than a path relative to this file's
# disk location. A path like Path(__file__).parent.parent.parent only works
# for an editable/source-checkout install; once the package is built into a
# wheel and installed normally, cli.py lives directly under site-packages/
# guardrail/ and that ".parent.parent.parent" walk lands somewhere that isn't
# even part of this package. importlib.resources resolves relative to the
# installed package itself, so it works the same way in every install mode
# (editable, wheel, zipapp). The template MUST live at src/guardrail/template
# (inside the package) for this — and for the wheel's package-data — to work.
def _template_root() -> Path:
    return Path(str(importlib.resources.files("guardrail") / "template"))


def _repo_root(start: Path = Path.cwd()) -> Path | None:
    """Return the git repo root containing `start`, or None if there isn't one.

    (The previous version returned `Path(out.stdout.strip()) or start` —
    but a Path object is always truthy, even Path(""), so on failure it
    silently returned `start` disguised as a valid repo root instead of
    signaling failure. Callers must be able to tell "no repo" from "found
    a repo", so this returns None explicitly.)
    """
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=start, capture_output=True, text=True,
            encoding="utf-8", errors="replace"
        )
    except OSError:
        return None
    if out.returncode != 0 or not out.stdout.strip():
        return None
    return Path(out.stdout.strip())


def _render(src: Path, dst: Path, project_name: str) -> None:
    text = src.read_text(encoding="utf-8", errors="replace")
    rendered = (text
                .replace("__PROJECT_NAME__", project_name)
                .replace("__PROJECT_NAME_TITLE__", project_name.replace("-", " ").title()))
    dst.write_text(rendered, encoding="utf-8", newline="\n")


def cmd_init(args: argparse.Namespace) -> int:
    target = Path(args.dir or ".").resolve()

    # Find the git repo root WITHOUT silently falling back to the filesystem
    # root. If target isn't inside a git repo, refuse and say so — never
    # guess. (The old code walked parent-by-parent until it ran out of
    # parents, and on a directory with no .git anywhere would happily
    # settle on "/" or "C:\" and try to scaffold there.)
    root = _repo_root(target)
    if root is None:
        print(
            f"lawkeeper: {target} is not inside a git repository.\n"
            f"Run `git init` first (lawkeeper governs a git project; it "
            f"will not guess where your project root is).",
            file=sys.stderr,
        )
        return 1

    already_governed = (root / ".guardrail.json").exists() or (root / "docs/AI_CONSTITUTION.md").exists()
    if already_governed and not args.force:
        print(
            f"lawkeeper: {root} already looks governed "
            f"(.guardrail.json or docs/AI_CONSTITUTION.md present).\n"
            f"Re-run with --force if you intend to overwrite the existing governance files.",
            file=sys.stderr,
        )
        return 1

    template_root = _template_root()
    if not template_root.exists():
        print(
            f"lawkeeper: internal error — template directory not found at "
            f"{template_root}. This is a packaging bug, not a project problem; "
            f"please report it rather than proceeding.",
            file=sys.stderr,
        )
        return 1

    project_name = args.name or root.name
    dst_root = root

    # Copy template tree (rendering placeholders), tracking what we wrote so
    # we can verify afterward instead of just trusting the loop ran.
    written: list[Path] = []
    for rel in template_root.rglob("*"):
        if rel.is_dir():
            continue
        rel_target = rel.relative_to(template_root)
        dst = dst_root / rel_target
        dst.parent.mkdir(parents=True, exist_ok=True)
        if rel.suffix == ".tmpl":
            dst_final = dst.with_suffix("")
        else:
            dst_final = dst
        _render(rel, dst_final, project_name)
        written.append(dst_final)
        # Git hooks must be executable or git silently no-ops them (just a
        # soft "hint", commit still succeeds) — found by actually running
        # `git commit` against a freshly-scaffolded project: install_hooks.py
        # reported "hooks ACTIVE" and the commit sailed through with zero
        # enforcement. write_text() doesn't preserve the +x bit, so every
        # freshly scaffolded hook was silently inert until a human happened
        # to chmod it manually.
        if dst_final.parent.name == "git-hooks":
            dst_final.chmod(dst_final.stat().st_mode | 0o111)

    # Write project config.
    import json
    config = {
        "project_name": project_name,
        "machines": args.machines.split(",") if args.machines else ["desktop", "laptop"],
        "canonical_branches": ["main"],
    }
    (dst_root / ".guardrail.json").write_text(json.dumps(config, indent=2), encoding="utf-8")
    written.append(dst_root / ".guardrail.json")

    # FAIL LOUDLY if nothing meaningful was actually written. A silent
    # zero-file "success" is the worst outcome for a governance tool: the
    # user believes they're protected and they are not.
    required = [
        dst_root / "docs" / "AI_CONSTITUTION.md",
        dst_root / "scripts" / "install_hooks.py",
        dst_root / ".guardrail.json",
    ]
    missing = [str(p) for p in required if not p.exists()]
    if missing or len(written) < 3:
        print(
            "lawkeeper: init did not complete correctly — expected files are "
            "missing after the copy step:\n  " + "\n  ".join(missing or ["(fewer files written than expected)"]) +
            "\nDo NOT treat this project as governed. This is a bug in lawkeeper "
            "itself, not something you did wrong.",
            file=sys.stderr,
        )
        return 1

    # Seed a compliance baseline against the just-copied guard scripts
    # themselves. Without this, `system_audit.py` FAILS on step 4 of this
    # project's own quickstart, on every single freshly scaffolded project,
    # before the user has written a line of code: compliance_watchdog.py's
    # AST checks (module_mutable, module_size, ...) flag the guard scripts
    # it was just handed (PLACEMENT_RULES, GOVERNANCE_FILES, and similar
    # module-level constants all count as "mutable globals"), and with no
    # baseline on disk yet, every one of those reads as a brand-new
    # violation and blocks the audit. compliance_watchdog.py already has a
    # documented mechanism for exactly this — "pre-existing debt does not
    # fail the check, only violations absent from the baseline do" — it was
    # just never invoked automatically. Found by actually running the
    # documented quickstart against a fresh scaffold, not by inspection.
    baseline_script = dst_root / "scripts" / "compliance_watchdog.py"
    baseline_seeded = False
    if baseline_script.exists():
        result = subprocess.run(
            [sys.executable, str(baseline_script), "--baseline"],
            cwd=dst_root, capture_output=True, text=True,
            encoding="utf-8", errors="replace",
        )
        baseline_file = dst_root / "scripts" / "compliance_baseline.json"
        baseline_seeded = result.returncode == 0 and baseline_file.exists()
        if baseline_seeded:
            written.append(baseline_file)

    print(f"lawkeeper: scaffolding written to {dst_root} ({len(written)} files)")
    if baseline_seeded:
        print("lawkeeper: compliance baseline seeded — system_audit.py should PASS as-is.")
    else:
        print(
            "lawkeeper: WARNING — could not seed the compliance baseline "
            "automatically. Run `python scripts/compliance_watchdog.py "
            "--baseline` yourself before system_audit.py, or it will FAIL "
            "on the guard scripts' own module-level constants.",
            file=sys.stderr,
        )
    print("Next steps:")
    print("  1. pip install -e .   # from the project root")
    print("  2. python scripts/install_hooks.py   # installs pre-commit, commit-msg, pre-push")
    print("  3. git add -A && git commit -m 'chore: lawkeeper governance bootstrap' -m 'GOVERNANCE-UPDATE'")
    print("  4. python scripts/system_audit.py    # must PASS before any real commit")
    print("  5. git push && open a PR (branch protection requires it)")
    return 0


def cmd_status(_: argparse.Namespace) -> int:
    """Human-safe summary of enforcement layers. Never destructive."""
    root = _repo_root()
    if root is None:
        print("lawkeeper: not inside a git repository.")
        return 1
    print(f"repo: {root}")
    print(f"project: {(root / '.guardrail.json').exists() and 'governed' or 'NOT governed by lawkeeper'}")
    hooks = root / ".git" / "hooks"
    cfg = subprocess.run(["git", "config", "--get", "core.hooksPath"],
                         cwd=root, capture_output=True, text=True,
                         encoding="utf-8", errors="replace").stdout.strip()
    print(f"core.hooksPath: {cfg or '(unset)'}")
    audit = root / "scripts" / "system_audit.py"
    print(f"system_audit.py: {'present' if audit.exists() else 'MISSING'}")
    if audit.exists():
        print("\nRun `python scripts/system_audit.py` to verify all enforcement layers are active.")
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="lawkeeper",
        description="Constitution-as-code governance for agentic + vibe-coded projects.",
    )
    parser.add_argument("--version", action="store_true", help="print version and exit")
    sub = parser.add_subparsers(dest="cmd")

    p_init = sub.add_parser("init", help="scaffold full governance into a project")
    p_init.add_argument("dir", nargs="?", default=".", help="target directory (default: .)")
    p_init.add_argument("--name", help="project name for templates")
    p_init.add_argument("--machines", help="comma-separated machine names, e.g. desktop,laptop")
    p_init.add_argument("--force", action="store_true", help="overwrite existing governance")

    sub.add_parser("status", help="show enforcement-layer status (read-only)")

    args = parser.parse_args(argv)
    if args.version or args.cmd is None:
        print(f"lawkeeper {__version__}")
        return 0
    if args.cmd == "init":
        return cmd_init(args)
    if args.cmd == "status":
        return cmd_status(args)
    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
