#!/usr/bin/env python3
"""Orphan-script scanner: real, mechanical Law 21 ("a capability with
no consumer is a bug") detection, one pass over the whole repo, not N
separate greps per candidate file.

Built 2026-08-21 for a real, cross-repo round-up (docs/
SESSION_ROUNDUP_2026-08-21.md) -- an earlier shell-loop attempt did one
`grep -rl <basename>` per candidate file, which is O(candidates x repo
size) and timed out against a 132-script directory. This reads the
whole repo once, builds one haystack, then checks every candidate's
basename against it -- O(repo size) total, regardless of candidate
count.

For every .py file under scripts/ and tools/, counts real references to
its module basename anywhere else in the repo's .py/.md/.yml/.yaml
files, plus real git commit-history stats. A file with 0 real
cross-references AND that doesn't match a known one-off-task-script
naming pattern (export_*, refine_*, generate_*, validate_*_baseline,
etc. -- these are meant to be run manually, "unreferenced" is their
normal, correct state, not a sign of neglect) is flagged as a real
orphan candidate.

Real, known limitations, stated rather than hidden:
- A basename substring match can false-positive if one script's name is
  a substring mentioned in another file for an unrelated reason, or
  false-negative-protect a genuinely unused script that happens to
  share a common word with something else. Basename matching is a real
  heuristic, not a guarantee -- the round-up doc this tool produced
  data for treats every flagged result as a candidate to check, not a
  proven conclusion.
- A recently-built CLI entry point invoked directly by hand (not
  imported by other code) will correctly show 0 cross-references and
  get flagged even though it's actively used -- a real false positive
  class, not a bug in the logic; the round-up doc's own findings
  include a live example of this (render_literature_html.py).
- MCP-registered tools (referenced via a JSON/config file's tool
  registration, not a Python import) can also false-positive for the
  same reason -- worth checking the actual MCP config before concluding
  a flagged MCP-shaped tool is genuinely unused.

Usage: python orphan_scan.py <repo_root>
"""
import re
import subprocess
import sys
from pathlib import Path

ONE_OFF_TASK_PATTERNS = [
    re.compile(p, re.IGNORECASE) for p in [
        r"^export_", r"^refine_", r"^generate_", r"^validate_.*_baseline$",
        r"^promote_", r"^overnight_", r"^stability_check_", r"^smoke_test_",
        r"^diagnose_", r"^investigate_", r"^compare_", r"^bracket_check_",
        r"^experiment_", r"^benchmark_.*_dask$", r"^v2_validation_runner$",
        r"^test_",
    ]
]


def is_one_off_task_script(basename: str) -> bool:
    return any(p.match(basename) for p in ONE_OFF_TASK_PATTERNS)


def git_commit_info(repo_root: Path, rel_path: str) -> tuple[int, str]:
    try:
        log = subprocess.run(
            ["git", "log", "--oneline", "--", rel_path],
            cwd=repo_root, capture_output=True, text=True, encoding="utf-8", errors="replace",
        )
        count = len([l for l in log.stdout.splitlines() if l.strip()])
        recency = subprocess.run(
            ["git", "log", "-1", "--format=%ar", "--", rel_path],
            cwd=repo_root, capture_output=True, text=True, encoding="utf-8", errors="replace",
        )
        return count, recency.stdout.strip()
    except OSError:
        return 0, "unknown"


def scan_repo(repo_root: Path) -> list[dict]:
    candidates = []
    for pattern_dir in ("scripts", "tools"):
        d = repo_root / pattern_dir
        if d.is_dir():
            candidates.extend(d.glob("*.py"))

    if not candidates:
        return []

    # One real pass: read every real text file in the repo once, build
    # a single combined haystack per extension group, then check each
    # candidate's basename against it -- O(repo size) total, not
    # O(candidates * repo size).
    text_exts = {".py", ".md", ".yml", ".yaml"}
    haystack_parts = []
    for f in repo_root.rglob("*"):
        if f.is_file() and f.suffix in text_exts and "__pycache__" not in f.parts and ".git" not in f.parts:
            try:
                haystack_parts.append(f.read_text(encoding="utf-8", errors="ignore"))
            except OSError:
                pass
    haystack = "\n".join(haystack_parts)

    results = []
    for f in sorted(candidates):
        basename = f.stem
        rel = str(f.relative_to(repo_root)).replace("\\", "/")
        # Count occurrences of the basename, but subtract this file's
        # own occurrences of its own name (docstring self-reference,
        # the file itself contributing to the haystack) by re-reading
        # just this file separately.
        try:
            own_text = f.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            own_text = ""
        total_occurrences = haystack.count(basename)
        own_occurrences = own_text.count(basename)
        external_refs = max(0, total_occurrences - own_occurrences)

        commits, recency = git_commit_info(repo_root, rel)
        results.append({
            "path": rel, "basename": basename, "external_refs": external_refs,
            "commits": commits, "recency": recency,
            "is_one_off": is_one_off_task_script(basename),
        })
    return results


def main():
    repo_root = Path(sys.argv[1]).resolve()
    results = scan_repo(repo_root)
    print(f"=== {repo_root.name} ({len(results)} scripts scanned) ===")
    orphans = [r for r in results if r["external_refs"] == 0 and not r["is_one_off"]]
    print(f"Real orphan candidates (0 external refs, not a one-off task script): {len(orphans)}")
    for r in sorted(orphans, key=lambda x: x["path"]):
        print(f"  {r['path']}  ({r['commits']} commits, last touched {r['recency']})")
    print()
    one_offs_skipped = len(results) - len(orphans) - len([r for r in results if r["external_refs"] > 0])
    print(f"(one-off task scripts excluded from orphan flagging: {sum(1 for r in results if r['is_one_off'])})")


if __name__ == "__main__":
    main()
