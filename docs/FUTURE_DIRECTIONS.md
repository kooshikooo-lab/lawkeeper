# Future Directions

Ideas that are explicitly out of scope right now but deliberately not lost.
Unlike the roadmap sections of other docs, this file exists specifically to
hold things that were *decided to be deferred*, with enough context that
picking one back up doesn't require re-deriving why it mattered. See also
task #85 in the session tracker and the `hermes-comparison-deferred` memory
note (Claude's persistent memory) — both point back here.

---

## Adopt Hermes's memory-provider pattern (not its verification model)

**Deferred:** 2026-08-19, by the user. Explicitly "a direction worth
considering, but not now."

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
