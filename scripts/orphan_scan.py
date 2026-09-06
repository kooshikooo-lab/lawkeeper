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

For every .py file under scripts/, tools/, and any auto-discovered
src/*/ package (a directory containing __init__.py), counts real
references to its module basename anywhere else in the repo's
.py/.md/.yml/.yaml files, plus real git commit-history stats. A file
with 0 real *production* cross-references (see production_refs below)
AND that doesn't match a known one-off-task-script naming pattern
(export_*, refine_*, generate_*, validate_*_baseline, etc. -- these are
meant to be run manually, "unreferenced" is their normal, correct
state, not a sign of neglect) is flagged as a real orphan candidate.

Two counts are tracked per candidate, not one:
- external_refs: total mentions anywhere else in the repo (.py/.md/
  .yml/.yaml), minus the file's own self-mentions. The original,
  looser count -- kept for display, no longer what flagging uses alone.
- production_refs: the same count restricted to a "production"
  haystack that excludes .md files and test-shaped .py files (under a
  tests/ or test_governance/ directory, or named test_*.py/*_test.py/
  conftest.py). Flagging uses this stricter number.
  Real gap found 2026-09-05, cross-repo: Falcun ported this scanner and
  found that a module referenced only by its own test file plus one doc
  mention (agent/zotero_bridge.py: 8 external_refs, 0 real production
  callers) read as "referenced" under the single-count version, hiding
  a genuine orphan. production_refs makes "only my own test/docs
  mention me" visible instead of silently passing as a real reference.

Package-dir scanning was also added 2026-09-05 (same cross-repo report:
the original scripts/tools-only scope meant a module built, tested, and
never wired into any real code path anywhere in a src/ package would
never even become a candidate, let alone get flagged). Package dirs are
auto-discovered (any src/*/__init__.py), not hardcoded to this repo's
own package name, so a package rename doesn't silently stop the scan
from covering it.

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
- A module discovered dynamically at runtime (never imported by literal
  name anywhere in source) will also false-positive -- confirmed live
  in this repo: src/guardrail/core/registry.py's load_law_classes()
  discovers guardrail.laws.* modules via pkgutil.iter_modules, so every
  real, wired-in law module shows 0 production_refs. Deliberately not
  special-cased away (that would hide a real category a human should
  see and confirm, the same stance already taken on the two blind spots
  above) -- check the registry/loader before concluding a flagged law
  module is genuinely unused.
- Scaffolding trees copied wholesale by path (src/guardrail/template/,
  template_extras/ -- read via Path.rglob and copied file-by-file,
  never referenced by individual basename anywhere) are excluded from
  candidate collection entirely rather than left to false-positive on
  every single file -- these aren't modules in the sense this scanner
  is checking, they're scaffolding assets.

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
        # Added 2026-08-21 after actually reading all 11 remaining
        # Windwright candidates from the round-up: 10 of them were real,
        # legitimate one-off diagnostic/manual-run utilities that just
        # didn't match the patterns above -- confirmed by reading each
        # one's real content, not assumed from the name alone. Broadened
        # here so future scans don't re-flag the same real non-issues.
        r"^debug_", r"^verify_", r"^view_", r"^propose_", r"^_run_",
        r"^blender_render_", r"^validate_chromatic_",
        r"^phase\d+_export",
    ]
]


def is_one_off_task_script(basename: str) -> bool:
    return any(p.match(basename) for p in ONE_OFF_TASK_PATTERNS)


# Directories, wherever they occur under a candidate dir, whose .py
# files are scaffolding assets copied wholesale by path (see module
# docstring) rather than modules referenced by individual basename --
# would otherwise all false-positive as orphans.
_SCAFFOLDING_DIR_NAMES = {"template", "template_extras"}


def _discover_package_dirs(repo_root: Path) -> list[str]:
    """Auto-discover Python packages under src/ (any dir with __init__.py).

    Generalizes the scripts/tools-only scan to cover real production
    packages without hardcoding this repo's own package name -- a
    rename or a second package under src/ is picked up automatically.
    """
    src = repo_root / "src"
    if not src.is_dir():
        return []
    return sorted(
        str(p.parent.relative_to(repo_root)).replace("\\", "/")
        for p in src.glob("*/__init__.py")
    )


def _is_scaffolding_path(rel_to_candidate_dir: tuple[str, ...]) -> bool:
    return any(part in _SCAFFOLDING_DIR_NAMES for part in rel_to_candidate_dir[:-1])


def _is_test_shaped(rel_parts: tuple[str, ...], stem: str) -> bool:
    """True for a test file or a path under a test directory.

    Used to build the stricter "production" haystack (see module
    docstring) -- a module mentioned only inside its own tests/docs
    must not read as a real reference.
    """
    if any(part in ("tests", "test_governance") for part in rel_parts[:-1]):
        return True
    return stem.startswith("test_") or stem.endswith("_test") or stem == "conftest"


def _collect_candidates(repo_root: Path) -> list[Path]:
    candidates: list[Path] = []
    for pattern_dir in ("scripts", "tools", *_discover_package_dirs(repo_root)):
        d = repo_root / pattern_dir
        if not d.is_dir():
            continue
        for f in d.rglob("*.py"):
            rel_to_d = f.relative_to(d).parts
            if "__pycache__" in rel_to_d or _is_scaffolding_path(rel_to_d):
                continue
            candidates.append(f)
    return candidates


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
    candidates = _collect_candidates(repo_root)

    if not candidates:
        return []

    # One real pass: read every real text file in the repo once, build
    # a single combined haystack per extension group, then check each
    # candidate's basename against it -- O(repo size) total, not
    # O(candidates * repo size). A second, stricter haystack
    # (production_parts) excludes .md files and test-shaped .py files,
    # so a module mentioned only by its own tests/docs doesn't read as
    # a real reference (see module docstring, production_refs).
    text_exts = {".py", ".md", ".yml", ".yaml"}
    haystack_parts = []
    production_parts = []
    for f in repo_root.rglob("*"):
        if not (f.is_file() and f.suffix in text_exts and "__pycache__" not in f.parts):
            continue
        # Real bug found 2026-09-05, re-running this scan against Windwright:
        # only ".git" was excluded by name, but a stale git worktree checkout
        # sitting on disk under the repo root (.claude/worktrees/<name>/,
        # 1129 files, untracked -- confirmed via `git ls-files`) got scanned
        # like real project content. It contained its own copies of
        # scripts/quality_gate.py and scripts/quality_gate_local.py, so
        # every basename match inside that stale copy inflated the
        # "external reference" count for the real script of the same name --
        # exactly the false-negative-protection failure mode already
        # documented in this file's own module docstring (limitation 1),
        # just from local disk clutter rather than a same-named different
        # script. Fixed generally (skip any dot-prefixed directory
        # component under repo_root: .git, .claude, .venv, .pytest_cache,
        # etc.), not just .claude specifically -- the next stale worktree
        # or cache directory shouldn't need its own special case.
        rel_parts = f.relative_to(repo_root).parts
        if any(part.startswith(".") for part in rel_parts[:-1]):
            continue
        try:
            text = f.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        haystack_parts.append(text)
        if f.suffix != ".md" and not (f.suffix == ".py" and _is_test_shaped(rel_parts, f.stem)):
            production_parts.append(text)
    haystack = "\n".join(haystack_parts)
    haystack_production = "\n".join(production_parts)

    results = []
    for f in sorted(candidates):
        basename = f.stem
        rel = str(f.relative_to(repo_root)).replace("\\", "/")
        rel_parts = f.relative_to(repo_root).parts
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

        # Same subtraction against the production haystack -- but only
        # if this candidate itself was test-shaped enough to have been
        # excluded from production_parts in the first place (a stray
        # scripts/test_*.py candidate never contributed there, so there
        # is nothing of its own to subtract back out).
        candidate_is_test_shaped = _is_test_shaped(rel_parts, basename)
        own_production_occurrences = 0 if candidate_is_test_shaped else own_occurrences
        production_occurrences = haystack_production.count(basename)
        production_refs = max(0, production_occurrences - own_production_occurrences)

        commits, recency = git_commit_info(repo_root, rel)
        results.append({
            "path": rel, "basename": basename, "external_refs": external_refs,
            "production_refs": production_refs,
            "commits": commits, "recency": recency,
            "is_one_off": is_one_off_task_script(basename),
        })
    return results


def main():
    repo_root = Path(sys.argv[1]).resolve()
    results = scan_repo(repo_root)
    print(f"=== {repo_root.name} ({len(results)} scripts scanned) ===")
    # Flagging uses production_refs (the stricter count) -- a module
    # mentioned only by its own test file or docs must not read as
    # referenced. external_refs is still shown alongside it: a result
    # with external_refs > 0 but production_refs == 0 is exactly the
    # "only my own tests/docs mention me" case this distinction exists
    # to surface, not hide.
    orphans = [r for r in results if r["production_refs"] == 0 and not r["is_one_off"]]
    print(f"Real orphan candidates (0 production refs, not a one-off task script): {len(orphans)}")
    for r in sorted(orphans, key=lambda x: x["path"]):
        note = " [test/docs-only mentions]" if r["external_refs"] > 0 else ""
        print(f"  {r['path']}  (external_refs={r['external_refs']}, {r['commits']} commits, "
              f"last touched {r['recency']}){note}")
    print()
    print(f"(one-off task scripts excluded from orphan flagging: {sum(1 for r in results if r['is_one_off'])})")


if __name__ == "__main__":
    main()
