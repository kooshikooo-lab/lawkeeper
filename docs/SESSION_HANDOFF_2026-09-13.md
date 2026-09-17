# Session Handoff — 2026-09-13, unfinished tasks and priorities

Written at the user's explicit request to close out a long session with a
real priority list for next time — not a status recap. Read this in full
before starting new work; it replaces any shorter chat-pasted version of
this handoff.

## What this session actually did, briefly (context for the list below)

Started as "look at Omnigent and think about learning from it," escalated
through a real self-audit (found only 3 of 24 guard scripts were
mechanically wired to git hooks; found the CI backstop had been silently
broken for most of the project's history), a multi-round prior-art survey
(Claude Code's own `PreToolUse` hooks, Omnigent, deepseek-harness,
hermes-agent, goose — five independently-built systems converging on the
same deny>ask>allow precedence), and landed a real, tested, twice-reviewed
feature (`scripts/gate_pretooluse.py`, PR #19). Along the way: added a
cross-repo "Standing Philosophy — Maximum Flexibility" section to the
constitution, set up lawkeeper's own weekly scheduled research routine,
and — the biggest open thread — the user pushed back on every piece of
AEF research quietly assuming lawkeeper's own codebase as the permanent
base, which escalated into a real, unresolved "should AEF be the base
instead" question with real setup (a pinned sibling clone) done but the
actual evaluation not started.

Full detail for anything summarized here lives in
`docs/RESEARCH_agent_harness_landscape.md` and
`docs/RESEARCH_harness_governance_survey.md` — read those, not just this
doc, before touching anything below. A third doc,
`docs/RESEARCH_harness_hook_mechanisms_survey.md`, is real and already
written but not yet on `main` — it's bundled into PR #19's first commit
(`d63d746`) rather than landed independently, so it won't exist on this
branch until Priority 1 item 1 (merging PR #19) actually happens; check
that PR's branch directly if you need it before then. (Caught by GitHub
Copilot's review of PR #21 — the reference was broken on `main` at the
time this doc itself was written.)

## Priority 1 — ready to finish now, concrete and bounded

1. **Merge PR #19** (`scripts/gate_pretooluse.py`, the live `PreToolUse`
   gate on force-push/delete of canonical branches). Real work, not a
   stub: 313+ tests, two real Copilot review rounds already addressed
   (refspec parsing, a remote-only-push regression, `--all`/`--mirror`),
   plus the AEF scope-boundary characterization methodology ported on
   top. What's left: `mergeStateStatus` was `BEHIND` as of this session's
   end (main moved since the last push) — rebase, request one more fresh
   Copilot review to cover everything since 2026-09-06 (the AEF work was
   never re-reviewed), confirm clean, merge. This is the single
   highest-value, lowest-effort thing to close out next session.

2. **Check the first automated research-routine run.** Lawkeeper's new
   weekly routine (`trig_01UgJi3thYGyEYQaHFif3CY1`, via `RemoteTrigger`)
   fires for the first time 2026-09-14T09:01 UTC — check whether it
   produced a real `docs/RESEARCH_EXTERNAL_SCAN_*.md` PR with real,
   verified findings (it was told to prioritize the queue in item 4
   below), or whether it needs tuning. Windwright's and Falcun's own
   routines are running on the same pattern, staggered by an hour each.

## Priority 2 — the big open question, set up, not started

3. **The AEF-as-base evaluation.** AEF (Apache-2.0) is cloned as its own
   sibling repo at `G:\repos\agentic-engineering-framework`, pinned to
   commit `35aaaaedc1c32269079b32de14aa31a7bebe2a54` — deliberately *not*
   a lawkeeper branch, deliberately read-only against lawkeeper's real
   files (see the doc entry for the full reasoning, agreed with Falcun).
   The actual task, not done yet: take lawkeeper's real theory-card
   system (`test_governance/cards/*.yaml`), the 23 laws
   (`docs/AI_CONSTITUTION.md`), and `scripts/governed_test.py`, and
   attempt to genuinely re-express them as an AEF task-gate/policy layer
   — then give an honest account of what's preserved, lost, or gained.
   This is the single most consequential open question from tonight; the
   user explicitly wants it done, explicitly didn't want it started
   tonight. Recommended: give this real, uninterrupted time next
   session rather than splitting attention across the smaller items
   below.

## Priority 3 — queued research (may be partially covered by item 2 above)

From `docs/RESEARCH_agent_harness_landscape.md`'s own open-follow-ups
list, none yet read directly:

4. **pre-commit's own extension model** — how lawkeeper's guard scripts
   could be packaged/versioned instead of manually copied across
   Windwright/falcun/orbital-study. Queued since the very first research
   pass this session, never picked up.
5. The **Open Plugins hooks specification** (open-plugins.com) — goose
   implements it; the spec itself has never been read directly.
6. **Codex's native hook protocol**, read directly — currently only
   known secondhand via dsh's own bridge-implementation comments.
7. **MITRE ATLAS's actual technique matrix** — every fetch attempt so
   far has 404'd or returned an empty shell; needs a different fetch
   strategy.
8. **AWS Cedar's own policy reference** — fetch attempts hit TLS errors;
   only a secondary AWS blog post has actually been read.
9. Omnigent's `schema.py` condition/label-gate matching and
   `risk_score.py`/`routing.py` builtins — flagged unread since the very
   first Omnigent research pass.

Note: the new weekly research routine (Priority 1, item 2) was
explicitly instructed to close these out first before finding new
candidates — check its output before manually chasing these by hand.

## Priority 4 — explicitly deferred, real but not urgent

10. **Scheduling-platform migration**: lawkeeper's (and Windwright's,
    Falcun's) research routines currently run on claude.ai's own cloud
    `RemoteTrigger` infrastructure — itself "an external platform for
    research scheduling," in real tension with a stated user principle
    from `RESEARCH_SCHEDULING_INDEPENDENCE_2026-09-09.md` (Falcun repo).
    A real, ready alternative exists on this machine (Hermes's MIT
    cron subsystem, fully tested, no claude.ai dependency). Explicitly
    confirmed by the user: wanted eventually, not high priority right
    now. Re-check when it becomes an actual priority, not on a schedule.
11. **AEF's remaining individual pieces** (single-use command-hash
    approval flow, the Watchtower approval queue/CLI, process-ancestry
    origin tracking) — not decided against, just queued. Their value is
    now contingent on Priority 2's outcome: if AEF becomes the base,
    these arrive for free as part of it; if not, they're still viable
    incremental additions to `gate_pretooluse.py` on their own.

## Priority 5 — blocked on a bigger decision, not actionable alone

12. **The shared canonical research registry proposal** (Falcun's
    `sources.json`/`canon.json` as a cross-repo store other repos read
    from) — raised weeks ago, explicitly still undecided, needs the
    user's own call before any repo builds toward it.
13. **Lawkeeper's own domain-boundary scope-check** (an equivalent to
    Falcun's `agent/scope.py`) — deliberately not built yet because
    lawkeeper has no structured catalog for it to protect (Law 21: no
    consumer, no capability). Blocked on item 12 being decided one way
    or the other, or on lawkeeper independently adopting its own
    structured catalog some other way.

## Already fully resolved this session — no action needed

- "Standing Philosophy — Maximum Flexibility" added to
  `docs/AI_CONSTITUTION.md` (commit `72e29c1`), synced to the
  `lawkeeper init` template.
- deepseek-harness (dsh) viability assessment: complete, verdict
  delivered (adopt-selectively — use as an optional external subprocess
  for a richer proposer step) — this is Falcun's decision to act on, not
  lawkeeper's.
- The refined neurosymbolic-AI/AlphaGeometry-for-acoustics framing: this
  is Windwright's domain, already relayed there, not lawkeeper's to
  carry forward.
- Windwright's old C:\ path: confirmed nothing in lawkeeper depends on
  it; cleared for Windwright's own cleanup pass.
- Lawkeeper's own C:\ footprint: checked, negligible (8.8MB) — no
  disk-space reason to move it, unlike the two harness research clones
  already relocated to `G:\repos\` earlier this session.
- All three repos (lawkeeper, Windwright, Falcun) now have independent,
  staggered weekly research routines — no duplication, confirmed via
  direct API checks, not assumed.
