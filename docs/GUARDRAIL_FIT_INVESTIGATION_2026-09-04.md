# Guardrail package — fit investigation for Falcun (and other repos)

**Queued:** 2026-09-04, from a Falcun session, at the user's request.
**Started 2026-09-06** — see "Findings" below for tasks 1, 2, 3, and 4.
Confirmed first that `claude/guardrail-fit-investigation-spmp2b` (a
different, earlier attempt at a related but distinct question — whether
lawkeeper's own guard scripts fit lawkeeper itself, not this doc's
Falcun-adoption question) is genuinely abandoned: its PR #3 was closed
2026-09-04 as redundant, no commits since 2026-09-03 — not touched by
this update. **Decision not yet made** — see "Still open" at the end.
**Related but distinct from** `docs/RESEARCH_governance_mechanism_audit.md`
(that one asks "does our governance tooling actually work, empirically,
across repos" via controlled comparison — not started either). This
file asks a narrower, prior question: **for Falcun specifically, is
`guardrail` the right tool to adopt, or should Falcun keep what it
already built?** If this investigation proceeds, its findings should
feed the effectiveness audit rather than duplicate its methodology.

## The ask, precisely

Falcun (separate repo, `C:\Users\Admin\Desktop\falcun`) spent real
effort this session hand-building its own git-hook governance
enforcement (`scripts/validate_commit_msg.py`,
`scripts/guard_branch.py`) — then found, the same night, that
lawkeeper already has a more general, pip-installable version of
overlapping functionality: the `guardrail` package
(`src/guardrail/`). Falcun currently has **zero** of `guardrail`
installed.

The question is not "does guardrail work" (see the other doc for
that) — it's **"should Falcun use it instead of / alongside / in
place of the hooks it just built"**, plus the same question for
whatever other repos have their own drifted copies of similar
mechanisms (Windwright confirmed to have some; "orbital-study" is
named in the other doc but not yet investigated by anyone as far as
this file knows).

## What's already confirmed real (verified 2026-09-03/04, on disk, not just read about)

All of the following exist exactly as described, checked via direct
`find`/`ls` from a Falcun session:

- `src/guardrail/template/scripts/install_hooks.py` — wires real,
  cross-platform git hooks (pre-commit, commit-msg, pre-push)
- `src/guardrail/laws/law_15_branch_naming.py` — branch-naming
  enforcement
- `src/guardrail/core/hedge_check.py` — Law 22, a mechanical
  overconfidence/hedge check
- `src/guardrail/template/scripts/system_audit.py` and
  `template/scripts/merge_gate.py` — audit/merge-gate checks
- `src/guardrail/memory/provider.py` — adaptive memory-provider system
- (Separately, also confirmed real: Windwright's own
  `scripts/check_doc_consistency.py` — a deliberately non-LLM,
  hand-written phrase-pair doc-consistency checker, already caught a
  real 3-week-live contradiction in Windwright's own docs. Different
  mechanism, same "reuse before rebuild" question.)

## Falcun's current hand-built equivalent (for direct comparison)

Built and adversarially tested this session, not hypothetical:

- `scripts/validate_commit_msg.py` — 6 real rules: governance-file
  change markers, provisional-keyword AUDIT markers, a mandatory
  `Verification:`/`Tests:` line on any `.py` change, human-check-path
  markers, canonical-claim-verification markers (ties a claim to an
  actual entry in `agent/canon.py`'s registry, not just a keyword
  match), and a state-file review marker. Each rule was adversarially
  tested (tried committing without the marker first, confirmed
  blocked) before being trusted.
- `scripts/guard_branch.py` — a Law-15-style branch-naming +
  content-preservation guard. **3 real, cascading bugs found and
  fixed live** while actually trying to delete real branches with it
  (see Falcun's `docs/WORKPLAN.md` for the incident write-up) — a
  useful data point on how much real-world exercise a governance tool
  needs before it can be trusted, which cuts both ways: it's evidence
  Falcun's version has now been battle-tested, and also evidence that
  a tool that "looks done" and passes its own tests can still have
  real, unexercised bugs.
- Both have real test suites (`agent/tests/`, `scripts/tests/`).

## Investigation tasks

1. **Fit-for-Falcun, feature by feature.** Does `guardrail`'s
   `install_hooks.py` actually cover everything Falcun's 6
   `validate_commit_msg.py` rules cover? Where it doesn't (Falcun's
   canonical-claim-verification and state-file-review rules look
   Falcun-specific, not generic), would `guardrail` need extending, or
   would Falcun keep those two as local additions on top of an
   otherwise-adopted `guardrail`? Is it cleanly pip-installable
   outside lawkeeper, or does it carry lawkeeper-specific
   assumptions/config that would need adapting?

2. **Fit-for-other-repos.** Same question for Windwright (what does
   it already have installed, if anything, and how does it compare?)
   and for "orbital-study" (unclear what this repo even is yet — a
   real first step is just locating it and checking whether it exists
   as described).

3. **Search for alternatives before committing.** Before adopting
   `guardrail`, search for whether a more established, widely-adopted
   OSS tool already solves "governance-as-code for git repos" better —
   e.g. the `pre-commit` framework, Conventional Commits tooling, any
   real "AI agent governance" framework. **Given tonight's Falcun
   session found a ~2-in-9 fabrication rate on tool names in one
   Devin-authored report** (two "real-sounding" GitHub repos that
   didn't exist as described), verify anything found the same way —
   actual PyPI/GitHub page, not just a plausible name — before citing
   it as a candidate.

4. **Improvement research on `guardrail` itself.** Read the actual
   code, not just the README. Specific things worth checking rather
   than assuming: does `hedge_check.py` do real analysis of hedging
   language, or is it pattern/keyword matching the way Falcun's own
   `agent/verify.py::_classify_source` turned out to be crude
   type-only matching dressed up as something smarter? Does
   `memory/provider.py` have real persistence guarantees or is it
   aspirational? This is exactly the kind of claim that needs
   hands-on verification, not README-trust — same discipline Falcun
   applied to Devin's research docs this session.

5. **Cross-reference, don't duplicate.** If this investigation
   surfaces evidence relevant to "does the mechanism actually work
   empirically" (item 3 above, or a controlled-comparison-style
   finding), hand it to
   `docs/RESEARCH_governance_mechanism_audit.md` rather than
   re-running that methodology here.

## Findings (2026-09-06)

### Task 4 — real, verified, and the single biggest finding of this pass

`Config` (`src/guardrail/config.py`) has **10 declared, typed,
`.guardrail.json`-configurable fields. 6 of them are dead** — checked one
by one with `grep -rn "\.<field>\b"` across the whole repo, not assumed:

- **Load-bearing (4):** `machines`, `canonical_branches` (via
  `canonical_branch_names()`), `feature_prefix` (via `feature_regexes()`,
  fixed 2026-09-04, see the note below), `show_internal_reasoning` /
  `reasoning_log` (ADR-006, real, used in `cli.py`).
- **Decorative — declared, loaded from JSON, never read anywhere else in
  the codebase (6):** `project_name`, `merge_prefix`, `placement_rules`,
  `regenerable_suffixes`, `regenerable_paths`, `governance_files`.

Concretely: `validate_pre_commit.py` has its **own separate, hardcoded**
`PLACEMENT_RULES`/`REGENERABLE_SUFFIXES`/`REGENERABLE_PATHS` dicts (with
different keys/values than `Config`'s same-named fields) and its own
comment claiming "`config.py`'s `Config` class intentionally does not
duplicate this" — false; `Config` has a `placement_rules` field, it's
just never consulted. A project editing `.guardrail.json`'s
`placement_rules`, `merge_prefix`, `regenerable_suffixes`,
`regenerable_paths`, or `governance_files` today gets silent no-ops on
5 of them — the exact `feature_prefix` bug shape, times five, found by
systematically checking every field instead of stopping at the one
already known. **Not fixed here** — this is either a real bug (wire
these fields in) or a real doc fix (state plainly that only 4 of 10
`Config` fields currently do anything), the user's call given the size
(wiring 5 fields into 2+ scripts each is a real feature-sized change).

Also for task 4: `hedge_check.py` (Law 22) is honestly exactly what it
claims to be — 5 hardcoded regex patterns matching the tail of a
message, explicitly documented as "deliberately narrow," not oversold as
semantic analysis. `memory/provider.py` is a pure ABC (no persistence of
its own, correctly); its one read-heavy concrete implementation,
`failure_pattern_provider.py`, does real TF-IDF relevance scoring over a
real corpus (tested) — genuine functionality. But `memory/` as a whole
is not wired into `cli.py` at all (see `.importlinter`'s own contract
comment, ADR-010) — its only real consumer is the standalone
`scripts/memory_query.py` dev script, not the shipped product.

### Task 1 — Falcun fit: already partially answered, with new evidence

Falcun's `scripts/validate_commit_msg.py` is not an independent
build — its own comment says "Adapted for falcun 2026-08-27 (governance
parity check) — lawkeeper's own governance-doc names replaced with
falcun's actual equivalents." Diffed directly: Rules 1-4 (governance
guard, provisional-work marker, Law-14 audit declaration, Law-23
human-facing check) are near-byte-identical to lawkeeper's own Rules 1-4.
Rules 5-7 (canonical-claim, state-file-review, prior-art-check) are real
Falcun-specific additions — confirming the doc's own guess from
2026-09-04.

**New, concrete evidence for the actual decision**: Falcun's forked copy
has **already drifted and is currently carrying a live bug lawkeeper
already found and fixed**. Rule 4 in Falcun's copy (line 411) still
calls `human_facing_changed(staged=True)` hardcoded — the exact bug
GitHub Copilot caught and lawkeeper fixed on 2026-09-04 (PR #4, commit
`e521c2c`): in CI (no staged files, message-file arg only), this
silently means Rule 4 never fires, disabling the Law 23 human-facing
check gate for every CI run. This is real, live, checked directly
(`grep -n "human_facing_changed(staged" falcun/scripts/validate_commit_msg.py`)
— not a hypothetical risk of forking, an actual instance of it, a little
over a week after the fork was made. Strong, concrete evidence toward
"depend on lawkeeper as a real package" over "fork and maintain a copy"
for at least Rules 1-4 — Falcun would need to keep Rules 5-7 as local
additions either way (guardrail has no canon.py/prior_art.py/state-file-
review equivalent — see `docs/CROSS_REPO_TOOL_PARITY_2026-09-05.md`),
making the "hybrid" option from the decision menu below the best-
evidenced choice so far, not yet formally adopted.

Is `guardrail` cleanly pip-installable outside lawkeeper with no
lawkeeper-specific assumptions? Not fully checked this pass — real next
step, not assumed either way.

### Task 2 — fit for other repos

- **Windwright**: has its own real, independent `docs/AI_CONSTITUTION.md`
  (confirmed — this is the repo lawkeeper's own constitution was
  originally extracted from, per multiple 2026-09-04/05 findings this
  session about unmigrated Windwright content in lawkeeper's own docs
  and scripts). No `.guardrail.json` — not currently using `guardrail`
  as a scaffolded project. `pip show guardrail` succeeds in the shell
  used to check this, but that's this machine's shared Python
  environment, not proof Windwright's own project depends on it —
  inconclusive, not asserted either way.
- **orbital-study**: located (`C:\Users\Admin\Desktop\orbital-study`,
  real repo, `kooshikooo-lab/orbital-study`). Confirmed to have **no
  governance tooling of any kind** — no `.guardrail.json`, no
  `AI_CONSTITUTION.md`, `scripts/` contains only `team_chat.py`/
  `team_chat_monitor.py`. A clean-slate candidate for `lawkeeper init`,
  not a fork-vs-adopt question the way Falcun is (nothing to migrate
  away from).

### Task 3 — real alternatives search (web-verified 2026-09-06, not assumed from training data)

- **[pre-commit](https://github.com/pre-commit/pre-commit)** — real,
  well-established (pre-commit.com), multi-language git-hook framework.
  Different scope than `guardrail`: manages *which* hooks run and their
  tool versions (linters, formatters, etc.), not *what a commit message
  must declare* or branch-topology/constitution enforcement. Genuinely
  complementary, not a replacement — `guardrail`'s hooks could plausibly
  run *as* pre-commit hooks rather than via its own `install_hooks.py`,
  a real integration question not investigated further here.
- **[DimitriGeelen/agentic-engineering-framework](https://github.com/DimitriGeelen/agentic-engineering-framework)**
  — the closest real analog found: "governance framework for AI coding
  agents — enforces task traceability, structural gates, session
  continuity, and audit trails for Claude Code, Cursor, and Copilot,"
  runs as a CLI (`fw`), 15 internal subsystems behind ~6 commands and a
  dashboard. Explicitly does not execute agents or provide a skills
  marketplace — governs agents that already exist, same positioning as
  `guardrail`. Conceptually close to lawkeeper's own laws (traceability
  ≈ Law 14 audit-before-commit + ADRs, session continuity ≈ Law 12,
  failure memory ≈ `AI_FAILURE_PATTERNS.md`). Not independently verified
  beyond its own README/search results — a real, worthwhile next step
  is reading its actual source, the same "don't trust the README"
  discipline task 4 already applied to `guardrail` itself.
- **[Microsoft Agent Governance Toolkit](https://opensource.microsoft.com/blog/2026/04/02/introducing-the-agent-governance-toolkit-open-source-runtime-security-for-ai-agents/)**
  — real (Microsoft Open Source blog, MIT-licensed), but a different
  category: runtime/OWASP-agentic-risk policy enforcement (tool-call
  interception), not git/commit-time governance. Lower relevance to
  `guardrail`'s actual mechanism.
- **systempromptio/awesome-ai-agent-governance** and
  **agentrust-io/awesome-ai-governance** — real curated lists, useful as
  a starting point for a deeper pass, not themselves tools.

## Decision this investigation should produce

One of: adopt `guardrail` as a dependency, fork-and-maintain a Falcun
copy, keep Falcun's hand-built hooks and only borrow specific patterns
from `guardrail`, or a hybrid (e.g. `guardrail` for the generic rules,
Falcun's own code for the two Falcun-specific rules). Write the
decision and its reasoning to disk when made — this file's own
existence is itself an instance of the project's write-through rule
("nothing lives only in chat"), and the decision should follow the
same discipline.

## Note added 2026-09-04 (after this file was first written): a real example for task 4

While fixing an unrelated problem (the `opencode/`-to-`agent/`
branch-prefix rename, see `docs/WORKPLAN.md` in Falcun for the full
story), a concrete, real instance of exactly what task 4 above asks to
look for turned up: `src/guardrail/config.py`'s `Config.feature_prefix`
was a documented, dataclass-level, user-configurable field —
but `Config.feature_regexes()` never actually read it; it hardcoded
the branch-prefix pattern as a literal string instead. Editing
`feature_prefix` in a repo's `.guardrail.json` silently did nothing,
for as long as that code existed. Now fixed (see commit `a40e152` on
`opencode/framework-mvp/desktop`) — `feature_regexes()` genuinely
derives its pattern from `self.feature_prefix`. Worth treating as a
concrete precedent when doing task 4's review: at least one other
field in this config surface was decorative rather than load-bearing,
so don't assume the rest of `Config`'s fields are actually consumed
just because they're documented and typed — check each one the same
way.

## Still open after this pass (2026-09-06)

Not a completed investigation — real progress on all 4 tasks, but the
decision itself is not made:
1. Whether/how to fix the 6 decorative `Config` fields (real bug or real
   doc fix — user's call given the size).
2. Whether Falcun formally adopts `guardrail` as a dependency for Rules
   1-4 (strong new evidence favors it; not decided or implemented).
3. Whether `guardrail` is cleanly pip-installable outside lawkeeper with
   no lawkeeper-specific assumptions — not checked.
4. A deeper read of `agentic-engineering-framework`'s actual source
   (task 3's closest real analog) — not done, README/search-level only.
5. Formally logging a decision for Windwright and orbital-study, beyond
   "orbital-study is a clean-slate candidate."

## Re-check when

Before the decision above is made, or before either Falcun's or
Windwright's governance tooling is next substantially changed (the
Rule 4 drift found this pass is exactly the kind of thing that keeps
recurring the longer a fork goes unreconciled).
