# Adaptive Interface Plan — UI/feature research and proposal

Written 2026-08-20 per user direction: research what exists for
adapting an AI assistant's communication style to an individual user
(jargon level, explanation depth, ADHD-aware output), and propose
concrete features for lawkeeper. Extends `docs/PROJECT_GOALS.md`'s
"adaptive-assistant vision" section (task #93/#94) from a one-line goal
into an actual plan — read that section first, this doesn't repeat it.

---

## Research (real citations, not assumed)

**Expertise/jargon adaptation actually works, and has a known cheap
technique.** "Explain Less, Understand More: Jargon Detection via
Personalized Parameter-Efficient Fine-tuning"
([arXiv:2505.16227](https://arxiv.org/html/2505.16227)) fine-tunes a small
model per-user with LoRA (rank 16) on that user's own familiarity
judgments — supervised where labels exist, self-supervised on the user's
own writing otherwise, combined with background-aware prompting (their
subfield, publication history, similar users' judgments via BM25
retrieval). Result: 77.9 F1, beating GPT-4-with-prompting by 21.4%, using
only 10% of the annotation a fully-supervised approach would need. The
concrete takeaway for lawkeeper: full fine-tuning isn't necessary — a
lightweight, incrementally-updated per-user profile (what terms this
person already knows, built from their own actual usage) beats a generic
"explain simply" instruction.

**A companion paper on the tradeoff itself**: "Towards Balancing
Preference and Performance through Adaptive Personalized Explainability"
([arXiv:2504.13856](https://arxiv.org/pdf/2504.13856)) — the real risk
this names is over-fitting to *stated* preference at the cost of actual
task performance; adaptation needs to track outcomes, not just what a
user says they want. Relevant to lawkeeper: "explain jargon, don't dumb
down" (the user's own standing preference, see the memory file of that
name) is exactly this — a stated preference for the *floor* to stay high
even while the *style* adapts.

**ADHD-specific output shaping has a concrete, already-implemented
precedent**: `i-have-adhd` ([github.com/ayghri/i-have-adhd](https://github.com/ayghri/i-have-adhd)),
a real GitHub skill for AI programming assistants. Ten specific rules,
directly reusable as a starting checklist:
1. Lead with the next action, not the explanation.
2. Number multi-step tasks.
3. End with one concrete next step (no open loops).
4. Suppress tangents.
5. Restate current state every turn (context isn't assumed carried).
6. Specific time estimates ("12 minutes," never "a bit").
7. Make wins visible (progress is shown, not just implied).
8. State errors matter-of-factly, not softened.
9. Cap lists at 5 items.
10. No preamble, no recap, no closers — strip filler entirely.
The core mechanism across all ten: **information hierarchy reordered so
the actionable instruction comes first**, supporting detail after, not
before.

**Broader accessibility research confirms the mechanism, not just the
anecdote**: a cognitive-accessibility analysis
([ACM SIGACCESS 2024](https://dl.acm.org/doi/10.1145/3663547.3749831))
frames this as "concise, high-impact responses" being an accessibility
requirement, not a style preference, for users whose executive function
or sustained attention differs from the default assumption baked into
most AI output. A related HCI study on IDEs specifically
([arXiv:2506.10598](https://arxiv.org/pdf/2506.10598)) found the same
pattern in a dev-tooling context — directly relevant since lawkeeper *is*
dev tooling, not a generic assistant.

## What this means for lawkeeper, concretely

### 1. A UserPreferenceProvider — the second real consumer of tonight's
   MemoryProvider work

`src/guardrail/memory/` (commit `a651f9d`, earlier tonight) already has
the right abstraction: `initialize()` / `prefetch(query)` /
`sync_turn()` / `shutdown()`. A `UserPreferenceProvider` implementing that
same interface, tracking:
- **Vocabulary/jargon familiarity** — built incrementally from what terms
  the user has already used correctly themselves (the arXiv:2505.16227
  technique's cheap version: track usage, not a fine-tuned model, since
  lawkeeper doesn't need per-user model weights for this).
- **Explanation-style preference** — analogy-first vs. definition-first,
  captured from corrections ("that's a whole lot of jargon," said tonight,
  is exactly this signal — see the transcript, that correction should
  have been *recorded*, not just responded to in the moment).
- **ADHD-mode toggle** — on/off, or per-session, applying the 10-rule
  checklist above when active.

This is a genuinely new consumer, not a restatement of the
failure-pattern one — different data, same lifecycle, same interface,
Law 3-compliant reuse.

### 2. `sync_turn()` is where this actually closes the loop

The base `MemoryProvider` class already has this hook, currently unused
by the one existing implementation (`FailurePatternMemoryProvider` is
read-only, correctly — it shouldn't be writing to a shared corpus every
turn). A `UserPreferenceProvider` is the natural first implementation
that actually *uses* `sync_turn(query, response)`: after a turn where the
user corrects the explanation level (too much jargon, too dumbed-down,
too slow to get to the point), that's a write, not just a read. This is
also a direct, concrete instance of Law 21 (a capability with no consumer
is a bug) being obeyed proactively this time, not found broken after the
fact.

### 3. Interface surface — what a person actually sees

Not just an invisible backend adjustment. Two concrete UI elements worth
building, matching the "user's memory files" pattern already established
(this session's own memory system, `explain-jargon-not-dumbed-down.md`
etc.) but visible and editable, not just inferred silently:
- A **visible, editable preference summary** — "here's what I've learned
  about how you like things explained" — reviewable and correctable
  directly, not just something happening invisibly. This matters
  specifically because arXiv:2504.13856's finding (over-fitting to
  *stated* preference over actual outcomes) is a real risk lawkeeper
  should design against from the start, not discover later — an editable,
  visible model is auditable in a way a silent one isn't.
- An **ADHD-mode toggle that's a real, first-class setting**, not a
  buried config flag — applying the 10-rule checklist when on. Off by
  default (per-user preference is exactly the right place to make this
  decision, not a global default).

## Open questions — not decided here

- Where does preference data actually live — same `AI_FAILURE_PATTERNS.md`-
  style durable file, or a separate mechanism? A single flat file risks
  becoming exactly the kind of thing Law 21 warns about (written, never
  actually read back into a live decision) if it isn't wired into
  `prefetch()` from day one.
- Should ADHD-mode formatting apply to *lawkeeper's own agent output*
  only, or is this meant to generalize to the broader platform-cooperative
  vision (`PROJECT_GOALS.md`)? Scope call, not a technical one — flagging
  per tonight's earlier discussion about which decisions need a real
  check-in.
- Relationship to the session-mining skill (task #93) and the fuller
  adaptive-assistant vision (task #94) — this document is a piece of both,
  not a replacement for either; worth explicitly reconciling scope before
  building rather than after.
