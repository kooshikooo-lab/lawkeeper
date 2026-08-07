"""Merge preflight gate — predict merge conflicts WITHOUT touching the worktree.

Cross-machine merges are risky (they historically produced 19 conflicts). This
gate uses `git merge-tree --write-tree` to compute what a merge WOULD do and
report conflicts before any merge starts. It never modifies the index or
working tree, so it is safe to run anytime, including from CI and hooks.

Law 15.3 requires cross-machine merges to go through merge/<topic> staging and
be verified before promotion. This gate is the verification step: if it reports
conflicts, do NOT merge blindly — rehearse on a merge/<topic> branch instead.

Commands:
  merge_gate.py <base> <head>            predict merge(base, head); exit 1 if conflicts
  merge_gate.py <base> <head> --explain  print per-file conflict reasons
  merge_gate.py --examples               show usage examples

Exit codes: 0 = clean merge (no conflicts), 1 = conflicts predicted, 2 = error.

Requires git >= 2.38 (git merge-tree --write-tree).
"""

import argparse
import shutil
import subprocess
import sys


def git(args):
    try:
        result = subprocess.run(
            ["git"] + args, capture_output=True, text=True,
            encoding="utf-8", errors="replace"
        )
        return result.stdout, result.stderr, result.returncode
    except OSError:
        return "", "", 2


def resolve_ref(ref: str) -> str | None:
    out, _, code = git(["rev-parse", "--verify", f"{ref}^{{commit}}"])
    return out.strip() if code == 0 else None


def merge_tree(base: str, head: str):
    """Run git merge-tree --write-tree and parse output.

    Returns (tree_sha, conflicts, error_lines).
    Exit semantics of `git merge-tree --write-tree`:
      0  = clean merge (tree produced, no conflicts)
      1  = conflicts present (tree produced, conflict markers recorded)
      >=2 = fatal error (ref not found, bad repo, old git)
    """
    out, err, code = git(["merge-tree", "--write-tree", base, head])
    if code >= 2 or code < 0:
        return None, [], err.splitlines()
    lines = out.splitlines()
    tree_sha = lines[0].strip() if lines else ""
    conflicts = []
    for line in lines[1:]:
        if line.startswith("CONFLICT"):
            conflicts.append(line)
    return (tree_sha or None), conflicts, []


def main():
    parser = argparse.ArgumentParser(description="Merge conflict preflight gate")
    parser.add_argument("base", nargs="?", help="base ref (e.g. opencode/main/desktop)")
    parser.add_argument("head", nargs="?", help="head ref (e.g. opencode/build123d/laptop)")
    parser.add_argument("--explain", action="store_true",
                        help="print per-file conflict reasons")
    parser.add_argument("--examples", action="store_true", help="show usage")
    args = parser.parse_args()

    if args.examples:
        print(
            "Examples:\n"
            "  python scripts/merge_gate.py opencode/main/desktop opencode/build123d/laptop\n"
            "  python scripts/merge_gate.py origin/opencode/main/desktop 6c23a11 --explain\n"
            "  # exit 0 = clean merge, 1 = conflicts, 2 = error"
        )
        return 0

    if not args.base or not args.head:
        parser.print_help()
        return 2

    if shutil.which("git") is None:
        print("ERROR: git not found", file=sys.stderr)
        return 2

    base_sha = resolve_ref(args.base)
    head_sha = resolve_ref(args.head)
    if not base_sha or not head_sha:
        print(f"ERROR: ref not found (base={args.base!r}, head={args.head!r})",
              file=sys.stderr)
        return 2

    tree, conflicts, errs = merge_tree(base_sha, head_sha)
    if tree is None:
        print("ERROR: merge-tree failed:", file=sys.stderr)
        for e in errs:
            print("  " + e, file=sys.stderr)
        return 2

    if not conflicts:
        print(f"OK: merge({args.base}, {args.head}) is CLEAN — no conflicts predicted.")
        return 0

    print(f"BLOCKED: merge({args.base}, {args.head}) predicts {len(conflicts)} conflict(s):",
          file=sys.stderr)
    seen = set()
    for c in conflicts:
        if c in seen:
            continue
        seen.add(c)
        print("  " + c, file=sys.stderr)
    if args.explain:
        for c in conflicts:
            print("  " + c)
    print(
        "Do NOT merge blindly. Rehearse on a merge/<topic> staging branch "
        "(Law 15.3), resolve, verify, then promote.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
