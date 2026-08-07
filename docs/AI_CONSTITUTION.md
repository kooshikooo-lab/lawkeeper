# AI Constitution

A small, enforceable rule set written in git that every agent and human follows.
Laws are machine-checked (see `scripts/`); a guard that is not enforced is dead.
Non-coders: `lawkeeper init` installs everything below; you only have to follow
the human-facing rules.

## How to change this file
It is protected. A commit touching it MUST contain `GOVERNANCE-UPDATE`.
A human must approve the change (see Law 16).

### Law 1 — Architecture over features
The project's structure and interfaces are decided first; features conform to
them. An agent must not invent architecture — it asks ("Law 10: when uncertain,
stop and ask") instead. Architectural decisions are recorded as ADRs (Law 9).

### Law 2 — No architectural invention
Never silently introduce new patterns, coordinate systems, or data flows. If a
decision needs input, stop and request it in the team channel before coding.

### Law 3 — Never duplicate
Search before writing. Two implementations of the same thing diverge and break.
Every new function/class must be justified by not already existing.

### Law 4 — Concerns stay separated
Geometry, physics, optimization, and presentation do not live in the same module.
Each layer has one responsibility and depends only on the layer below it.

### Law 5 — The optimizer chooses variables; the physics is computed elsewhere
Optimizer/pipeline code never contains domain equations. Physics is computed in
a single source of truth; the optimizer calls it.

### Law 6 — The UI never contains physics
Presentation code never computes results. It formats and displays; it does not
encode physical assumptions.

### Law 7 — One source of truth for every physical quantity
Each physical constant or canonical value lives in exactly one module and is
imported everywhere else. Hardcoded duplicates are a constitutional violation and
are caught by the pre-commit hook.

### Law 8 — One responsibility per module
Modules stay small (<500 lines by default) and focused. Split or record debt.

### Law 9 — Document architectural decisions
Every significant decision affecting architecture, interfaces, or data flow is
an ADR in `docs/ARCHITECTURE_DECISIONS.md`. Silent changes are forbidden.

### Law 10 — When uncertain, stop and ask
Never guess about architecture, coordinate systems, or assumptions. Stop, document
the uncertainty, and request clarification in the team channel.

### Law 11 — Multi-machine coordination protocol
When the project is built by multiple agents/machines, coordination uses a durable
team channel (GitHub Discussion). A real-time channel carries live messages;
the durable channel is for decisions. Machines talk to machines directly, never
through the human as a relay. Unacknowledged messages are re-sent until answered.

### Law 12 — Read before you act
A machine that posts but never reads is as broken as one that never posts. Every
session re-reads the session state, the reminders, and pending team messages
before touching code, and re-checks on a schedule.

### Law 13 — Missing dependencies are bugs
A declared dependency that is not installed is a BUG, same severity as a failing
test. Skips (`importorskip`/`skip`) that mask missing declared software are only
allowed for genuinely optional, undeclared capabilities, and must be justified in
code.

### Law 14 — Audit before you commit
No commit from unverified work. Before every commit: re-read the constitution and
state which laws apply; run the tests covering the change; review the diff
line-by-line; scan for classic silent killers; delete scratch files; and declare
the verification in the commit message (`Tests:` or `Verification:`). The hook is
the floor, not the ceiling.

### Law 15 — Branch governance
A branch name tells any reader what it is and how it lives. There are exactly
four namespaces, each with a fixed lifetime:

1. **Exact namespaces**:
   - `main` — shared trunk. Clean, protected, advanced only by promoting a
     canonical machine branch via reviewed PR. Never worked on directly.
   - `opencode/main/<machine>` — canonical per-machine branch. PERMANENT: never
     force-pushed, never renamed. Deleting a canonical branch requires explicit
     approval from the human user; never on a machine/agent's own initiative.
   - `opencode/<topic>/<machine>` — feature/experiment branch. EPHEMERAL: merge
     into the machine's canonical branch when done, then delete.
   - `merge/<topic>` — cross-machine merge staging. EPHEMERAL: rehearse the
     merge, promote, then delete.
   - Any branch outside a namespace is an orphan — rename or delete. "Stale/old/
     legacy" is never a deletion license; only the namespace decides lifetime.
2. **One upstream per branch**: all work forks a canonical machine branch.
3. **Cross-machine merges go through `merge/` staging** — never directly onto a
   canonical branch untested. Use `merge_gate.py` first.
4. **Promotion to `main` is PR-only and canonical-to-canonical**.
5. **Before deleting any branch, prove its content exists on a canonical branch
   or `main`** (`git merge-base --is-ancestor`).
6. **`origin/HEAD` must point at `main`**.
7. **Announce topology changes** in the team channel.
8. **Canonical branches need human approval to delete** — no delete/rename/
   force-push without the human's explicit prior approval, obtained via the team
   channel.

### Law 16 — The enforcement system must itself be enforced
Agents malfunction: they misunderstand, lose context, act rashly, or ignore. The
guards MUST NOT depend on the agent being well-behaved.

1. **Prevention over trust** — rules are mechanically enforced at the git layer
   (local hooks + CI), not just written down.
2. **Fail safe by default** — deletions, force-pushes, canonical-branch mutation
   are BLOCKED unless explicitly approved (named, scoped overrides).
3. **No single point of trust** — local hooks, server-side CI/branches, and a
   system self-audit verify each other.
4. **System audits itself** — `python scripts/system_audit.py` MUST pass before
   any commit to a canonical branch or `main`: it checks hooks are wired, laws
   parse, baseline current, topology holds, guards import.
5. **The guards have tests** — `tests/test_guard_scripts.py` must pass; a change
   to a guard without a test exercising it is a violation.
6. **Cross-machine merges are gated** — run
   `python scripts/merge_gate.py <base> <head>` first; conflict → rehearse on a
   `merge/<topic>` branch.
7. **Audit result is declared in the commit** (`System: audit PASS/FAIL`).

Violating any law is a constitutional violation. Log failures in
`docs/AI_FAILURE_PATTERNS.md`.
