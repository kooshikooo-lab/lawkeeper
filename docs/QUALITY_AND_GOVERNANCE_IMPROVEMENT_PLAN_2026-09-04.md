# Quality & Governance Improvement Plan (2026-09-04)

## Why this exists

Prompted directly by the user, mid-audit: distrust of the last several
days' commits, and a broader statement that the current state — bug rate,
governance-tool reliability — "is not nearly good enough on a number of
metrics." This document is the write-up requested, not a vibe check: it
starts from what this session actually found by running things, not from
impressions.

## The evidence, stated plainly

This session ran the real test suite and the real guard scripts against
`opencode/framework-mvp/desktop` — the branch with the most governance
tooling in the whole project — rather than trusting commit messages. It
found 3 confirmed, root-caused bugs in one pass (fixed separately, see
commits `f0be48d`, `3768f04`, `cf9e07a`):

1. A hardcoded single-machine path (`C:\Users\Admin\Desktop`) silently
   zeroed out a whole feature (`mine_failure_patterns.py`'s corpus) on
   any other machine.
2. Two of this repo's own guard scripts (`toolcheck.py`,
   `validate_pre_commit.py` — the *actual live pre-commit hook*) were
   still blind to this project's own source directory, `src/guardrail/`
   — a fix already made and verified on a sibling branch (PR #3 on
   `main`) three weeks ago, never picked up here.
3. A unit test was silently corrupting a real, tracked file
   (`BLOCKERS.md`) on every single run, for months — explaining a wall
   of ~20 near-identical duplicate entries already sitting in that file.

None of these were found by reading commit messages. All three were
found by actually executing the code and diffing real output.

**The pattern underneath all three, and worth naming honestly:** this is
not random bad luck. Finding #2 is the *third* time this exact bug shape
(a guard script hardcoding one project's directory names, blind to its
own) has appeared in this repo's own history — `compliance_watchdog.py`
and `check_local_dependencies.py` already had it fixed once
(`scan_config.py`, introduced specifically to stop it recurring), and it
still recurred twice more in scripts that weren't touched by that fix.
A shared fix existing in the codebase does not mean it gets applied
everywhere it's needed — that's a real, recurring quality gap, not a
one-off.

## What's already working, so this isn't starting from zero

- A real, broad set of mechanical guards already exists and mostly runs
  (system_audit, compliance_watchdog, toolcheck, validate_pre_commit,
  validate_commit_msg) — most projects have none of this.
- An honest debt-logging habit (`FIXES.md`, `BLOCKERS.md`, `AI_FAILURE_PATTERNS.md`)
  — failures get written down, not hidden. `mine_failure_patterns.py`
  exists specifically to learn from that history systematically, which
  is a real, good idea, just currently broken (fixed today).
- A cross-agent coordination tool already exists: `scripts/team_chat.py`.
  The gap is using it consistently, not building a new one (see Phase C).

## Phase A — Mutation testing: verify the tests actually test something

252/252 passing tells you the tests that exist don't currently fail. It
does not tell you whether those tests would catch a real bug — bug #3
above (an un-mocked side effect) is exactly the kind of gap that a
92%-coverage, 100%-passing suite can hide indefinitely. Mutation testing
answers the actual question: for each small deliberate change to the
source, does *some* test fail? A test suite that lets mutants survive
silently is asserting less than it looks like it is.

**Tool choice, researched, not assumed:**

- [Cosmic Ray](https://github.com/sixty-north/cosmic-ray) ([docs](https://cosmic-ray.readthedocs.io/)) —
  actively maintained (v8.4.x as of this research), Python ≥3.9,
  config-driven via a TOML file (fits this repo's existing
  `pyproject.toml`-centric style), and is the only one of the two with
  real build-tool integration — matters here since this repo already has
  a CI backstop (`governance-guard.yml`) mutation testing could plug
  into later.
- [mutmut](https://github.com/boxed/mutmut) — simpler, lower setup
  overhead, and per a recent academic comparison, the more actively
  maintained of the two by issue-resolution speed. A reasonable fallback
  if Cosmic Ray's config proves heavier than warranted for a repo this
  size.
- Independent grounding, not just tool docs: an IEEE paper and an ACM
  (SBQS 2026) paper both directly compare Python mutation tools on real
  metrics (mutant uniqueness, competency score) — worth reading before
  committing to one, not just picking by name recognition.

**Proposed first target, not the whole repo at once:** `src/guardrail/core/`
and `src/guardrail/laws/` — the parts every other guard script and the
CLI itself trusts. If mutation testing finds survivors there, it's the
highest-leverage place to find them.

**Not started yet** — this needs your go-ahead before I add a new dev
dependency and run what can be a slow, CPU-heavy process (mutation
testing re-runs the test suite once per mutant). Say the word and I'll
scope a first run.

## Phase B — A mechanical check for the exact bug class found today

Bug #1 and the recurring #2 pattern are both "a hardcoded, machine- or
project-specific literal in a file meant to be shared/portable." This is
mechanically detectable — a script scan for absolute paths
(`C:\`, `/home/`, `/Users/`) and for suspiciously narrow hardcoded
directory-name lists in `scripts/`/`src/` — the same kind of static
check `validate_pre_commit.py` already does for hardcoded IPs.

This would be a new constitutional rule (the file's current highest is
Law 23). Per this repo's own Law 22 ("technical decisions proceed;
directional decisions ask or flag"), **adding a new Law is a directional
decision** — proposed here, not added unilaterally. If you want it, I can
draft "Law 24 — No machine- or project-specific literals in shared
tooling" plus the mechanical check, the same way Law 15/18/22 each got a
real enforcement script alongside the prose.

## Phase C — Cross-session coordination, using what already exists

You raised this directly: other sessions (Falcun, and whatever the
"Windroid"/Windwright session built) need to know about this fix, and
governance tooling changes need to be visible across sessions instead of
each one rediscovering the same bug independently — which is *literally
what happened* here: PR #3 and this branch both independently found and
partially fixed the same `backend/`/`woodwright_designer/` hardcoding,
without either session knowing about the other's fix, because nothing
told them to check.

`scripts/team_chat.py` already exists for exactly this. Before building
anything new: confirm it's still working, check whether it's actually
being read at session start (per the project's own `governance-recall`
skill's cadence), and use it now to post this fix + the divergence
finding for Falcun/other sessions to see. Reaching for a new
"interagent tool" before checking whether the existing one is just
unused would repeat Law 21 ("a capability with no consumer is a bug, not
neutral") on a tool built specifically to prevent that.

## Phase D — Real architecture grounding, not vibes

You asked for real CS-principles research into sound architecture, not
assumptions. Two things worth being honest about:

1. Some of the right principles are *already named* in this repo's own
   constitution (Law 3/7: one source of truth; Law 8: one responsibility
   per module) and even partially *implemented* (`scan_config.py` is a
   real, working instance of dependency inversion — one shared resolver
   instead of N copies) — the gap is applying them consistently, not
   knowing they exist.
2. Nobody has done a deliberate pass checking `src/guardrail/`'s actual
   module boundaries against those principles with fresh eyes — every
   past pass has been reactive (a specific bug triggered a specific fix).
   A real architecture review is a distinct, larger piece of work from
   bug-fixing and deserves its own scoped pass rather than being folded
   into this one.

## What's actually next

In rough order, each independently sized so you can pick without
committing to all of it:

1. **Small, now:** post this fix + the divergence pattern to
   `team_chat.py` for Falcun/other sessions (Phase C, low effort, real
   coordination value).
2. **Small, needs your decision:** approve or amend the proposed Law 24
   + its mechanical check (Phase B).
3. **Medium, needs your go-ahead:** scope and run a first Cosmic Ray
   pass against `src/guardrail/core/` + `src/guardrail/laws/` (Phase A).
4. **Larger, separate effort:** a real architecture review of
   `src/guardrail/` against named principles (Phase D) — not started,
   not estimated yet.

Sources consulted for Phase A: [Cosmic Ray on PyPI](https://pypi.org/project/cosmic-ray/), [Cosmic Ray docs](https://cosmic-ray.readthedocs.io/), [Cosmic Ray on GitHub](https://github.com/sixty-north/cosmic-ray), [mutmut write-up](https://medium.com/hackernoon/mutmut-a-python-mutation-testing-system-9b9639356c78), [IEEE comparison paper](https://ieeexplore.ieee.org/document/10818231/), [ACM SBQS 2026 comparison paper](https://dl.acm.org/doi/10.1145/3701625.3701659).
