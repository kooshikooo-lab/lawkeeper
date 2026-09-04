# Research: automated scientific discovery & invention (2026 state of the art)

Real research pass, requested by the user as a long-term goal (task #100):
"research on automated science and automated technological discovery and
invention and plan implementation of this using all available knowledge,
trying and establishing this as a long-term goal." Framed within the same
open-commons ethos as the platform-cooperative vision in `PROJECT_GOALS.md`
— open science/open hardware, not a closed proprietary system.

All claims below are sourced; distinguish VERIFIED (a specific, checkable
result cited to a real source) from general-field-description (still
sourced, but a synthesis claim rather than one verifiable fact).

---

## 1. Two distinct fields, both real, both active in 2026

**Self-driving laboratories (SDLs):** physical automation + AI in a real
lab — robots + instruments + AI closing the loop on hypothesis, experiment
design, execution, and analysis with minimal human input. Real, deployed
examples: Argonne National Laboratory's automated materials lab (robots
synthesizing new conductive polymers), Korea's national SDL initiatives,
robotic coin-cell assembly and autonomous nanoparticle synthesis in
materials science. **Real limitation, stated plainly by the field itself:**
high overhead, complex engineering, not remotely "everywhere overnight" —
this is genuine infrastructure-heavy work, not a software-only problem.
[Self-driving labs in Korea (Digital Discovery, RSC)](https://pubs.rsc.org/en/content/articlehtml/2026/dd/d6dd00024j),
[Argonne Autonomous Discovery](https://www.anl.gov/autonomous-discovery),
[Forbes: AI Is Becoming A Scientist](https://www.forbes.com/sites/bernardmarr/2026/04/17/ai-is-becoming-a-scientist-how-self-driving-labs-will-accelerate-discovery/)

**LLM + evolutionary-search code/algorithm discovery:** this is the field
that actually matches Falcun's own architecture, and it has real, verified
results as of 2026, not just promise:

- **AlphaEvolve (Google DeepMind, 2025-2026):** LLM-guided evolutionary
  search over code. **VERIFIED, independently reproducible result:**
  discovered a 4x4 matrix multiplication algorithm using 48 scalar
  multiplications, beating Strassen's 49-multiplication algorithm — the
  first improvement on that specific problem in 56 years. Matched or beat
  known human solutions on 95% of a 67-problem math benchmark. A third
  party has independently verified the discovered algorithm actually works
  as claimed (not just trusted DeepMind's report).
  [DeepMind blog](https://deepmind.google/blog/alphaevolve-a-gemini-powered-coding-agent-for-designing-advanced-algorithms/),
  [independent verification repo](https://github.com/PhialsBasement/AlphaEvolve-MatrixMul-Verification),
  [MIT Technology Review coverage](https://www.technologyreview.com/2025/05/14/1116438/google-deepminds-new-ai-uses-large-language-models-to-crack-real-world-problems/)
- **FunSearch (DeepMind, 2023, the direct predecessor to AlphaEvolve):**
  first system to use an LLM as a *mutation operator* inside an
  evolutionary loop to discover new, provably-correct results on open
  math problems — the architectural pattern Falcun already implements
  (population, fitness, selection, mutation) independently arrived at the
  same core design a major lab uses for real discovery work.
- **CodeEvolve (2026, open-source):** an open framework combining LLMs
  with evolutionary search for algorithmic discovery/optimization — real
  evidence this pattern is becoming a genuine open, replicable method, not
  DeepMind-proprietary.
  [arXiv:2510.14150](https://arxiv.org/html/2510.14150v3)
- **MOOSE-Chem:** evolutionary search over *hypotheses themselves*
  (mutation/recombination on hypothesis populations, fitness = a quality
  evaluator) for chemistry discovery — the same methodology one level up
  from code, applied to scientific hypotheses directly. Directly relevant
  to "point Falcun at hypothesis generation," not just code.

## 2. What this confirms about Falcun's own approach

Falcun's core methodology — population, fitness, selection, mutation,
applied first to code-bug-hunting — is not a bespoke, isolated idea. It is
architecturally the same pattern as FunSearch/AlphaEvolve/CodeEvolve, a
line of research with a real, independently-verified, record-breaking
result (the matrix multiplication discovery) behind it. This is a genuine
confirmation of `PROJECT_GOALS.md`'s existing claim that Falcun's
methodology is meant to be reusable beyond its current target domain, not
an aspirational reach — the reference architecture already exists and
already works in production research settings.

**Falcun's current gap relative to AlphaEvolve/FunSearch, honestly:** those
systems succeed specifically because they pair evolutionary search with a
**cheap, automatic, unambiguous fitness function** (does the discovered
matrix algorithm actually multiply correctly with fewer steps? — mechanically
checkable, no human judgment call). Falcun's bug-hunting domain has this
property. A hypothetical extension to something like "invent a better
woodwind bore-optimization heuristic" would also have it (TMM/OpenWind
give a mechanical fitness score, exactly like the module-size-threshold
and optimizer-competition audits already run tonight). An extension to
something like "generate new scientific hypotheses" would **not**
automatically have it — MOOSE-Chem's fitness function for a hypothesis is
a much harder, less mechanically verifiable thing than "count the
multiplications." This is the real constraint to design around, not a
reason to avoid the extension.

## 3. Concrete recommendation

Extend Falcun toward automated discovery in order of how mechanically
verifiable the fitness function is, cheapest/most-certain first:

1. **Already planned** (`FUTURE_DIRECTIONS.md`): point Falcun at the mined
   `AI_FAILURE_PATTERNS.md` corpus — fitness is mechanically checkable
   (does a proposed governance/process change reduce a real, measured
   failure-pattern recurrence rate).
2. **New, natural next step given tonight's own work:** point Falcun at
   Windwright's own debatable-architecture-decision candidates (the
   optimizer-algorithm comparison run tonight, `docs/EXPERIMENT_optimizer_competition.md`,
   is literally a one-off manual version of exactly what an AlphaEvolve-
   style loop would do continuously) — a mechanical fitness function
   already exists (RMS cents, real timing), so this is the cheapest real
   extension to build, not a new research question.
3. **Longer-term, harder, real:** hypothesis-generation-style extensions
   (MOOSE-Chem's pattern) for domains without an automatic fitness
   function — these need a designed evaluator (human-in-the-loop scoring,
   or a proxy metric known to correlate with real quality) before Falcun's
   architecture can be pointed at them honestly. Don't skip this step and
   claim mechanical verification where none exists — that would violate
   Law 18/20's own discipline (a test/fitness signal that doesn't actually
   discriminate is worse than none).

## 4. Framing (per `PROJECT_GOALS.md`'s public-facing rule)

This is squarely inside the existing open-commons framing: automated
discovery tooling built and shared openly, not a closed proprietary
system — the same posture as open source/open hardware/open standards
already established for the platform-cooperative vision.
