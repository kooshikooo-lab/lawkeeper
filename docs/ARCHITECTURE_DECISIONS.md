# Architecture Decisions Log

Format: [ADR-00N] Title — Date — Status

- [ADR-001] Constitution-as-code at the repo root, enforced by git hooks + CI — adopted
- [ADR-002] Three enforcement layers: local hooks, server-side CI, self-audit (Law 16) — adopted
- [ADR-003] Canonical branches are permanent; deletion requires human approval (Law 15) — adopted
- [ADR-004] Cross-machine merges rehearsed on `merge/<topic>` staging first (Law 15.3) — adopted
- [ADR-005] Guard scripts have dedicated tests (Law 16.5); regression caught when the law loader silently fell back to a hardcoded list — adopted
- [ADR-006] Internal reasoning toggle: `show_internal_reasoning` + `reasoning_log` in `.guardrail.json`, surfaced via `lawkeeper reasoning` and `lawkeeper run --show-reasoning/--hide-reasoning`; default hidden — adopted

(Add your own decisions here; one short paragraph each: context, decision, consequence.)

## ADR-006 context/decision/consequence
A model's internal reasoning (chain-of-thought) is useful for audit and cross-
machine handoff but noisy for clean project artifacts. Decision: keep the toggle
off by default (no reasoning written unless opted in per repo), store the flag in
`.guardrail.json` so it is shared across desktop/laptop, and expose two CLI
surfaces: `lawkeeper reasoning [TEXT]` to record/query the toggle, and
`run --show-reasoning/--hide-reasoning` to override it for a single check.
Consequence: reasoning capture is explicit, version-controlled, and never leaks
into a repo that hasn't opted in.
