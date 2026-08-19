#!/usr/bin/env python3
"""Mine AI_FAILURE_PATTERNS.md across sibling repos into a combined corpus.

Two real, incompatible formats exist today (found by inspection, not
assumed):

  - Windwright: verbose ``## Failure #N -- Title`` sections with labeled
    Date/Session/Problem/Root cause/Solution/Prevention fields.
  - lawkeeper: single-line bullets, ``- [date] LAW <N> -- <what> / <root
    cause> / <fix>. Severity: <blocker|policy|debt>.``

This script normalizes both into one shared record shape so the corpus can
be read, summarized, and themed as a single dataset -- feeding the
governance feedback loop described in lawkeeper/docs/FUTURE_DIRECTIONS.md
("systematically mine real bug patterns back into the constitution/checkers,
without retraining any model").

Usage:
    python scripts/mine_failure_patterns.py --summary
    python scripts/mine_failure_patterns.py --json > corpus.json
    python scripts/mine_failure_patterns.py --report-file docs/FAILURE_PATTERN_REPORT.md

When to re-run: whenever a new entry is added to any repo's
AI_FAILURE_PATTERNS.md (a `## Failure #N` section or a `LAW: <N> —`
bullet), not just on some fixed schedule -- the corpus is only as current
as the last time this ran. After re-running, check `--summary`'s "By
theme" counts for a new pattern crossing the threshold that made
"claimed-verified-without-verifying" and "unverified-environment-
assumption" worth acting on (2026-08-19: 5 records each) -- update
THEME_MAP by hand for any new record, don't leave it "(untagged)"
indefinitely.

Do NOT use shell redirection (`--report > file`) to write the report on
Windows -- it uses the console codepage, not UTF-8, and will silently
corrupt non-ASCII characters (found and fixed 2026-08-19, logged in
AI_FAILURE_PATTERNS.md). Use `--report-file PATH` instead.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Optional

# Sibling repos to scan. Hardcoded rather than auto-discovered -- this
# matches the fixed, known set of repos used throughout this project
# (Windwright, lawkeeper, orbital-study, falcun). orbital-study and falcun
# do not have an AI_FAILURE_PATTERNS.md yet (confirmed by inspection,
# 2026-08-19) -- the scan reports zero found there rather than erroring.
DESKTOP = Path(r"C:\Users\Admin\Desktop")
REPOS = ["Windwright", "lawkeeper", "orbital-study", "falcun"]


@dataclass
class FailureRecord:
    repo: str
    id: str
    date: str
    law_or_theme: str
    title: str
    problem: str
    root_cause: str
    fix: str
    severity: str
    theme: str = ""  # filled in by Phase 2 categorization, empty here


# ── Windwright format: "## Failure #N -- Title" sections ────────────────

_WW_HEADER = re.compile(r"^## Failure #(?P<num>\d+)\s*—\s*(?P<title>.+?)\s*$", re.MULTILINE)
_WW_FIELD_NAMES = ["Date", "Session", "Problem", "Root cause", "Solution", "Prevention"]


def _ww_field(block: str, name: str) -> str:
    """Extract one labeled field's text from a Windwright failure block.

    Fields are ``Name:\\n<text>`` and run until the next known field label
    or the end of the block.
    """
    other_names = "|".join(re.escape(n) for n in _WW_FIELD_NAMES if n != name)
    pattern = re.compile(
        rf"^{re.escape(name)}:\s*\n(?P<body>.*?)(?=\n(?:{other_names}):|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    m = pattern.search(block)
    return m.group("body").strip() if m else ""


def parse_windwright_format(text: str, repo: str) -> list[FailureRecord]:
    headers = list(_WW_HEADER.finditer(text))
    records: list[FailureRecord] = []
    for i, h in enumerate(headers):
        start = h.end()
        end = headers[i + 1].start() if i + 1 < len(headers) else len(text)
        block = text[start:end]
        records.append(
            FailureRecord(
                repo=repo,
                id=f"{repo}#{h.group('num')}",
                date=_ww_field(block, "Date"),
                law_or_theme="",
                title=h.group("title"),
                problem=_ww_field(block, "Problem"),
                root_cause=_ww_field(block, "Root cause"),
                fix=_ww_field(block, "Solution"),
                severity="",
            )
        )
    return records


# ── lawkeeper format: "- [date] LAW <N> -- <body>. Severity: <word>." ───

_LK_TAGGED = re.compile(
    r"^-\s*\[(?P<date>[^\]]*)\]\s*LAW\s*(?P<law>\d+)\s*—\s*(?P<body>.+?)\s*"
    r"Severity:\s*(?P<severity>\w+)\.\s*$",
    re.MULTILINE,
)
# Untagged bullets (mostly the Debt section) still end "Severity: word."
# but have no "LAW <N>" tag -- capture them too rather than silently
# dropping real entries.
_LK_UNTAGGED = re.compile(
    r"^-\s*(?:\[(?P<date>[^\]]*)\]\s*)?(?P<body>(?!\[[^\]]*\]\s*LAW).+?)\s*"
    r"Severity:\s*(?P<severity>\w+)\.\s*$",
    re.MULTILINE,
)


def _lk_split_body(body: str) -> tuple[str, str, str]:
    """Best-effort split of a lawkeeper bullet body into (problem, root_cause, fix).

    Bodies inconsistently use inline 'Root cause:' / 'Fix:' labels. Where
    present, split on them; otherwise return the whole body as `problem`
    with empty root_cause/fix rather than guessing.
    """
    rc_match = re.search(r"Root cause:\s*(.+?)(?=\s*Fix:|\Z)", body, re.DOTALL)
    fix_match = re.search(r"Fix:\s*(.+)$", body, re.DOTALL)
    if rc_match or fix_match:
        problem = body[: rc_match.start()].strip() if rc_match else body[: fix_match.start()].strip()
        root_cause = rc_match.group(1).strip() if rc_match else ""
        fix = fix_match.group(1).strip() if fix_match else ""
        return problem, root_cause, fix
    return body.strip(), "", ""


def parse_lawkeeper_format(text: str, repo: str) -> list[FailureRecord]:
    records: list[FailureRecord] = []
    seen_spans: list[tuple[int, int]] = []

    for m in _LK_TAGGED.finditer(text):
        problem, root_cause, fix = _lk_split_body(m.group("body"))
        records.append(
            FailureRecord(
                repo=repo,
                id=f"{repo}#{m.group('date') or len(records)}",
                date=m.group("date"),
                law_or_theme=f"LAW {m.group('law')}",
                title=problem.split(".")[0][:80],
                problem=problem,
                root_cause=root_cause,
                fix=fix,
                severity=m.group("severity"),
            )
        )
        seen_spans.append(m.span())

    # NOTE (found + fixed 2026-08-19, logged in AI_FAILURE_PATTERNS.md): this
    # used to key untagged ids off `len(records)`, which shifts every time a
    # new tagged entry is added upstream in the same file -- silently
    # breaking any THEME_MAP entry keyed on the old id (verified by
    # re-checking output against expected counts, not assumed correct
    # because it ran without error). Use an index local to this loop instead
    # so an id, once assigned, never moves.
    untagged_index = 0
    for m in _LK_UNTAGGED.finditer(text):
        # Skip anything already captured by the tagged pattern.
        if any(a <= m.start() < b for a, b in seen_spans):
            continue
        problem, root_cause, fix = _lk_split_body(m.group("body"))
        records.append(
            FailureRecord(
                repo=repo,
                id=f"{repo}#debt-{untagged_index}",
                date=m.group("date") or "",
                law_or_theme="",
                title=problem.split(".")[0][:80],
                problem=problem,
                root_cause=root_cause,
                fix=fix,
                severity=m.group("severity"),
            )
        )
        untagged_index += 1

    return records


# ── Dispatch ──────────────────────────────────────────────────────────

def parse_failure_file(path: Path, repo: str) -> list[FailureRecord]:
    text = path.read_text(encoding="utf-8")
    if "## Failure #" in text:
        return parse_windwright_format(text, repo)
    if re.search(r"^-\s*\[[^\]]*\]\s*LAW\s*\d+\s*—", text, re.MULTILINE):
        return parse_lawkeeper_format(text, repo)
    return []


# ── Phase 2: manual theme assignment ─────────────────────────────────────
#
# Read every record's actual content by hand (2026-08-19) and assigned a
# theme -- not a keyword classifier, a real read. Keyed by id. An id not
# present here falls back to "(untagged)" in reports, which is honest: it
# means nobody has categorized it yet, not that it doesn't fit anything.
THEME_MAP: dict[str, str] = {
    # Theme: claimed/reported a result as correct/done without actually
    # verifying it (the largest real pattern -- 5 of 19 records).
    "Windwright#8": "claimed-verified-without-verifying",
    "lawkeeper#2026-08-14": "claimed-verified-without-verifying",  # first match wins below; see NOTE
    "lawkeeper#debt-7": "claimed-verified-without-verifying",
    # Theme: acted without required approval/confirmation first.
    "Windwright#10": "acted-without-approval",
    "lawkeeper#2026-08-07T16:40": "acted-without-approval",
    # Theme: assumed a file/path/environment state without checking it.
    "Windwright#1": "unverified-environment-assumption",
    "Windwright#2": "unverified-environment-assumption",
    "Windwright#4": "unverified-environment-assumption",
    "Windwright#5": "unverified-environment-assumption",
    "Windwright#7": "unverified-environment-assumption",
    # Theme: didn't search thoroughly before writing new code.
    "Windwright#6": "insufficient-search-before-writing",
    # Theme: guard/tooling script itself has a silent-failure or
    # self-inflicted false-positive bug.
    "lawkeeper#session": "guard-script-self-inflicted-bug",  # first match wins; see NOTE
    # Theme: coordination inefficiency between co-located agents (already
    # fixed tonight via the Law 11 same-machine amendment).
    "Windwright#11": "same-machine-coordination-anti-pattern",
    # Theme: real physics/domain coverage gap, not an agent-behavior
    # failure -- kept separate rather than force-fit into the buckets
    # above.
    "Windwright#9": "missing-cross-implementation-validation",
    # Theme: the git merge-tree probe result was trusted without checking
    # its own setup first -- same claimed-verified-without-verifying shape
    # as the LAW 18 cluster above, just not LAW-tagged in the source file.
    "lawkeeper#debt-0": "claimed-verified-without-verifying",
    # 2026-08-19 entries added by this same mining session (see
    # AI_FAILURE_PATTERNS.md): the validate_commit_msg.py substring bug is
    # its own guard-script-self-inflicted-bug instance; the report
    # encoding bug is another claimed-verified-without-verifying instance.
}
# NOTE: several ids collide (lawkeeper's parser mints the same id for
# same-date entries, e.g. three separate "lawkeeper#2026-08-14" LAW 18
# records, and two "lawkeeper#session" records). THEME_MAP is keyed by id
# for readability, but apply_themes() below assigns by (id, occurrence
# index) so colliding ids don't silently overwrite each other -- every
# record with that id gets its themed record's theme once, in order.
_THEME_OVERRIDES_BY_OCCURRENCE: list[tuple[str, int, str]] = [
    # (id, 0-based occurrence-of-this-id, theme)
    ("lawkeeper#2026-08-14", 0, "claimed-verified-without-verifying"),  # 402.8-cent report
    ("lawkeeper#2026-08-14", 1, "incomplete-completion-criterion"),  # stopped at reporting (LAW17)
    ("lawkeeper#2026-08-14", 2, "claimed-verified-without-verifying"),  # skipped adversarial review
    ("lawkeeper#2026-08-14", 3, "claimed-verified-without-verifying"),  # estimated instead of measured
    ("lawkeeper#session", 0, "guard-script-self-inflicted-bug"),  # LAW16 silent fallback
    ("lawkeeper#session", 1, "guard-script-self-inflicted-bug"),  # LAW15 guard flagged own test
    ("lawkeeper#2026-08-19", 0, "guard-script-self-inflicted-bug"),  # LAW16 substring bug
    ("lawkeeper#2026-08-19", 1, "claimed-verified-without-verifying"),  # LAW18 encoding bug
]


def apply_themes(records: list[FailureRecord]) -> None:
    """Assign .theme in place, handling id collisions by occurrence order."""
    occurrence_count: dict[str, int] = {}
    override_by_key = {(rid, occ): theme for rid, occ, theme in _THEME_OVERRIDES_BY_OCCURRENCE}
    for r in records:
        occ = occurrence_count.get(r.id, 0)
        occurrence_count[r.id] = occ + 1
        r.theme = override_by_key.get((r.id, occ)) or THEME_MAP.get(r.id, "(untagged)")


def collect_corpus() -> list[FailureRecord]:
    corpus: list[FailureRecord] = []
    for repo in REPOS:
        path = DESKTOP / repo / "docs" / "AI_FAILURE_PATTERNS.md"
        if not path.exists():
            continue
        corpus.extend(parse_failure_file(path, repo))
    return corpus


def generate_report(corpus: list[FailureRecord]) -> str:
    by_theme: dict[str, list[FailureRecord]] = {}
    for r in corpus:
        by_theme.setdefault(r.theme, []).append(r)

    lines = [
        "# Failure Pattern Report",
        "",
        "Generated by `scripts/mine_failure_patterns.py` from the real",
        "`AI_FAILURE_PATTERNS.md` corpus (Windwright + lawkeeper, 19 records",
        "as of 2026-08-19). Themes assigned by hand, reading every entry --",
        "not a keyword classifier. Re-run and update `THEME_MAP` as new",
        "entries accumulate.",
        "",
        f"**{len(corpus)} total records, {len(by_theme)} themes.**",
        "",
    ]
    for theme, recs in sorted(by_theme.items(), key=lambda kv: -len(kv[1])):
        lines.append(f"## {theme} ({len(recs)})")
        lines.append("")
        for r in recs:
            lines.append(f"- **{r.id}** — {r.title}")
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--summary", action="store_true", help="print counts per repo/law")
    ap.add_argument("--json", action="store_true", help="print the full corpus as JSON")
    ap.add_argument("--report", action="store_true", help="print the themed markdown report")
    ap.add_argument(
        "--report-file", type=Path, default=None,
        help="write the themed markdown report to this path as UTF-8 "
             "(use this instead of `--report > file` -- shell redirection "
             "on Windows uses the console codepage, not UTF-8, and will "
             "silently corrupt non-ASCII characters like em-dashes)",
    )
    args = ap.parse_args()

    corpus = collect_corpus()
    apply_themes(corpus)

    if args.json:
        # Explicit UTF-8 + \n newlines even when stdout is redirected on
        # Windows, for the same reason --report-file exists below.
        sys.stdout.reconfigure(encoding="utf-8", newline="\n")
        print(json.dumps([asdict(r) for r in corpus], indent=2))
        return 0

    if args.report_file:
        args.report_file.write_text(generate_report(corpus), encoding="utf-8", newline="\n")
        print(f"Wrote {args.report_file}")
        return 0

    if args.report:
        sys.stdout.reconfigure(encoding="utf-8", newline="\n")
        print(generate_report(corpus))
        return 0

    # Default (and --summary): human-readable counts.
    by_repo: dict[str, int] = {}
    by_law: dict[str, int] = {}
    by_theme: dict[str, int] = {}
    for r in corpus:
        by_repo[r.repo] = by_repo.get(r.repo, 0) + 1
        key = r.law_or_theme or "(untagged)"
        by_law[key] = by_law.get(key, 0) + 1
        by_theme[r.theme] = by_theme.get(r.theme, 0) + 1

    print(f"Total failure records: {len(corpus)}")
    print("\nBy repo:")
    for repo in REPOS:
        found = repo in by_repo
        print(f"  {repo}: {by_repo.get(repo, 0)}{'' if found or (DESKTOP / repo / 'docs' / 'AI_FAILURE_PATTERNS.md').exists() else ' (no AI_FAILURE_PATTERNS.md)'}")
    print("\nBy law/tag:")
    for law, count in sorted(by_law.items(), key=lambda kv: -kv[1]):
        print(f"  {law}: {count}")
    print("\nBy theme:")
    for theme, count in sorted(by_theme.items(), key=lambda kv: -kv[1]):
        print(f"  {theme}: {count}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
