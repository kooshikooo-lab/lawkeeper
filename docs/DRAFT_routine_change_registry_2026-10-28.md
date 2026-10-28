# Lawkeeper weekly research routine files findings into the shared registry (2026-10-28)

Status: **APPLIED 2026-10-28 with the user's approval (all three edits).** The text below is the draft as proposed. The registry paragraph in the applied prompt follows falcun's `docs/research/REGISTRY_FILING_GUIDE.md` wording plus the guardrails listed in edit 2. Applied via the routines API (trigger `trig_01UgJi3thYGyEYQaHFif3CY1`); read back and confirmed. First run with it: Thursday 2026-10-29 09:32 UTC (the "2026-11-05" below is wrong). Original status line: DRAFT, nothing applied. This is the
"separate yes/no" that falcun's registry proposal (falcun PR #8, merged
2026-10-21) leaves to the user, and condition (c) for closing lawkeeper handoff
item 13. Conditions (a) and (b) are in falcun `main` (commit 8944704: lawkeeper's
domains in `agent/scope.py`, `check_scope()` on every registry write).

## What the routine is today
Routine `trig_01UgJi3thYGyEYQaHFif3CY1`, "Lawkeeper weekly harness/governance
research", Thursdays 09:30 UTC, model claude-sonnet-5. One repository source
(`kooshikooo-lab/lawkeeper`), tools Bash/Read/Write/Edit/Glob/Grep/WebSearch/WebFetch.
It writes `docs/RESEARCH_EXTERNAL_SCAN_<date>.md`, commits it on
`agent/external-research-scan-<date>/cloud` and opens a PR against `main`.

## What would change (three edits)

1. **Repository sources: add `https://github.com/kooshikooo-lab/falcun`** as a second
   source, so the run can read `research/sources.json` / `research/canon.json`
   and open a PR in falcun. This is the access change you approve.
2. **Prompt: add one paragraph** after the "Write your findings" paragraph:

   > After writing the research doc, also file each finding you verified from a
   > primary source in the shared research registry in the falcun repo
   > (`research/sources.json` for sources, `research/canon.json` for claims),
   > using falcun's `propose_source()` / `propose_claim()` so entries start
   > PROPOSED. Set `filed_by` to `lawkeeper/weekly-routine`, `repos` to
   > `["lawkeeper"]`, and only a domain from lawkeeper's registered list
   > (agent-governance, pretooluse, policy-decision, git-hook, test-governance);
   > run falcun's `check_scope()` first and skip anything it routes to another
   > repo. Never confirm a source or claim yourself, never set a `grade`, and
   > never file a finding you labelled SECONDHAND. Commit on a branch
   > `agent/lawkeeper-registry-<date>/cloud` in the falcun repo and open a PR
   > there; never push to falcun `main`. If falcun is unreachable or its check
   > fails, say so in the lawkeeper doc and finish normally.

3. **Prompt: refresh the stale queue paragraph.** It still tells the run to
   "prioritize closing" pre-commit, MITRE ATLAS and AWS Cedar, which the
   2026-10-01 scan closed, and Codex, which the 2026-10-08 scan closed. Replace it
   with: Open Plugins is the only item still blocked (re-attempt, do not pad);
   otherwise follow the previous scan's "Re-check when" list. This is unrelated
   to the registry but is the same prompt and is plainly out of date.

## What stays the same
- Still PR-only; nothing is pushed to any `main`.
- Registry entries are PROPOSED. Confirming a source stays with falcun's rules
  (an automated existence check may confirm a source; claims need a human).
- No grading by the routine (automated grading was closed after all three
  candidates failed the pre-registered test).
- The lawkeeper research doc and PR are produced exactly as now.

## Risks and how they are limited
| Risk | Limit |
|---|---|
| Routine opens junk PRs in falcun | PR-only, PROPOSED entries, `check_scope` on write; falcun session reviews. Easy to pause. |
| Cloud token cannot push to falcun | Unknown until the first run; the prompt says to finish normally and report it. Falcun's own `cloud` machine name is already valid (falcun PR #10). |
| Wrong repo for a finding | `check_scope()` routes by domain; the routine skips what it routes elsewhere. |
| More usage per week | One extra repo clone and a few JSON entries; small next to the research itself. |

## Rollback
Remove the falcun source and the added paragraph (the previous prompt is kept in
`docs/RESEARCH_EXTERNAL_SCAN_2026-10-01.md`'s era and in this file's "today"
section); no other state changes.

## Decision
- **Recommended: approve after reading edit 2 once**, apply all three edits, and
  review the first falcun PR the routine opens (2026-11-05 run).
- Alternatives: approve edit 3 only (prompt cleanup, no new access), or defer
  until the registry pilot has more than the 26 canon claims graded.

I apply nothing until you say so; the exact update goes through the
RemoteTrigger `update` action on `trig_01UgJi3thYGyEYQaHFif3CY1`.
