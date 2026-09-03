# Guardrail package — fit investigation for Falcun (and other repos)

**Queued:** 2026-09-04, from a Falcun session, at the user's request.
**Not started** — this file scopes the investigation so it isn't lost.
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

## Decision this investigation should produce

One of: adopt `guardrail` as a dependency, fork-and-maintain a Falcun
copy, keep Falcun's hand-built hooks and only borrow specific patterns
from `guardrail`, or a hybrid (e.g. `guardrail` for the generic rules,
Falcun's own code for the two Falcun-specific rules). Write the
decision and its reasoning to disk when made — this file's own
existence is itself an instance of the project's write-through rule
("nothing lives only in chat"), and the decision should follow the
same discipline.

## Re-check when

A Falcun (or Windwright) session actually starts this investigation,
or before either repo's governance tooling is next substantially
changed.
