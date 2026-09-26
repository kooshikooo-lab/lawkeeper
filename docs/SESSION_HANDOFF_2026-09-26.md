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
- `main` is at `f266dfd`, has no open PRs, and everything from this
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

## Where lawkeeper lives now, and the C: drive cleanup

**Working copy: `E:\lawkeeper`** (a fresh clone from GitHub, at `main`
`f266dfd`, next to `E:\falcun` and `E:\Windwright`). Work from there
from now on. It has the git hooks installed and the local-only files
restored; its system audit passes and all 348 tests pass. (An earlier
version of this section said no repo copy was needed on E:; that was
not practical once C: is being cleared, and the clone above fixes it.)

- Nothing here deletes anything for you. Deleting lawkeeper's old copy
  on C: (`C:\Users\Admin\Desktop\lawkeeper`) is yours (or the
  coordinator's) to do. Verified on 2026-09-26 before that: local `main`
  equals `origin/main`, no stashes, no open PRs, and every commit that
  matters is on GitHub.
- Backup folder `E:\lawkeeper-C-backup-2026-09-14\`:
  - `consensus/` and three files from `scripts/` (`.blockers.json`,
    `.team_state.json`, `compliance_log.jsonl`) — the local-only files Git
    doesn't track. Checked identical to the C: originals, and already
    restored into `E:\lawkeeper`.
  - `claude-memory/` (added 2026-09-26) — a copy of Claude's five memory
    notes, checked identical to the originals.
- **Claude's memory notes are the one thing not migrated.** Claude
  Code stores them per working folder, under
  `C:\Users\Admin\.claude\projects\<folder-name>\memory\`, so a session
  opened from `E:\lawkeeper` starts with an empty memory. The copy in
  `claude-memory/` above is the safety net. To make them active for the
  E: copy they must be placed in the matching folder for
  `E:\lawkeeper`, which only exists after the first session is opened
  there. Not done yet for that reason.
- Small leftovers on the old C: copy, all harmless:
  - Empty folders `.claude/worktrees/handoff-update` and
    `.claude/worktrees/handoff-0926` that Windows refused to remove
    ("permission denied"). Git no longer tracks them.
  - Local branches `agent/pretooluse-gate/desktop` (identical in content
    to `main`; git can't tell because the PR was squashed),
    `agent/guardrail-fit-investigation-update/desktop` and
    `opencode/framework-mvp/desktop` (on GitHub already). Ten commits
    exist only on local branches, all verified as present on `main` in
    content. None of this matters once C: is cleared; the E: clone has
    none of it.
- Old zips `lawkeeper-main.zip`, `lawkeeper-main (1).zip`,
  `lawkeeper-fixed.zip` in `E:\downloads`, and a stray `E:\Admin\Lawkeeper`
  (only `.claude` and `delivery`, not a Git repo) are older and not the
  source of truth. Ignore or delete them; not checked in detail.

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
