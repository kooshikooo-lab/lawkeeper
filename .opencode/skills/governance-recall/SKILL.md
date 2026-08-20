---
name: governance-recall
description: Forces agents to re-read the governance docs (AI_CONSTITUTION.md laws, COMPLIANCE_CHECK.md, AGENTS.md, AI_FAILURE_PATTERNS.md) at defined cadence so they never operate from stale memory. Use BEFORE every commit, at session start, and at every context-compaction event.
---

# Governance Recall (anti-forgetting cadence)

Ported from Windwright's `governance-recall` skill (2026-08-20) — found,
during a live conversation, to have been built once, worked (presumably)
in Windwright, and never propagated anywhere else, including this repo,
the one place a stale-constitution failure was actually caught live that
same night (Law 22, `docs/AI_FAILURE_PATTERNS.md`).

Agents forget the constitution under context pressure. This skill
hardcodes WHEN to re-read the authoritative governance files so recall
never depends on the agent "remembering to remember." Honest limitation,
carried over from the original and still true here: this is a written
cadence instruction, not a mechanical timer — it depends on being
followed, the same enforcement class as the constitution itself, not a
code-level gate. A real scheduled trigger (rather than an agent's own
judgment about when 15 minutes have passed) is a separate, larger piece
of work, not done here.

## The files (authoritative, in priority order — lawkeeper's real layout,
not copied from Windwright's)

| File | Why it matters |
|---|---|
| `docs/AI_CONSTITUTION.md` | The laws. Re-read before every commit (Law 14) and state which laws apply. |
| `docs/COMPLIANCE_CHECK.md` | The compliance checklist. |
| `AGENTS.md` | Working agreement, re-read on context compaction. |
| `docs/AI_FAILURE_PATTERNS.md` | Real, logged failures — read before repeating one. |
| `docs/ARCHITECTURE_DECISIONS.md` | ADRs — what's adopted vs. still planned. |
| `BLOCKERS.md` | Real, currently-open prerequisite gaps — don't re-discover a known blocker. |

Lawkeeper does not have Windwright's `CONSTRAINTS_AND_PREFERENCES.md`,
`REMINDERS.md`, or `docs/session-logs/BOOT_STATE.md` — don't reference
files that don't exist here; if this repo grows equivalents later, add
them to this table, don't assume Windwright's list applies unchanged.

## Cadence (MANDATORY triggers)

1. **Session start** — read `docs/AI_CONSTITUTION.md`, `AGENTS.md`,
   `docs/AI_FAILURE_PATTERNS.md` before doing anything else.
2. **Context compaction / mid-session loss** — STOP, re-read
   `AGENTS.md` and the constitution, then continue the interrupted task.
   Do not start new work from a paraphrased memory of what the rules say.
3. **BEFORE EVERY COMMIT** (Law 14) — re-read `docs/AI_CONSTITUTION.md`
   from the file, quote the laws that apply to this change, run the
   affected tests, review `git diff --cached` line by line.
4. **Whenever touching a protected file** — a change to
   `docs/AI_CONSTITUTION.md`, `docs/REMINDERS.md`, or another file
   `validate_commit_msg.py` protects requires `GOVERNANCE-UPDATE` in the
   commit message or the hook blocks it.
5. **Whenever a response is about to end on a stated future action** —
   Law 22's own amendment (2026-08-20): if the next step is technical,
   take it in this turn; don't narrate an intention and stop.

## What to do when you realize you don't remember

Never reconstruct from memory. Open the file and read it.
