# Session Handoff — 2026-09-04 audit + governance/quality initiative

Written by a cloud Claude Code session at the user's explicit request for
a full, complete brief — not a summary. Read this in full before doing
anything on lawkeeper today; it replaces any shorter chat-pasted version
of this handoff that came before it.

## 1. Why this session happened

The user asked, mid-conversation, to audit `lawkeeper` before trusting
recent work: "there's so much sloppiness, and I don't trust the code
before it's properly verified." This was not a vague worry — it led
directly to real, confirmed bugs (section 2). Everything else in this
doc (the quality plan, the architecture review, the cross-repo ask)
grew out of that one request, expanded by the user across several
follow-up turns into a broader mandate:

- Raise the standard across **all** repos (lawkeeper, Falcun, Windwright,
  orbital-study), not just this one.
- Coordinate that effort across sessions instead of each one working in
  isolation and re-finding the same problems independently.
- Use real testing procedures — specifically **mutation testing** with
  the best available external tools, not just "tests are green."
- Check the actual architecture against **real, established CS
  principles** — researched, not assumed.
- Find unused/dead scripts and tool-parity gaps across repos.

The user has said, more than once and in more than one way, that they
feel overwhelmed by how much is in motion and by confusing tooling
(branch names, cloud-vs-local sessions, being told to install something
they already had). If you are the session picking this up: **default to
fewer, clearer next steps, not more findings dumped on them at once.**
Confirm before doing anything hard to reverse.

## 2. What was actually found and fixed today (verified, not assumed)

All of this is already merged into `main` as of commit `aed62fc`
(squash-merged PR kooshikooo-lab/lawkeeper#4, which itself carried 70
commits — including everything from `opencode/framework-mvp/desktop`,
a branch that had been diverging from `main` unmerged since 2026-08-20).

Real bugs found by actually running the code, not by reading commit
messages:

1. **`scripts/mine_failure_patterns.py`** hardcoded `C:\Users\Admin\Desktop`
   as the sibling-repos root. Worked only on that one machine; silently
   returned zero records everywhere else. Fixed to resolve relative to
   the repo's own real location (same pattern `scan_config.py` already
   used elsewhere).
2. **`scripts/toolcheck.py` + `scripts/validate_pre_commit.py`** were
   still blind to `src/guardrail/` — lawkeeper's own source. The identical
   bug had already been found and fixed on `main` via PR #3, but
   `opencode/framework-mvp/desktop` split off before that fix landed and
   never got it. Ported the same fix rather than reinventing one. This
   also surfaced two more real, previously-invisible gaps once the tool
   could finally see its own source: a missing `claude_agent_sdk` →
   `claude-agent-sdk` alias, and `pkgutil` missing from the stdlib list.
3. **A test was silently corrupting a real tracked file.**
   `test_not_logged_in_raises` in `tests/test_consensus_review.py` never
   mocked `report_blocker()`, so every run of the test suite — for
   months, across many sessions — appended a new duplicate timestamped
   entry to the real, tracked `BLOCKERS.md`. That's what the wall of ~20
   near-identical entries in that file's history actually was.
4. **CI had never once run against `opencode/framework-mvp/desktop`**
   (this repo's workflow only triggers on `main` push + PRs into it), so
   merging it via PR immediately surfaced a real, previously-hidden CI
   failure: `check_local_dependencies.py --warn` correctly flagged
   `claude-agent-sdk` as declared+imported but not installed, since CI's
   `pip install -e ".[dev]"` never installed the "agent" extra. Fixed by
   adding `,agent` to that one install step (root workflow only — the
   shipped template's CI copy deliberately stays plain, since a
   `lawkeeper init`-scaffolded project has no `agent.py` of its own).
5. **GitHub's automated Copilot review left 4 real findings**, all
   verified against the code before fixing (not taken on faith):
   - `validate_commit_msg.py` Rule 4 hardcoded `staged=True` instead of
     the real computed `staged` value (missing the same fix Rules 1/3
     already got on 2026-08-17); `human_facing_changed()` itself also
     ignored its own `staged` parameter. Fixed to mirror the correct
     existing pattern.
   - `load_human_facing_patterns()` resolved `.guardrail.json` relative
     to the hook's cwd instead of the repo root — same class of bug as
     item 1 above. Fixed via `git rev-parse --show-toplevel`.
   - `hardware_scanner/storage.py`'s docstring claimed dedup by
     `(source, product_id, url)`; the real schema constraint is
     `(source, url)` only. Docstring corrected; also removed a genuinely
     unused `Path` import.
   - `ExecutorResult.combined_output()` prepended a stray leading newline
     for the empty-stdout/non-empty-stderr case. Fixed, with a new
     regression test.

Full suite: 256 tests passing (was 252 before today; +4 new tests added
covering the fixes above). `toolcheck.py`, `validate_pre_commit.py`,
`compliance_watchdog.py --check-baseline` all exit 0.

## 3. The two full write-ups — already merged, read them directly

Rather than duplicate ~300 lines of detail here, both are real files on
`main` right now:

- **`docs/QUALITY_AND_GOVERNANCE_IMPROVEMENT_PLAN_2026-09-04.md`** —
  the quality initiative itself. Covers mutation testing tool research
  (Cosmic Ray vs. mutmut — sources listed in that doc's own "Sources
  consulted for Phase A" line at the bottom: PyPI, official docs, GitHub,
  and an IEEE + an ACM SBQS 2026 comparison paper. Cosmic Ray recommended
  first there: active, TOML-configured, real build-tool integration — see
  section 5 below for the separate, live-run confirmation of its
  Windows/WSL behavior), a proposed new constitutional rule for the exact
  "hardcoded machine-specific literal" bug class found today (explicitly
  NOT added unilaterally — flagged as a directional decision per this
  repo's own
  Law 22), cross-session coordination guidance, and a real architecture-
  research angle.
- **`docs/ARCHITECTURE_REVIEW_2026-09-04.md`** — the deeper pass the
  user explicitly asked for, verified against the real import graph, not
  a rubric. Key findings: clean one-directional layering in
  `src/guardrail/` (a real strength, stated plainly); `executor.py` and
  `agent.py` are fully built and tested but have **zero real consumers**
  anywhere in the codebase (this project's own Law 21, unapplied to its
  own code); a mechanical template-sync test (`test_template.py`) is
  declared for 9 files but only enforced for 6 — of the 3 unenforced,
  `install_hooks.py` has already drifted for real; and the shipped
  `lawkeeper init` template bundles general LLM-orchestration tools
  (`ai_review.py`, `consensus_review.py`, `team_chat.py`) alongside actual
  governance enforcement, which doesn't read as a deliberate
  product-boundary decision.

**Read both in full before proposing any new architecture or testing
work** — re-deriving what they already cover would repeat the exact
mistake this session was started to correct (working without checking
existing work first).

## 4. Two real decisions still waiting on the user — do not decide these

Both are called out explicitly in the architecture review as *not*
something a session should settle on its own:

1. **`executor.py` / `agent.py`**: keep them and actually wire in a
   consumer (Stage 2+ of the original plan), or pull them until there is
   one. Real, tested code either way — the question is product direction,
   not correctness.
2. **Shipped template scope**: should `lawkeeper init` keep bundling
   general agent-coordination tools alongside governance enforcement, or
   should those be split out so "governance" and "utilities" are two
   honestly-named things?

If either comes up again, surface the question — don't pick an answer.

## 5. Cross-session / cross-repo coordination — what's actually correct

Two real, confirmed facts from earlier today, from a session working on
Windwright on this same physical machine:

- **Same-machine coordination should use `shared_memory/` direct file
  access, not chat relay or `team_chat.py`.** This repo has its own
  documented convention for exactly this:
  `shared_memory/same-machine-direct-file-access-not-chat-relay.md`. The
  earlier chat-pasted handoff from this cloud session wrongly pointed at
  `team_chat.py` as the answer — that tool is for cross-machine
  coordination, not same-machine. Use the right one.
- **Cosmic Ray needs no WSL on Windows**; it's `mutmut` that requires it.
  Reported by a Windwright session as a real, live mutation-testing run
  on this machine (once against a toy function, once against a real
  Windwright module) relayed into this conversation, not read from this
  repo's own history — there is no file in *this* repo recording that
  run, so treat it as a strong, first-hand claim from another session
  rather than something independently auditable from lawkeeper alone. If
  it matters for a decision here, ask that session (or check Windwright's
  own repo) for where the run's output was saved, rather than citing this
  paragraph as the source.

## 6. Outstanding work, explicitly delegatable (this cloud session cannot do these — no access to the other repos)

- **Re-run `scripts/orphan_scan.py` fresh, across all four repos**
  (lawkeeper, Windwright, Falcun, orbital-study). It already exists and
  already found 17 real candidates once before
  (`docs/SESSION_ROUNDUP_2026-08-21.md`), but that scan is now over two
  weeks stale.
- **A tool-parity check across repos**: what exists in one repo's
  `scripts/` that the others don't have and could use (the user's
  explicit ask — "check what tools are available in one repo that could
  be used in another").
- **Apply today's audit pattern to the other repos too**: specifically,
  check each one for the same "hardcoded machine-specific path" /
  "guard script blind to its own source" bug shapes found here — this
  exact class of bug has now recurred at least 3 times in lawkeeper's own
  history alone.
- **Mutation testing**: a first real Cosmic Ray pass was already started
  (on this machine, against a real Windwright module) — check its result
  and consider a first pass against `src/guardrail/core/` and
  `src/guardrail/laws/` too, per the plan doc's Phase A.

## 7. Git/branch state as of 2026-09-04, right after this doc was written

This section is a snapshot, not a live fact — `main` moves. Verify with
`git log -1 main` rather than trusting the SHA below if any real time has
passed since this doc was written.

- `main` was at `aed62fc3c95e4c6b20f1449796a59ce37733788c` as of this writing.
- PR kooshikooo-lab/lawkeeper#3 (the earlier, smaller investigation) is
  **closed**, superseded by #4.
- PR kooshikooo-lab/lawkeeper#4 is **merged** (squash).
- Leftover branches still on GitHub, safe to delete (all fully merged,
  confirmed via `git merge-base --is-ancestor` before this was written):
  `opencode/framework-mvp/desktop`, `opencode/executor-backend/laptop`,
  `claude/guardrail-fit-investigation-spmp2b`. Deleting them needs a
  manual click on GitHub (the "Delete branch" button on each) — the
  cloud session that did today's work was blocked by its own sandbox
  from deleting branches directly.
- This repo's branch protection requires **all PR review threads
  resolved** before merge (not just green CI) and only allows **squash**
  merges (not merge-commit or rebase) — worth knowing before opening the
  next PR here.
