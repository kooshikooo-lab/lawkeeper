# Session Handoff — 2026-10-07: research routine fixed, repos connected, C: copy retired

Written at the end of the session that ran 2026-09-26 → 2026-10-07 (it
started in the old `C:\Users\Admin\Desktop\lawkeeper` copy and worked from
`E:\lawkeeper`). Read the short version first; the rest is reference. The
older handoffs (`SESSION_HANDOFF_2026-09-13.md`, `SESSION_HANDOFF_2026-09-26.md`)
are still the master to-do list; this one sits on top of them.

## The short version (read this first)

**Where lawkeeper lives:** `E:\lawkeeper`, nowhere else. The old C: copy is
retired. Every branch it had (two were never on GitHub) is saved in
`E:\lawkeeper-C-backup-2026-09-14\lawkeeper-C-copy-all-branches-2026-10-02.bundle`
(checked on 2026-10-07: identical to the folder). The user is deleting the
folder. To get a branch back, clone or fetch from that bundle.

**What works now that didn't before:**
- **The weekly research routines.** All three (Windwright, Falcun, lawkeeper)
  now run **Thursdays 07:30 / 08:30 / 09:30 UTC**, just after the weekly
  usage limit resets. They used to run on Mondays, when the shared limit was
  already used up. The first Thursday run (2026-10-01) worked for all three.
  Lawkeeper's produced `docs/RESEARCH_EXTERNAL_SCAN_2026-10-01.md` (PR #29).
- **Routine branches can be pushed.** The routines name their branch
  `agent/<topic>/cloud`; lawkeeper's Law 15 guard didn't know the machine
  "cloud", so lawkeeper's 2026-09-28 report was finished but never uploaded.
  `.guardrail.json` now lists `cloud` (PR #28). falcun did the same (falcun
  #10); Windwright's version is Windwright PR #99 (user-approved, Law 15 text).
- **Cross-repo notice board.** lawkeeper and falcun are wired to the
  notice board Windwright sessions use (PR #27, falcun #4). Sessions see new
  notes automatically. Machine board: `C:\Users\Admin\agent-noticeboard\`.
  How-to: `docs/inter-agent/README.md`.
- **Tests check this checkout's own code.** A stale install made
  `E:\lawkeeper` import `guardrail` from the old C: copy, so tests and the
  architecture audit were silently checking the wrong code (results matched
  only because the code hadn't changed). Fixed in the repo (PR #30: pytest
  `pythonpath = ["src"]`, audit puts `src/` on the path) and on this machine
  (`pip install -e E:/lawkeeper`, stale `guardrail` install removed).

**User decisions made in this session (all recorded):**
1. Shared research registry: **yes** (PR #26). Falcun drafted the design
   (falcun PR #8, still open). Lawkeeper's reply is on the board
   (NB-20261007T181804Z-1c2a): see "Open" below.
2. Research routine: solved jointly by the three repos, then moved to
   Thursdays (done).
3. Standing rule for every repo, now in `AGENTS.md` (PR #31): the user's
   decisions go in **one multi-select menu** with "(Recommended)" first; no
   loose questions in prose; **agents do the work** once approved and finish
   their own PRs (verify, answer review threads, resolve, squash-merge);
   technical choices are the agent's.

## What is still open

**Needs the user (one click each):**
- **Hygiene checks stuck on permission prompts.** The three every-3-days
  git-hygiene tasks (Windwright, Falcun, LawKeeper) start, then wait forever
  on their first shell command. Fix: open each running "… git hygiene check"
  session in the sidebar and approve with "always allow". Approvals are saved
  on the task, so it's a one-time fix. Lawkeeper's task now scans
  `E:\lawkeeper` (it was still pointed at the C: copy; repointed 2026-10-07).

**For lawkeeper sessions — first, a safety-gate gap found 2026-10-07 (not fixed):**
- `scripts/gate_pretooluse.py` decides "which branch is current" for a push
  with no named destination by running git in the *session's* folder
  (`_current_branch()`), ignoring a `cd <dir> &&` or `git -C <dir>` in the same
  command. Reproduced: from a checkout on a feature branch, the gate **allows**
  `cd /e/lawkeeper && git push --force` and `git -C /e/lawkeeper push --force`
  while `E:\lawkeeper` is on `main`; the plain `git push --force` run from the
  `main` checkout is correctly denied. GitHub branch protection on `main` still
  refuses force-pushes, so `main` is backstopped, but the gate's own guarantee
  fails silently; the opposite case gives false blocks (seen 2026-09-28).
  Fix: resolve the target checkout from `cd`/`-C` (or fall back to "ask" when
  the command changes directory), with tests for both directions.

**For lawkeeper sessions:**
- **Registry and item 13.** Lawkeeper's own "does this finding belong here"
  check (2026-09-13 handoff item 13) will be covered by the registry's
  `check_scope()`, provided (a) the registry knows lawkeeper's topics
  (runtime/PreToolUse governance, allow/deny/ask decision algebras, git-hook
  enforcement, test-governance/oracle independence), (b) the check runs on
  every registry change automatically, and (c) lawkeeper's weekly routine
  files findings into the registry. (c) and adding falcun to the routine's
  repo access are routine changes for the user to OK once the design is
  agreed. Close item 13 only when all three, (a), (b) and (c), are approved and in place.
- **From the 2026-10-01 research report** (`docs/RESEARCH_EXTERNAL_SCAN_2026-10-01.md`):
  queued items now resolved: MITRE ATLAS, AWS Cedar, pre-commit. Codex's
  hook protocol: much better evidenced but no first-party doc read yet.
  Open Plugins: still blocked by the cloud sandbox's network. Two leads worth
  acting on, neither started:
  - pre-commit's *distribution* model (pinned references + a warning on
    mutable refs) as a design to copy for how lawkeeper ships its guard
    scripts and records pinned external commits. Not the pre-commit tool itself.
  - `mutmut` (BSD-3) as a complement to Law 18's hand-rolled single-mutation
    T4 check.
  - Codex finding, stated carefully: whether Codex enforces a hook's `deny`
    is not settled and depends on more than version or platform
    (openai/codex#27833, still open): enforced on 0.147.0 macOS; not enforced
    on Windows CLI 0.154.0 with a long-used `CODEX_HOME`, but enforced on that
    same build with a fresh, empty `CODEX_HOME` (same reporter, 2026-09-15).
    Matters if `EXECUTOR_CONTRACT.md` ever adds a Codex adapter: it would need
    characterization tests per version, platform, tool-call type and
    configuration state.
- **Still from 2026-09-13, unchanged:** the AEF-as-base evaluation
  (Priority 2, set up, not started, needs uninterrupted time); moving routines
  to a self-hosted scheduler (Priority 4).

**Belongs to other repos (tracked on the board, not lawkeeper's job):**
falcun #15 and #8; Windwright #96/#93 (backlog session) and #99 (L7).

## Things to know when working here

- **Branch names.** `agent/<topic>/desktop` for this machine; `cloud` is valid
  for the cloud routines. When force-pushing a feature branch, name it
  explicitly (`git push --force-with-lease origin <branch>:<branch>`); that's a
  recommendation, not a rule the gate enforces. The gate blocks a push whose
  named destination is canonical, and a push with no named destination only
  when the current branch is canonical (`scripts/gate_pretooluse.py`, the
  `explicit_targets` logic).
- **Notice-board hook form.** lawkeeper/falcun hooks call
  `python ${CLAUDE_PROJECT_DIR}/scripts/noticeboard.py ...`. Verified only
  with hooks running through Git Bash on this machine, not under
  PowerShell-only and not with a path containing spaces. Windwright keeps a
  POSIX-guarded form. Both are recorded on the board (NB-...dfb8).
- **Limits.** All sessions and routines share one account: a weekly limit
  (resets Thursday 07:00 UTC) and a 5-hour limit. A busy morning of
  interactive sessions blocked a routine once (2026-09-28). Before starting
  anything large, post one line on the board.
- **Memory.** This session's notes live in
  `C:\Users\Admin\.claude\projects\E--lawkeeper\memory\` too (copied there,
  including "finish own PRs" and "agents are the doers"), so a session opened
  in `E:\lawkeeper` starts with them.

## Merged in this session

lawkeeper #26 (decisions), #27 (notice board), #28 (cloud machine), #29
(2026-10-01 research report, Codex claims corrected from the issue's own
comments), #30 (own `src/` on path), #31 (decision-menu rule). falcun #4
(notice board), #7 (2026-09-28 scan; replaces #3; FPF source confirmed by a
real OpenAlex check; `mechanically_confirm_source()` now runs the check
itself), #10 (cloud machine).
