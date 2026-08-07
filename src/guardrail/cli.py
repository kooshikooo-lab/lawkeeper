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
import importlib
import shutil
import subprocess
import sys
from pathlib import Path

from guardrail import __version__

TEMPLATE_ROOT = Path(__file__).resolve().parent.parent.parent / "template"


def _repo_root(start: Path = Path.cwd()) -> Path:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=start, capture_output=True, text=True,
            encoding="utf-8", errors="replace"
        )
        return Path(out.stdout.strip()) or start
    except OSError:
        return start


def _render(src: Path, dst: Path, project_name: str) -> None:
    text = src.read_text(encoding="utf-8", errors="replace")
    rendered = (text
                .replace("__PROJECT_NAME__", project_name)
                .replace("__PROJECT_NAME_TITLE__", project_name.replace("-", " ").title()))
    dst.write_text(rendered, encoding="utf-8", newline="\n")


def cmd_init(args: argparse.Namespace) -> int:
    target = Path(args.dir or ".").resolve()
    root = target if (target / ".git").exists() else None
    if root is None:
        # walk up for a git repo; else treat target as new
        walk = target
        while walk != walk.parent and not (walk / ".git").exists():
            walk = walk.parent
        root = walk
    if (root / ".guardrail.json").exists():
        print(f"lawkeeper: {root} already has a .guardrail.json — refusing to overwrite.")
        return 1
    if (root / "docs/AI_CONSTITUTION.md").exists():
        print(f"lawkeeper: {root} already looks governed (has docs/AI_CONSTITUTION.md). "
              f"Re-run with --force only if you intend to replace it.")
        return 1

    project_name = args.name or root.name
    dst_root = root

    # Copy template tree (rendering placeholders).
    for rel in TEMPLATE_ROOT.rglob("*"):
        if rel.is_dir():
            continue
        rel_target = rel.relative_to(TEMPLATE_ROOT)
        dst = dst_root / rel_target
        dst.parent.mkdir(parents=True, exist_ok=True)
        if rel.suffix in (".tmpl",):
            dst_final = dst.with_suffix(rel.suffix.replace(".tmpl", ""))
        else:
            dst_final = dst
        _render(rel, dst_final, project_name)

    # Write project config.
    import json
    config = {
        "project_name": project_name,
        "machines": args.machines.split(",") if args.machines else ["desktop", "laptop"],
        "canonical_branches": ["main"],
    }
    (dst_root / ".guardrail.json").write_text(json.dumps(config, indent=2), encoding="utf-8")

    print(f"lawkeeper: scaffolding written to {dst_root}")
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
