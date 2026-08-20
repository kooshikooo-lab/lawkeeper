# Session status & consolidated to-do — 2026-08-20

Full cleanup pass, requested by the user: collect every loose thread from
this session, verify real state (not assumed — checked git log/team_chat
directly for each uncertain item), and restore order. Supersedes scattered
chat-thread status; this is the real, current picture.

**Uncommitted-work audit result: clean.** Checked lawkeeper, Windwright,
orbital-study, falcun, Windwright-research-Devin — nothing uncommitted
except deliberately-uncommitted raw research data (Devin's
`levin-sarkar-raw/`, honestly labeled, not code).

---

## Genuinely done tonight (verified, not just claimed)

- **Windwright**: architecture backbone audit (Laws 4/5 corrected, dead
  ADRs superseded), optimizer competition experiment, task #80 (all 5
  chat-log-mined timbre metrics — confirmed 5/5 via commit history),
  Assignment 3 steps 1-2 (Blender render stage + Tauri Analyze tab, build-
  verified by me directly), routine test/compliance sweeps.
- **lawkeeper**: Laws 21/22/23 added (23 mechanized, Layers 1+2 built and
  tested), governance parity check started (`team_chat.py`, `ai_review.py`
  ported and verified), 3 governance proposals resolved, SUBSYSTEM_TABLE
  fixed, `.gitignore`/tracked-`.pyc` hygiene fixed.
- **orbital-study**: canon lockdown (`NARRATIVE_PROMOTION_ENABLED` gate,
  `UNIVERSE_BIBLE.md` — the user's own dictated canon, "Vesper Spindle"
  removed), PROTOTYPE_PLAN.md Steps 1-5 done, quality gate + Law 23
  Layer 2 grounding.
- **Standing directive recorded**: only Claude works on lawkeeper for now
  (memory note saved, other agents notified).

## Real open items, prioritized

### High priority — real decisions or verification pending
1. **The orbital-study core scope question (biggest open item):** text-
   scene generator vs. an explorable game with a movable character and
   evolved environments/alien biology. Everything downstream (Steps 6-9,
   the installer, the dashboard) is built for the current text-scene
   format — genuinely blocked on this, not mine to decide (Law 22).
2. **Dashboard rate/kill click never re-verified in the browser** after I
   fixed the stale-server-process bug — I confirmed the API routes exist
   again, but got interrupted before actually clicking a star in the
   browser to confirm the fix works end-to-end. Real, small, open
   verification gap.
3. **Task #74 (sharp-bias intonation)**: laptop ran the comparison, real
   numbers came back (asymmetric_penalty wins clearly), but nothing ever
   actually adopted it as the production default — recommendation made,
   not acted on. Confirmed via commit search, not assumed.
4. **lawkeeper/main vs. laptop's executor-backend branch**: real,
   unresolved structural + file-level merge conflict (template location
   moved on main; validate_commit_msg.py/compliance_watchdog.py/
   pyproject.toml touched independently on multiple branches). Now solely
   Claude's to resolve, since lawkeeper is Claude-exclusive going forward.
   Not attempted yet beyond a safe rehearsal-and-abort.
5. **Law 23 Layer 3** (independent-audit surfacing tool) — designed,
   not built. Layers 1+2 are done.

### Medium priority — queued, real, not urgent
6. **Governance mechanism audit** (the controlled-experiment methodology
   for testing whether governance itself works) — fully scoped in
   `docs/RESEARCH_governance_mechanism_audit.md`, needs a real multi-hour
   window, not started.
7. **Governance parity check, remaining candidates**: `backup.py` (needs
   real adaptation, not a blind port — Intra-Chat coupling), `comms_relay.py`
   / the "Intra-Chat" system (real, matches the user's earlier "inter-chat
   tool" idea — worth a real look, not decided), `consensus_orchestrator.py`
   (846 lines, "multi-AI review tribunal" — flagged, not reviewed in
   depth), `tailscale_monitor.py` (downgraded already, probably stays
   optional-only).
8. **Devin's queue**: Assignment 1 (governance checker fixes) and
   Assignment 4 (Levin/Sarkar real-paper deep dive) — confirmed via commit
   log, genuinely not started yet. Assignment 2 (manufacturing fact-check)
   also untouched, lowest priority already.
9. **opencode-desktop on orbital-study**: idle since the Law 23 Layer 2
   commit — PROTOTYPE_PLAN.md Steps 6-9 (installer polish, real overnight
   run, repackage, report) all effectively paused behind item #1 above.

### Lower priority / background research, real but not urgent
10. Anthropic data-deletion request — drafted, explicitly deferred by the
    user to a later day, not sent.
11. ToS-analyzer browser extension idea — repo cloned for reference, not
    studied in depth.
12. Wiki system (task #44) and distributed-compute research (task #62) —
    in-progress from earlier in this session, untouched tonight.
13. Session-mining skill (task #93) — still just an idea.

## Per-repo real HEAD state (for quick orientation)

- **lawkeeper**: `opencode/framework-mvp/desktop` @ `8c2164b`. `main` has
  diverged (10 commits, real CI/template-restructuring work) — not yet
  reconciled with this branch.
- **Windwright**: `opencode/hole-probe-conical-commitmsg/desktop` ==
  `opencode/timbre-objectives/laptop` @ `021263b7` (merged clean earlier
  tonight).
- **orbital-study**: `main` @ `ff06a28`.
- **Windwright-research-Devin**: `master` @ `78fd934`, Devin itself hasn't
  committed since.

## Re-check when

Before starting any new major thread — read this file first rather than
re-deriving state from scrollback, per the same discipline Law 12 already
established for `FUTURE_DIRECTIONS.md`.
