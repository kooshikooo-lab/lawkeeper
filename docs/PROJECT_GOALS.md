# Project Goals

The "why" layer above the individual repos — durable, canonical, meant to
be read by a human, not derived from code. Where `FUTURE_DIRECTIONS.md`
holds specific deferred technical ideas, this holds the actual vision
those ideas serve. Update this when the vision itself changes, not on
every task completion.

---

## The core goal: a platform cooperative, not a product

Knowledge and automation as commonly-owned capital — a "virtual nation"
structured legally as a platform cooperative (real precedent: Stocksy
United; the movement is called platform cooperativism, Trebor Scholz).
Universal access to all utilities according to need; contribution
according to ability (compute donation, coding work) — not a
subscription, not pay-to-play. The theoretical basis is Murray Bookchin's
communalism: a "third way" between market capitalism and centralized
state control, built on directly-democratic structures rather than either.

This directly answers a real problem, not an abstract one: open source,
open hardware, and open standards already work as commons that most
people — including capitalists — use without reciprocating. The
contribution-according-to-ability requirement exists specifically to
prevent that extraction pattern here.

**Public-facing framing rule:** state these goals unapologetically, but
never lead with the ideological labels (Bookchin, anarchism,
anticapitalist) — they trigger prejudice before anyone engages with the
substance. Describe the mechanism and its plain benefit instead. Name the
theory accurately in internal documents only.

## Why now, not building toward paid AI forever

The user is anticapitalist and does not intend to keep paying for Claude
Code (or any single commercial AI provider) long-term. The plan: a
local-first open-weight model, with a first-party (never third-party)
remote-compute fallback for people whose hardware can't run one — never
routing through another company's commercial AI service, so the privacy
promise is one the project can actually keep. A harness (lawkeeper) robust
enough to make a less-capable local model still do good work is the
mechanism that makes "not depending on Claude" realistic rather than
aspirational.

## What lawkeeper actually is

Not a generic dev-tooling side project. It's the governance/harness layer
for the whole cooperative structure — laws that are mechanically enforced
where possible (git hooks), not just written down and trusted, because
"guards must not depend on the agent being well-behaved" (Law 16) is true
of AI agents *and* of a system meant to work even with a less-capable
local model. Currently shelved/dormant relative to how central this
actually is — worth reconsidering its priority when there's real bandwidth
for it.

## The adaptive-assistant vision

Both the coding-assistant platform and any organizing tools should help
the user fulfill *their* goals — accounting for personality, knowledge
level, and how they actually speak — not a one-size-fits-all interaction
style. Explicitly, not incidentally: ADHD-aware. Should work fine for
neurotypical users, but should notice and adapt to a specific person's
working style, and proactively suggest systems for organizing both their
project and their mind. The session-mining skill (task #93) is one small,
concrete instance of this; the fuller vision (task #94) is long-term.

This is also the direct answer to a real, lived frustration: Claude
Desktop's own Projects/home organization feature wasn't built to notice
disorganization and adapt — it's a generic tool. A purpose-built one,
especially with AI doing the adaptive work, can genuinely do better for
someone without excellent executive function. That's not overconfidence,
it's the correct diagnosis of why a generic tool keeps failing here.

## Falcun's real scope

Not "an AI that evolves bug-finding prompts." The evolutionary methodology
— population, fitness, selection, mutation — is meant to be a reusable
core methodology applied broadly, with code-bug-hunting as only today's
target domain. Already extended once, concretely: pointing the same
approach at the failure-pattern corpus mined from `AI_FAILURE_PATTERNS.md`
is the natural next-level version of that mining tool (see
`FUTURE_DIRECTIONS.md`).

## Status snapshot

Living document — see `ROADMAP.md` (repo root) for the current priority
order and phased plan, kept current rather than duplicated here. (This
line previously pointed at "the published dashboard," which doesn't exist
anywhere in this repo -- corrected 2026-08-20 rather than left stale.)
