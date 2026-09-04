# Roadmap

Written 2026-08-20, at the user's request, once the project had grown from
a single repo into an overlapping multi-repo ecosystem and needed an actual
plan rather than ad hoc priority calls each session. Living document —
update it when priorities genuinely change, not on every task completion
(same rule as `docs/PROJECT_GOALS.md`, which holds the *why*; this holds
the *what, in what order*).

---

## The ecosystem this has to account for

Four repos, not independent projects sharing a folder — real relationships:

- **lawkeeper** (this repo): the governance/harness layer. Laws (git hooks,
  self-audit, now a memory-provider) meant to work for *any* project, not
  just this one.
- **Windwright**: the primary real-world application (instrument design)
  *and* lawkeeper's proving ground — most Laws were discovered and hardened
  here first, against a real, messy, multi-agent codebase, then generalized
  back into lawkeeper. This relationship should stay explicit: Windwright
  is where lawkeeper gets tested against reality, not a separate concern.
- **falcun**: the evolutionary methodology engine (population / fitness /
  selection / mutation) as a reusable core, applied to more than one
  domain already (code-bug-hunting, and now the failure-pattern corpus
  itself — see `docs/FUTURE_DIRECTIONS.md`). Relationship to lawkeeper:
  falcun could eventually *evolve* governance rules/checkers, not just
  execute lawkeeper's hand-written ones — the corpus-mining work started
  tonight is the first real link between the two.
  A future direction discussed tonight is deliberately **not** scheduled
  here yet: pointing Falcun-style evolution at lawkeeper's own governed
  test suites, using each test's Law-18 theory card (`oracle`,
  `acceptance`, `blind_spot`) as ground truth so a candidate isn't just
  scored on "tests pass" but on whether it actually explains real,
  documented failures. Genuinely interesting, genuinely not scoped —
  **Re-check when:** the memory-provider work above has a second real
  consumer (see Phase 1) and there's a concrete "what would the fitness
  function even score against" answer, not before.
- **orbital-study**: mostly independent — a separate creative/evolutionary
  project (game content) that doesn't share lawkeeper's governance
  infrastructure the same way the other three do. Worth remembering it's
  the outlier here so it doesn't get force-fit into decisions made for the
  other three.

The long-term shape this is heading toward (explicitly a **long-term**
goal per the user, not a near-term commitment): lawkeeper's laws,
checkers, and now memory-provider become a **plugin architecture** — an
agentic coding platform that keeps *other* agents compliant and
coordinated, usable by non-coders doing "vibe coding," with Windwright/
falcun/orbital-study as the first three real (not hypothetical) case
studies for whether the plugin model actually generalizes. This is the
frame for everything below, not a phase in itself.

---

## Phase 0 — testable tonight

The user asked for something testable as soon as possible, not just
passing tests. This session's memory-provider work
(`src/guardrail/memory/`, commit `a651f9d`) is real but currently only
reachable by importing it in Python — there's no way to just *try* it.
Fixing that is Phase 0, immediately after this roadmap: a tiny CLI
(`scripts/memory_query.py "some question"`) that runs
`FailurePatternMemoryProvider.prefetch()` against the real corpus and
prints the results. Minutes of work, and it turns tonight's abstract
"MemoryProvider adopted" into something the user can literally run and
see respond to a real question.

## Phase 1 — near term (next real session on lawkeeper)

- A second concrete `MemoryProvider` consumer beyond the standalone CLI —
  e.g., wiring `prefetch()` into an actual agent workflow (a pre-turn hook
  in a dispatched session, the way Hermes uses it), not just a demo
  script. This is what makes the falcun-evolves-checkers idea above
  scoped enough to revisit.
- Task-planning capabilities (explicitly requested tonight): a real
  structure for "here's a list of tasks, move through them, report as you
  go" — the claim/release protocol added tonight (`TEAM_PROTOCOL.md`,
  falcun commit `53c7e1e`) is the coordination half of this; the planning/
  queue half doesn't exist yet.
- Adaptive mechanisms — "it should learn from you" (the user's words
  tonight). Directly overlaps `docs/PROJECT_GOALS.md`'s existing
  "adaptive-assistant vision" section (task #93/#94) — don't build a
  second, competing version of this; extend that one.

## Phase 2 — mid term

- Study Hermes Agent further (partially done tonight — the memory-provider
  comparison) and DeepSeek (raised tonight, not yet started) specifically
  for what each does well that a plugin-based architecture could adopt or
  should deliberately avoid, same discipline as the Hermes comparison
  (read the source, not marketing copy; name what's adopted and what
  isn't, and why).
- Begin the plugin-architecture design in earnest, informed by Phase 1's
  real second consumer and by Windwright's actual governance experience,
  not designed in the abstract first.

## Renaming lawkeeper — flagged, deliberately not scheduled yet

The user raised this tonight: "lawkeeper" isn't a good name, and it should
change — but explicitly acknowledged as risky and needing real planning,
not a quick find-and-replace.

**Why it's actually risky, not just annoying:** the name is load-bearing
in more places than the repo name — the GitHub repo itself, cross-repo
references from Windwright/falcun/orbital-study's own docs and commit
messages, the constitution's and failure-log's own internal self-
references, this session's own `TEAM_PROTOCOL.md` posts already on record
in Discussion #23, and (per `docs/PROJECT_GOALS.md`) the eventual public-
facing product identity if the plugin-platform vision ships. A rename done
carelessly breaks links and creates exactly the kind of "which repo is
canonical now" confusion Law 15 exists to prevent.

**Re-check when:** Phase 1 is underway (there's a second real
MemoryProvider consumer) — renaming a project that's still finding its
shape wastes the rename; renaming one with real, working parts is worth
doing once, properly, with a migration plan (old name kept as an alias/
redirect where it matters, a single coordinated update across all four
repos' cross-references, not a silent one-repo change).

**Not a task for right now:** collecting name candidates. When this is
actually scheduled, that's a separate, smaller planning pass.

---

## What's deliberately not in this roadmap

`docs/FUTURE_DIRECTIONS.md` still holds items with their own
`Re-check when:` triggers (the hybrid local/remote architecture, offline
voice input) that aren't restated here — this roadmap sequences lawkeeper-
specific work; that file remains the source of truth for deferred ideas
generally. Don't let the existence of this roadmap become a second place
those trigger conditions have to be kept in sync — this file references
them, it doesn't duplicate them (Law 3).
