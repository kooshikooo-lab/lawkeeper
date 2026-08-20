"""lawkeeper CLI — make any git project constitution-governed.

Commands:
  lawkeeper init [DIR]   scaffold full governance into a project (constitution,
                        hooks, guards, CI, template files)
  lawkeeper run          run constitution laws against the repo (exit non-zero on FAIL)
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

    print(f"lawkeeper: scaffolding written to {dst_root} ({len(written)} files)")
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

    p_run = sub.add_parser("run", help="run constitution laws against the repo")
    p_run.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    p_run.add_argument("--law", type=int, action="append", default=[],
                       help="run only the given law id (repeatable)")
    p_run.add_argument("--quiet", action="store_true", help="suppress output; exit code only")
    p_run.add_argument("--show-reasoning", action="store_true",
                       help="show the model's internal reasoning (overrides config)")
    p_run.add_argument("--hide-reasoning", action="store_true",
                       help="suppress internal reasoning (overrides config)")

    p_reason = sub.add_parser("reasoning",
                              help="record or show the model's internal reasoning")
    p_reason.add_argument("text", nargs="*", help="reasoning text to record")

    p_choose = sub.add_parser(
        "choose",
        help="interactive checkbox-choice protocol (lawkeeper choose --file spec.json)")
    p_choose.add_argument("--file", required=True, help="path to the choice spec JSON")
    p_choose.add_argument("--select", action="append", default=[],
                          help="pre-select an option id or 1-based number (non-interactive)")
    p_choose.add_argument("--custom", default=None,
                          help="free-text value (non-interactive)")
    p_choose.add_argument("--single", action="store_true",
                          help="single-select mode (clears other picks on toggle)")

    sub.add_parser("status", help="show enforcement-layer status (read-only)")

    args = parser.parse_args(argv)
    if args.version or args.cmd is None:
        print(f"lawkeeper {__version__}")
        return 0
    if args.cmd == "init":
        return cmd_init(args)
    if args.cmd == "status":
        return cmd_status(args)
    if args.cmd == "run":
        return cmd_run(args)
    if args.cmd == "reasoning":
        return cmd_reasoning(args)
    if args.cmd == "choose":
        return cmd_choose(args)
    parser.print_help()
    return 1


def cmd_run(args: argparse.Namespace) -> int:
    """Run the constitution laws against the current repo."""
    from guardrail.core.reasoning import is_enabled as reasoning_enabled
    from guardrail.core.runner import GuardrailRunner

    root = _repo_root()
    runner = GuardrailRunner(root)
    report = runner.run(only=set(args.law) if args.law else None)

    show_reasoning = reasoning_enabled(runner.config)
    if args.hide_reasoning:
        show_reasoning = False
    elif args.show_reasoning:
        show_reasoning = True

    if not args.quiet:
        if args.json:
            print(report.to_json())
        else:
            print(report.human_text(show_reasoning=show_reasoning))
    return report.exit_code


def cmd_reasoning(args: argparse.Namespace) -> int:
    """Record or report the state of internal-reasoning capture."""
    from guardrail.config import Config
    from guardrail.core.reasoning import emit, is_enabled

    root = _repo_root()
    config = Config.load(root)
    if not args.text:
        print(f"show_internal_reasoning: {is_enabled(config)}")
        print(f"reasoning_log: {config.reasoning_log}")
        return 0
    text = " ".join(args.text)
    log = emit(text, root, config)
    if log:
        print(f"reasoning recorded to {log}")
    else:
        print("reasoning hidden — set show_internal_reasoning=true in .guardrail.json to record")
    return 0


def cmd_choose(args: argparse.Namespace) -> int:
    """Run the checkbox-choice protocol against a spec file.

    Non-interactive (--select/--custom): validate the declared picks and emit
    JSON of the ChoiceResult. Interactive (no --select): present the menu on
    stdin/stdout. Exit code 1 signals a cancelled/invalid pick so callers can
    detect it.
    """
    import json
    from guardrail.choices import (Choice, ChoiceResult, ask, load_spec,
                                   resolve_token, spec_to_choices, validate)

    spec = load_spec(args.file)
    choices = spec_to_choices(spec)
    title = spec.get("title", "")
    body = spec.get("body", "")
    multi = spec.get("multi", not args.single)

    if args.select or args.custom is not None:
        selected = []
        for token in (args.select or []):
            cid = resolve_token(token, choices)
            if cid is None:
                print(f"unknown option: {token!r}", file=sys.stderr)
                return 2
            selected.append(cid)
        res = validate(choices, selected, args.custom)
    else:
        res = ask(title, body, choices, input_lines=None, multi=multi)

    print(json.dumps({"selected": res.selected, "custom": res.custom,
                      "cancelled": res.cancelled}))
    return 1 if res.cancelled else 0


if __name__ == "__main__":
    sys.exit(main())
