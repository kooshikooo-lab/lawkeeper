# Future Directions

Ideas that are explicitly out of scope right now but deliberately not lost.
Unlike the roadmap sections of other docs, this file exists specifically to
hold things that were *decided to be deferred*, with enough context that
picking one back up doesn't require re-deriving why it mattered. See also
task #85 in the session tracker and the `hermes-comparison-deferred` memory
note (Claude's persistent memory) — both point back here.

**Every entry below MUST have a `Re-check when:` line** — a concrete,
checkable condition, not "someday" or "later." A deferred item with no
re-check trigger is a failure mode (see `docs/AI_FAILURE_PATTERNS.md`,
2026-08-20 entry): it silently becomes permanent, indistinguishable from
"never." Whenever an agent reads this file for any reason, check every
`Re-check when:` condition against current reality, not just the one entry
that prompted the read — a condition that now holds means the item is
un-deferred as of that session, not "still someday."

---

## [UN-DEFERRED 2026-08-20] Point Falcun's evolutionary methodology at the failure-pattern corpus

**Deferred:** 2026-08-19, explicitly scoped out of the same-day session
that built `scripts/mine_failure_patterns.py`, per the plan's own Step 3.
**Re-check when:** an unattended/headless session has enough time budget to
do real design+implementation work, not just a live one-hour interactive
session. **Un-deferred:** 2026-08-20 — exactly that condition held (a
headless dispatch can run 30-50+ minutes unattended), caught when the user
pushed back on treating "deferred" as permanent. Dispatched to falcun via
headless `opencode run`; see Windwright Discussion #23 for live status.

**Context:** the miner does real, valuable work today (parsed 19 real
failure records across Windwright and lawkeeper into themes by hand,
already led to Law 20 being added — see `docs/AI_CONSTITUTION.md`), but
the categorization is manual (`THEME_MAP`, hand-assigned) and the
governance response is a one-off human/Claude judgment call, not a
systematic loop. [[falcun-broader-vision]] establishes Falcun's actual
purpose as a reusable evolutionary methodology (population of rules,
fitness-scored against real outcomes, mutation/selection across
generations) — pointing that at this corpus is the natural next-level
version: candidate governance rules/checkers as the population, fitness =
how many real historical failure records a candidate would have caught,
evolved instead of hand-picked.

**Real external grounding (2026-08-19, `docs/RESEARCH_AUTOMATED_DISCOVERY.md`):**
this exact architecture — LLM-guided evolutionary search with a
mechanical fitness function — is not a bespoke idea; it's the same
pattern behind DeepMind's AlphaEvolve/FunSearch, with a real,
independently-verified result (a new 48-multiplication 4x4 matrix
algorithm, the first improvement on Strassen's 56-year-old record). This
item is genuinely well-precedented, not speculative.

**If this gets picked back up again** (e.g. the dispatch above didn't
finish or didn't land): the corpus format `mine_failure_patterns.py`
already produces (`FailureRecord`: repo, id, date, law_or_theme, problem,
root_cause, fix, severity, theme) is the natural input — no need to
re-parse `AI_FAILURE_PATTERNS.md` again, just feed the existing structured
output into whatever Falcun population/fitness setup gets built.

---

## Adopt Hermes's memory-provider pattern (not its verification model)

**Deferred:** 2026-08-19, by the user. Explicitly "a direction worth
considering, but not now."
**Re-check when:** lawkeeper becomes an active project again (see the
"Status" note below for what that means concretely) — this session's
multi-agent claim/release work (2026-08-20) is lawkeeper-adjacent
tooling, not lawkeeper itself becoming active; don't let that be
mistaken for the trigger firing.

**Context:** lawkeeper's original vision was a coding-assistant harness /
governance system robust enough to make even a weaker model do good work,
with memory encoded into it — closely overlapping with what Hermes Agent
(Nous Research) already does. Earlier research into this space missed
Hermes and similar prior art entirely, so the comparison was never actually
done until now.

**What a real comparison found** (Hermes installed locally, source read
directly — not marketing copy):

- **Worth adopting:** Hermes's `MemoryProvider` abstraction
  (`agent/memory_provider.py`) — a pluggable interface with a clean
  lifecycle (`initialize`, `prefetch`, `sync_turn`, `shutdown`), where
  `prefetch(query)` runs *before every turn*, keyed on the incoming
  message, and injects only what's relevant. Lawkeeper's
  `AI_FAILURE_PATTERNS.md` is the same underlying idea (durable,
  cross-session memory of lessons) but has no relevance-based
  injection — it's a file that has to be manually read.
- **Worth adopting:** the "learning graph" concept (`agent/learning_graph.py`)
  — skills and memories as first-class nodes with usage tracking
  (`use_count`, `pinned`, `created_by`), making what's actually been
  learned over time visible rather than just accumulated.
- **NOT worth adopting:** Hermes's verification step
  (`agent/verify_hooks.py`) is a soft in-context prompt nudge — text
  appended to the conversation encouraging the model to check its work,
  with nothing mechanically enforcing it. That is the opposite of
  lawkeeper's actual founding premise (Law 16: "guards MUST NOT depend on
  the agent being well-behaved"). A bad-faith or careless model can ignore
  a Hermes-style nudge; it cannot skip a lawkeeper pre-commit hook. Copying
  Hermes's verification model — or forking Hermes wholesale — would be a
  regression on the one thing lawkeeper was actually built to guarantee.

**If this gets picked back up:** steal the memory-provider *pattern* (the
interface shape and the prefetch-before-turn injection idea), not the
verification philosophy. A straight fork of Hermes solves a different
problem than the one lawkeeper was founded to solve — Hermes is a
single-agent CLI tool with no concept of multi-agent branch/merge
governance (lawkeeper's Law 15/16), and its soft-nudge verification is
weaker exactly where lawkeeper needs to be strongest.

**Status as of 2026-08-19:** lawkeeper itself has been shelved/postponed
since early on — very little work has been done on it beyond the
constitution and a handful of checker-script fixes. This is not an active
project right now; revisit this note when that changes.

---

## Hybrid architecture: local-first with first-party remote-compute fallback

**Deferred:** 2026-08-19, by the user, refining [[ai-independence-goal]]
(Claude's memory) after an earlier pass that incorrectly framed this as
"fully offline." Corrected the same day, same conversation.
**Re-check when:** the project reaches real architecture/infrastructure
decisions for an actual product (choosing a hosting setup, picking an
open-weight model to serve, or scoping a first release) — this is a
design note to consult at that point, not a task with its own start
condition.

**The correction:** the tool isn't meant to be offline-only. Most people's
hardware can't run a genuinely capable local model, so the design needs a
remote-compute path too — but that path must be **first-party/self-hosted
by the project itself, never third-party API routing** to another
company's commercial AI service (OpenAI, Anthropic, etc.). The difference,
plainly: routing sends a user's data through two parties — the app, then
someone else's business, bound only by that business's own terms. A
first-party service means the project rents or owns the actual compute and
runs an open-weight model on it directly, so the data never passes through
another company's hands, and the project can make (and mean) a direct
privacy promise instead of inheriting someone else's policy.

**Why the privacy contract is necessary, not conditional:** the user was
explicit that "it's designed that way" doesn't mean anything to a
nontechnical user, who has no way to audit code or verify an offline
claim. The enforceable, unambiguous contract (see the voice-input section
below, and task #58) is what actually protects users — independent of
whether the underlying architecture is technically sound — and it's needed
the moment any remote-compute path exists at all, not deferred until "once
this is a real product." Given the hybrid architecture, that path exists
from the start.

**Shape, roughly:** local inference by default when the user's hardware
supports it; an optional first-party hosted-compute service (the project's
own rented/owned GPU infrastructure, running open-weight models) as a
fallback for underpowered hardware — governed by the same unambiguous,
litigation-friendly privacy terms described below, applied to whatever data
that remote path actually touches.

---

## Context-aware, fully offline voice input with unambiguous privacy guarantees

**Deferred:** 2026-08-19, by the user, as a reflection on voice-recognition
quality during this session — "something that lawkeeper should have."
**Re-check when:** idea-organizer reaches its Phase 0 voice-transcription
spike (`C:\Users\Admin\.claude\plans\golden-puzzling-raccoon.md`) — that's
the concrete, already-planned milestone this piggybacks on; check that
plan's status directly rather than guessing whether it's been reached.

**The problem, as described:** current voice recognition (a) doesn't use
conversation/project context to disambiguate what was actually said, and
(b) sends audio to a remote server, which the user considers a real,
principled problem, not just an accuracy nuisance. Live evidence from
tonight's session: "law keeper" → lawkeeper, "Deep sick" → Devin/opencode,
"Open calls"/"Open code" → opencode — all corrected only because Claude
cross-checked against real project context (repo names, task history, who
was being discussed), not because the transcription itself improved.

**Technical shape of a fix (fully achievable offline):**
`whisper.cpp`/`whisper-rs` for the acoustic transcription (already the
standard local STT engine — see the idea-organizer plan's Phase 0 voice
spike, `C:\Users\Admin\.claude\plans\golden-puzzling-raccoon.md`, which
already scopes this), paired with a rescoring/disambiguation pass against a
known project vocabulary (repo names, agent names, task terms) pulled from
the same kind of files read throughout this session. Whisper supports
vocabulary-biasing / initial-prompt hints natively — nothing about
context-aware correction requires a network round-trip.

**On the privacy/legal angle — corrected 2026-08-19, same conversation:**
voice transcription specifically can plausibly stay fully local even in the
hybrid architecture described in the section above (whisper is cheap enough
to always run on-device, even when the broader reasoning/LLM step uses the
first-party remote-compute fallback) — that's a real, worth-preserving
design property, not just an aspiration. But the enforceable contract is
NOT conditional on that holding, and is not something to defer "until it's
a real product": a nontechnical user can't verify "voice stays local" by
inspecting code, so the legible, unambiguous promise is what actually
protects them regardless of the technical design's soundness. It should
NOT be written as vague "we take your privacy seriously" boilerplate full
of hedges and carve-outs — specific and unambiguous enough that any actual
breach would be trivially provable and legally indefensible, a contract a
user could confidently sue over and win. Concrete instruction for task #58
(the Bookchin-inspired company-structure/manifesto doc) whenever it gets
written.

**This is not only a lawkeeper idea** — it directly sharpens the
already-planned idea-organizer app's Phase 0 voice-transcription spike
(see the plan file above). Treat the two as the same underlying
requirement, not separate efforts.

## [NEW 2026-08-20] Law 23 mechanical enforcement (Layers 1+2, in progress now)

Direct follow-up to the Law 23 incident (orbital-study evolution loop
scored a text card as a good "game"). Three-layer plan, agreed with the
user: (1) `Human-check:` required commit-message field for human-facing
paths, mechanically enforced like the existing `Tests:`/`Verification:`
fields; (2) ground `vision_review.py`'s quality prompt in the literal
request text instead of an abstract score; (3) a surfacing tool for
periodic independent spot-checks (design, not build, pending a real
decision on how independent it needs to be). Layers 1+2 approved and
being built now, in this session. Layer 3 explicitly not started.

**Re-check when:** Layers 1+2 land (should be this session); revisit
Layer 3's design once there's real `Human-check:` data in git history to
build the surfacing tool against.

## [NEW 2026-08-20] Governance mechanism audit — full scope, not yet started

Full scoping doc: `docs/RESEARCH_governance_mechanism_audit.md`. The
bigger ask behind the Law 23 fix: audit whether the whole governance
system (constitution prose + hooks/checker code + adaptive memory
mechanisms) actually works, empirically, across every repo where it's
applicable — using a controlled-comparison methodology (varied rule-set
branches, comparable-not-identical tasks) rather than just re-reading the
code. Explicitly bigger than Law 23's own fix and not scoped to start
tonight.

**Re-check when:** a multi-hour unattended window is available for real
parallel-branch comparisons (per the scoping doc's own note), or before
the next major governance change is proposed.

## [NEW 2026-08-20] Roll out scripts/blockers.py more broadly

**Deferred:** built and wired into consensus_review.py's one concrete
case (claude-CLI-auth-not-available) as the first real usage, 2026-08-20.
Explicitly not rolled out further per the user's own instruction not to
get sidetracked ("continue with your work... just make a note of this").

**Context:** structured blocker reporting (BLOCKERS.md, `report_blocker()`)
-- explicit user requirement that a missing API key/program/hardware must
always be reported as a concrete, actionable note (what's missing, why,
how to fix), never as "not possible." Real precedents already existed
before the module (the laptop's SDXL/GPU report, consensus_review.py's
own claude-auth case) -- this generalizes the pattern into one place.

**Re-check when:** the next time any script hits a real "needs X to
proceed" situation -- use `report_blocker()` there instead of inventing
new ad hoc wording, and consider whether older scripts with existing
"can't do X" messages (e.g. get_api_key() in ai_review.py) should be
retrofitted to use it too.

## [NEW 2026-08-20] Wire real mechanical checks into the science panel

**Deferred:** the "science" panel in `scripts/consensus_review.py` was
built 2026-08-20 to judge what genuinely needs judgment (methodological
soundness, reasonable interpretation, source quality) -- explicit user
principle: mechanically enforce everything that CAN be hardcoded, don't
make an LLM panel guess at things a real tool checks reliably. Two real,
identified mechanical pieces not wired in yet:
1. **Citation existence/accuracy** -- `sciwrite-lint`
   (github.com/authentic-research-partners/sciwrite-lint, arXiv:2604.08501)
   is a real, open-source, local-first tool (single consumer GPU,
   open-weight models) that checks reference existence, retraction
   status, and whether a citation actually supports the claim attached to
   it. The panel's checklist item 6 (citation support) should receive
   this tool's real output as evidence, not have an LLM guess from
   parametric memory.
2. **P-hacking detection** -- real, semi-mechanical signals exist
   (multiple-comparison counts, pre-registration cross-checks) that
   checklist item 2 currently asks the LLM panel to judge from text
   alone, a known, real limitation of the current implementation.

**Re-check when:** the peer-review benchmark (the user's real long-term
goal for this whole automated-research track) is revisited with enough
time to actually clone/evaluate sciwrite-lint, not just reference it.
