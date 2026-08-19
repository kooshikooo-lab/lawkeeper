---
name: hermes-comparison-deferred
description: Adopting Hermes Agent's memory-provider pattern (not its verification model) for lawkeeper is a deliberately deferred future direction, not active work.
metadata:
  type: project
---

The user explicitly deferred (2026-08-19) adopting something closer to
Hermes Agent — possibly even forking it — for lawkeeper's governance/harness
design. Their framing: "a direction worth considering, but not now... it's
outside the scope of what we're doing now." They asked for it to be
cataloged somewhere that can't just be overlooked, since a roadmap doc alone
is "seldom read."

**Where this lives, deliberately in multiple places so it actually
resurfaces:** this shared-memory entry, task #85 in the session task
tracker, and `lawkeeper/docs/FUTURE_DIRECTIONS.md` — the durable written
record with full technical detail.

**The substance, briefly** (full detail in the doc above): Hermes's
pluggable `MemoryProvider` architecture (`agent/memory_provider.py`) —
relevance-keyed recall injected before every turn via `prefetch()` — is a
real, adoptable pattern; this shared-memory system itself is a step in that
direction, though simpler (git-file-backed rather than a live
prefetch-before-turn hook). Hermes's verification step, though, is a soft
in-context prompt nudge (`agent/verify_hooks.py`) with nothing mechanically
enforcing it — the opposite of lawkeeper's founding premise that guards
must not depend on the model being well-behaved (Law 16). Any future
adoption should take the memory pattern, not the verification philosophy,
and should not be a straight fork of Hermes.

Note also (from direct inspection, not assumption): Hermes's `mcp_serve.py`
exposes messaging/conversation platforms over MCP, NOT its memory system —
there is no existing "just connect via MCP" shortcut to Hermes's memory.

Related: [[falcun-broader-vision]] (a separate but similarly-scoped
"reusable system beyond one project" idea, for the evolutionary
methodology rather than governance). Lawkeeper itself has been
shelved/postponed since early on — this is revisiting a paused vision, not
redirecting active work.
