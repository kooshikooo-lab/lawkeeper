---
name: falcun-broader-vision
description: Falcun's current code (evolving critic/proposer prompts to find code bugs) is only one narrow instance of a much broader intended vision.
metadata:
  type: project
---

The falcun repo's current implementation — a population of "rulesets" (critic/proposer prompt pairs) evolving over generations to find and fix code bugs — is **one concrete implementation, not the whole project**.

The user's actual, broader vision for Falcun (stated directly, 2026-08-19): something closer to an **"AI factory"** combined with **automated research and discovery**. "Evolution of rulesets" — population, scoring, breeding winners, mutation — is meant to be a **core, reusable methodology** applied broadly across many domains, not a project scoped only to code-bug-hunting. The user described it as "a very broad project with some core methodologies," and corrected an over-narrow description of it as just "an AI that evolves bug-finding prompts."

**Why this matters:** none of this broader scope is derivable from reading the current code — the repo today only implements the narrow bug-hunting instance. Don't describe or scope Falcun work as if bug-hunting is the whole point; treat new Falcun features/hypotheses (F1-F4 from opencode's cross-project research) as instances of the broader evolutionary-methodology platform, and ask the user before assuming a narrow scope when planning new Falcun work.

**How to apply:** when discussing or extending Falcun, frame the core mechanisms (population, fitness, selection, mutation, coevolution) as the reusable part, and the current critic/proposer bug-hunting setup as just today's target domain. If the user brings up applying Falcun's methodology to a new domain, that's consistent with the stated vision, not scope creep.
