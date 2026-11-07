# Session Handoff — 2026-11-07: gate hardened, registry filing live, hygiene tasks working

Covers 2026-10-10 → 2026-11-07. Sits on top of `SESSION_HANDOFF_2026-10-07.md`
(still the reference for older items). Read the short version first.

## The short version

**Done and merged (lawkeeper PRs #34–#48):**
- **Gate fixes** (`scripts/gate_pretooluse.py`): a force-push with no named branch is
  now judged in the checkout named by `cd <dir> &&` / `git -C <dir>` (#34, the gap from
  the 10-07 handoff); unquoted Windows paths to git and `git.exe` are recognised (#40).
  Unresolvable directories (`$VAR`, `cd -`, `pushd`, `--git-dir`) make an unnamed
  force-push ask. Not handled: subshells like `(cd x && git push)`, backslash-escaped
  spaces in Windows paths, UNC paths.
- **Mutation testing:** advisory CI job `.github/workflows/mutmut-gate.yml` (ubuntu only,
  never a required check; mutmut 3 does not run on native Windows). Gate survivors
  146 → 16, killed 284 → 411 (`tests/test_gate_pretooluse_mutants.py`, #38/#39).
  Result and method: `docs/DESIGN_NOTE_mutmut_and_pinned_distribution_2026-10-10.md`.
- **`lawkeeper update`** (#36): `init` now records `template_version` + per-file sha256
  in `.guardrail.json`; `lawkeeper update` is a dry run by default, `--apply` writes only
  files unchanged locally, conflicts are diffed and never overwritten
  (`src/guardrail/template_sync.py`). Repos scaffolded earlier have no hashes.
- **Docs:** Claude Code's `PreToolUse` precedence is `deny > defer > ask > allow`
  (correction notes in the three surveys, #44, verified on the live hooks reference);
  noticeboard history committed (#42); research scans 2026-10-08/15/22/29 and 11-05
  merged (#33, #41, #43, #47, #48).
- **Registry (handoff item 13) — CLOSED.** All three conditions are met: (a) lawkeeper's
  domains are in falcun `agent/scope.py`, (b) `check_scope()` runs on every registry
  write, (c) the weekly routine files into the registry. Applied 2026-10-28 with the
  user's OK (`docs/DRAFT_routine_change_registry_2026-10-28.md`, status APPLIED). First
  filings worked: falcun PRs #42 (10-29) and #44 (11-05), entries `proposed`,
  `filed_by: lawkeeper/weekly-scan`. Those falcun PRs are the Falcun session's to review.

**Hygiene tasks (user-level, not in the repo):** the three every-3-days tasks now run
unattended for LawKeeper and Falcun. What fixed it: read-only `git`/`gh` allow rules in
`C:\Users\Admin\.claude\settings.json` (applied by the user, 2026-10-11 — Claude cannot
edit its own permission settings), the routines' working folder set to each repo's own
`E:` folder, worktree mode off, one approved full run, and a first summary line
`State saved (last_run …)` / `STATE NOT PERSISTED: …`. **Windwright's task still fails
silently some runs** (state.json last_run 2026-10-22; runs end in seconds): it needs its
own owner session or one approved full run. A hygiene run only counts if `state.json`
`last_run` is today and the run took minutes. Scheduled tasks only run while the app is
open (no 10-25 run happened).

## Open

- **Windwright hygiene task:** see above. Also Falcun's `state.json` is written with a
  UTF-8 BOM and a `T12:00:00` time in `last_run` (reported to the Falcun session).
- **Windwright board item 47:** 70 tracked files vanished from `E:\Windwright` on
  2026-10-22 ~13:58–14:04 UTC. Lawkeeper answered "nothing from us in that window" with
  evidence (NB-20261107T172602Z-4a33). Not lawkeeper's to solve.
- **Ideas from the scans, none started:** a `PermissionDenied` hook writing a structured
  deny attestation (10-22 scan §1, a future Law 14 upgrade); mutable-ref check for
  recorded external pins (design note step 3, wait for a consumer — Law 21);
  the AEF-as-base evaluation and a self-hosted scheduler (older handoffs).
- **Backlog hygiene:** falcun has 7 old branches without PRs (its own report).

## Things to know

- Merging a PR makes every other open PR "behind": `gh pr update-branch <n>`, wait for CI,
  then squash-merge, one at a time.
- Commit messages for code changes need a `Tests:` or `AUDIT:` line (Law 14); new test
  files need a theory card in `test_governance/cards/` (Law 18); modules stay under 500
  lines (compliance watchdog).
- Heredocs containing backslashes get mangled by the shell tool; write helper scripts with
  the file-writing tool and run them.
- The advisory mutmut job needs the gate tests staged in `gt/` (see the workflow); the
  gate tests import it as `scripts.gate_pretooluse`, not through `conftest.load_script`.
- Board posts edit tracked `docs/inter-agent/noticeboard/*.md`; the hygiene prompt ignores
  that folder. Commit the board in a docs PR now and then.
