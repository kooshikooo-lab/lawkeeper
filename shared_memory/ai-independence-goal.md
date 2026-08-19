---
name: ai-independence-goal
description: The user is anticapitalist and does not intend to keep using Claude Code (or other paid commercial AI) long-term; the plan is a local-first open-weight model with a first-party remote-compute fallback, plus a harness robust enough to compensate for lower model capability.
metadata:
  type: user
---

The user is pleased with how Claude Code works but does not intend to keep
using it long-term — they're anticapitalist and don't want to keep giving
money to large corporations, Anthropic included. Stated 2026-08-19.

**The plan, in their own framing:** once they have enough local compute to
run a very capable open-source/open-weight model, that model needs either
(a) capabilities close to Claude's own, or (b) "some system in place that
would keep the process going even if I couldn't run a capable enough
model."

**Why this matters for prioritization, not just as background:** path (a)
is what the existing local/distributed-compute work is actually for — the
Dask worker fleet, dual-boot Linux planning, multi-GPU JAX research
(tasks #62, #69, #70) — even though it wasn't originally framed as
"replace Claude Code," it's the same compute buildout. Path (b) is
lawkeeper's actual founding purpose: "a governance system good enough to
make bad models do good work" (see [[hermes-comparison-deferred]] for the
closest existing comparison). Lawkeeper has been shelved/postponed since
early on with very little work done on it — but if this is the real goal,
its priority probably deserves reconsidering relative to that dormancy.
Not a directive to resume it unprompted; just don't treat it as a minor
side-project if it comes up again.

**Correction, same day:** not offline-only. The user clarified the design
needs a remote-compute fallback too, since most people's hardware can't run
a capable local model — but it must be first-party/self-hosted by the
project itself, never third-party API routing to another company's
commercial service (the difference: routing puts a second business in the
data path, bound only by its own terms; first-party means the project's own
infrastructure, so it can make a direct, meant promise about data handling).
And the privacy contract governing that path isn't conditional on "once
it's a real product" — a nontechnical user can't verify an offline/local
claim by inspecting code, so the enforceable promise is what protects them
regardless of the architecture's technical soundness. Full detail in
`lawkeeper/docs/FUTURE_DIRECTIONS.md` ("Hybrid architecture" section).

See also [[voice-input-offline-privacy]] — the same data-sovereignty stance
applied specifically to voice input rather than the AI model itself.

**How to apply going forward:** don't default to paid/cloud-API solutions
without at least noting a local/open alternative when one is realistically
viable — this isn't a hard rule against using cloud APIs (OpenRouter,
Ollama-cloud, etc. have been used pragmatically, e.g. for Hermes testing),
just awareness that the user's actual long-term direction is away from
dependency on any one paid provider, Claude included. Don't be defensive or
sentimental about this when it comes up — the user was direct about it,
engage with it the same way.
