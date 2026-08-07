# Architecture Decisions Log

Format: [ADR-00N] Title — Date — Status

- [ADR-001] Constitution-as-code at the repo root, enforced by git hooks + CI — adopted
- [ADR-002] Three enforcement layers: local hooks, server-side CI, self-audit (Law 16) — adopted
- [ADR-003] Canonical branches are permanent; deletion requires human approval (Law 15) — adopted
- [ADR-004] Cross-machine merges rehearsed on `merge/<topic>` staging first (Law 15.3) — adopted
- [ADR-005] Guard scripts have dedicated tests (Law 16.5); regression caught when the law loader silently fell back to a hardcoded list — adopted
- [ADR-006] Executor layer: framework-agnostic `Task`/`Executor`/`ExecutorResult` protocol; backends (subprocess, OpenAI-compatible) behind one interface; explicit `ExecutorResult`→`CheckResult` adapter; wired via `lawkeeper run --executor`. Context: agentic + vibe-coded tasks need a governed execution path decoupled from any single agent. Consequence: callers never depend on a backend; new backends plug in without touching core. Contract: `docs/EXECUTOR_CONTRACT.md` — adopted

(Add your own decisions here; one short paragraph each: context, decision, consequence.)
