# Session Handoff — 2026-09-26: archive of this session + "where things stand"

Written at the user's request to close and archive this session and to
remind them of the situation in plain language. Read the short section
first; everything below it is reference.

## The short version (read this first)

**What was the older handoff (`SESSION_HANDOFF_2026-09-13.md`)?**
Not a task for closing a session. It was the priority-ordered to-do list
written at the end of the previous long session, so the next session
would know what was left. Its item 1 ("merge PR #19") is now done. Its
other numbered items are still valid and still the
master list; this document does not replace it, it sits on top of it.

**What got done since then (2026-09-13 → 2026-09-26):**
- PR #19 merged: the live safety gate (`scripts/gate_pretooluse.py`)
  that stops an AI session from force-pushing over, or deleting, `main`
  or another protected branch. It is switched on for sessions in this
  repo through `.claude/settings.json`. Tested by hand: a force-push to
  `main` is refused.
- Its last-minute CI failure turned out to be a real, recurring bug in
  `scripts/toolcheck.py` (a hand-kept list of Python built-in modules
  that didn't include `shlex`). Fixed properly by using Python's own
  list, with tests, so it can't happen for the next new module either.
- PRs #21, #22, #23 merged: the pending docs (Standing Philosophy, AEF
  setup, the older handoff), the cosmic-ray note, and the handoff update.
- `main` is at `ace0979`, has no open PRs, and everything from this
  session is on GitHub.

**The one thing that is actually broken: the weekly research routine has
never produced a result.** It ran on Sept 14 and Sept 21 and both times
was refused within seconds with "You've hit your weekly limit"
(resets Sept 17 and Sept 24, both Thursdays 07:00 UTC). The routine's
own setup is fine (it clones the repo and starts normally). The problem
is that all three research routines (Windwright 07:00, Falcun 08:00,
lawkeeper 09:00 UTC, Mondays) share your one account limit, and by
Monday morning the limit is already used up. Windwright, running first,
got through both times; Falcun and lawkeeper were locked out both times.
This is a decision for you, see "Decisions waiting on you" below.

## About the C: drive cleanup and closing sessions

- Nothing here deletes anything for you. Deleting lawkeeper's old copy
  on C: is yours (or the coordinator's) to do.
- Everything that matters is on GitHub (`kooshikooo-lab/lawkeeper`,
  `main` at `ace0979`). The backup `E:\lawkeeper-C-backup-2026-09-14\`
  holds only the small local-only files (`consensus/`, `scripts/`), not
  the repo, because the repo itself is safely on GitHub.
- If lawkeeper is worked on from anywhere else after C: is cleared:
  clone fresh from GitHub, then follow `AGENTS.md` Step 0
  (`python scripts/install_hooks.py`, then `python scripts/system_audit.py`,
  which must PASS).
- Small leftovers on this machine, all harmless:
  - `.claude/worktrees/handoff-update` — an empty leftover folder Windows
    refused to remove ("permission denied"). Git no longer tracks it.
  - Local branches `agent/pretooluse-gate/desktop` (content is identical
    to what is on `main`, git just can't tell because the PR was
    squashed), `agent/guardrail-fit-investigation-update/desktop`,
    `opencode/framework-mvp/desktop` — check before deleting the last
    two; I did not verify them this round.
- Claude's own memory notes live under
  `C:\Users\Admin\.claude\projects\C--Users-Admin-Desktop-lawkeeper\memory\`,
  i.e. on C:. If C: is wiped, that folder is what would be lost.

## What is still open (unchanged from the 2026-09-13 handoff)

Go to `docs/SESSION_HANDOFF_2026-09-13.md` for the full text. Summary:
- **Priority 2, the big one:** the AEF-as-base evaluation (does the
  external "agentic engineering framework" fit better as lawkeeper's
  foundation than lawkeeper's own code?). Set up (clone pinned at
  `35aaaae…` on `G:\repos\agentic-engineering-framework`), deliberately
  not started, because you asked to start it later. Needs real
  uninterrupted time.
- **Priority 3:** the queued research reading list (pre-commit's
  extension model, Open Plugins hooks spec, Codex's hook protocol,
  MITRE ATLAS, AWS Cedar, Omnigent's rule matching). The weekly routine
  was meant to do these, and hasn't, so this list has not moved.
- **Priority 4/5:** moving the routines off claude.ai to a self-hosted
  scheduler (wanted eventually); AEF's smaller pieces; the shared
  cross-repo research registry; a lawkeeper domain-boundary check.

## Decisions waiting on you (nothing here is urgent)

1. **The research routine.** Options: (a) do nothing and hope the limit
   isn't used up by Monday; (b) move all three routines to a slot right
   after the Thursday 07:00 UTC reset, when the cap is fresh (my
   recommendation: cheapest, no code); (c) do less per run; (d) speed up
   the move to your own scheduler. Changing the schedule touches all
   three repos' routines, so it is your call, not something I did on my
   own.
2. **When to start the AEF evaluation** (Priority 2 above).
3. **Whether the shared research registry is wanted at all** (still
   undecided since it was proposed).

## Things to remember about how to work in this repo

- `main` is protected: no direct pushes, no merge commits, all changes go
  in through a PR whose CI (`guard` and `powershell-lint`) is green and
  whose review threads are resolved. You are not expected to review code:
  the assistant handles PR mechanics itself.
- Project wording (the constitution, research documents' conclusions) is
  yours to decide; technicalities (branches, file locations, tests) the
  assistant decides. Questions to you should be about things a non-coder
  can weigh in on.
- The "Standing Philosophy" section in `docs/AI_CONSTITUTION.md` is
  internal-only and must never ship in the product template.
- The safety gate blocks force-pushes and deletes of protected branches.
  If you ever genuinely need one, the override is an environment
  variable (`GUARD_BRANCH_ALLOW_FORCE` or `GUARD_BRANCH_ALLOW_DELETE`)
  set *before* the session starts; it cannot be granted from inside a
  session by design.
- Other Claude sessions on this machine share the same folders. Use a
  separate git worktree for any work that must not collide with them.
