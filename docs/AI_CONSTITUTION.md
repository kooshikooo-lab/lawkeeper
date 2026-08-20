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
**Same-machine exception**: when agents are confirmed co-located on one host with
a shared filesystem, prefer reading the other agent's actual log/state files
directly over posting to the channel and waiting for a reply — reserve the
channel for genuinely separate machines. Any real-time transport under the
durable channel (e.g. a peer-to-peer tool) is optional acceleration, never a
dependency: its absence must never block work or require pausing.

### Law 12 — Read before you act
A machine that posts but never reads is as broken as one that never posts. Every
session re-reads the session state, the reminders, and pending team messages
before touching code, and re-checks on a schedule. This includes
`docs/FUTURE_DIRECTIONS.md`: a deferred item with no re-check trigger silently
becomes permanent, which is a failure (2026-08-20). Every entry there carries a
`Re-check when:` condition; check it against current reality whenever the file
is read for any reason, not only when hunting for new work.

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

### Law 17 — Work in order of safety, not order of approval
Halting is the expensive failure. A machine that waits for approval for steps it
could safely do itself wastes the whole session. Work MUST be ordered by what is
safe and independent, not by what requires permission. Approval gates only the
steps that truly need them.

1. **Do the safe work first**. When a task has multiple steps, execute every step
   that is local, reversible, and unblocked BEFORE any step that requires another
   machine, a human, or a shared-state change. Never let a downstream approval
   gate stall upstream work that does not depend on it.
2. **Local is never blocked**. Working on a machine's own canonical branch
   (committing, merging its own branches, running tests, updating docs) is always
   permitted and NEVER waits for the other machine. An instruction to "hold
   pushes" does NOT mean hold local commits, merges, rehearsals, or verification —
   it means hold only the shared-state actions.
3. **Rehearse while you wait**. If a step is gated, do the unblocked preparation
   now: run `merge_gate.py`, rehearse on a `merge/<topic>` branch, run the
   verification gates, resolve conflicts. The gated action becomes a single push
   instead of a stalled workflow.
4. **Blocked ≠ idle**. When blocked, do the next safe thing: test, research,
   document, prepare messages, review the diff. Silence and waiting are never the
   default.
5. **Ask once, then proceed**. Post the question once with a deadline, then
   continue with all safe independent work. Do not re-ask, do not idle.
6. **Escalate only real blocks**. Escalation to the human is for decisions that
   genuinely require a human. Work a machine can verify itself is never an
   escalation.

### Law 18 — Tests must be governed
A test that passes while the code is wrong is worse than no test — it produces
false confidence. Every test must carry a machine-readable "theory card" declaring
its independent oracle, acceptance threshold, blind spot (what wrong code it would
NOT catch), and a trust level. Tests run through a governed runner; a result is
UNTRUSTED until it is adversarially reviewed.

1. **No test without a card** — a commit touching `tests/` whose test file has no
   theory card is blocked (structural hook). A missing card is an infrastructure
   failure, not permission to proceed.
2. **Independent oracle** — a test must assert against an analytic formula, a
   published reference, a known-bad fixture, or a pure relation, NOT against the
   code it tests. A self-referential test (asserts the code equals its own
   constant) is worthless and is rejected.
3. **Classify before reporting** — a failing test is not "done" until it is
   classified CODE BUG / TEST BUG / KNOWN LIMITATION with a justification that
   references the oracle. "Ran" is never "passed": a result must state its number
   WITH its threshold (a 400-cent result against a <20-cent target is BROKEN).
4. **Trust levels** — T0 smoke, T1 assertion, T2 independent oracle, T3
   adversarially reviewed, T4 mutation/discrimination verified, T5 validated
   against independent physics/reference. Reports state trust level, not just
   pass/fail.
5. **Adversarial review is a state transition** — a non-trivial change's result is
   UNTRUSTED until `scripts/ai_review.py` (or equivalent) has reviewed it and its
   answer has been fact-checked empirically. Model confidence is not evidence.
6. **Tests must discriminate** — mutation testing (deliberately break the code;
   the test must fail) proves a test actually checks what it claims. A test that
   passes on both broken and fixed code is worthless.

### Law 19 — Delegation authority via the team channel
Defines how work gets assigned between agents so the team channel (Law 11/12)
is not just a log nobody acts on.

1. **Every agent checks its team channel regularly** — same cadence as Law 12.
   A message sitting unread is a protocol violation, not a minor lapse.
2. **The coordinating agent may delegate agreed-upon tasks to other agents
   through the team channel**, and those agents should treat such a
   delegation as actionable — not merely conversational — to the same degree
   a direct message from the human would be.
3. **"Agreed-upon" is the load-bearing qualifier.** Delegation authority
   covers work the human has already approved — explicitly in conversation,
   or via decisions posted to the team channel. No agent has standing
   authority to originate new project direction on its own initiative and
   hand it to another agent as if it were a settled decision. If a
   delegation's approval isn't obvious from the channel history, the
   delegation message must say where the approval came from.
4. **Tag delegated assignments IMPORTANT** (Law 12) so they surface clearly
   and require acknowledgment, with enough detail that the receiving agent
   doesn't have to guess scope — file paths, acceptance criteria, and what
   "done" looks like, not just a topic name.
5. **This does not change who owns the project.** The human's word overrides
   any agent's at any time. This law is a *mechanism* for turning the
   human's already-given approval into concrete work across agents
   efficiently — it is not a grant of independent decision-making power.

### Law 20 — Research before you act; never claim verified without a fresh check
Agents default to over-confidence: they act on a guess, and — the most
repeated failure in this project's own logged history — report a result as
"verified," "passed," or "done" without having actually re-checked it in
this session. Added 2026-08-19 from real evidence, not a general worry:
`scripts/mine_failure_patterns.py` found this is lawkeeper's single most
common logged failure theme (4 of its 5 most-repeated-pattern records) —
a 402.8-cent intonation result called "worked" against a <3-cent target;
an adversarial review skipped while claiming it was satisfied; a duration
estimated from a plan and reported as measured; a `git merge-tree` probe
result trusted without checking its own setup. This law existed in
Windwright's constitution already; lawkeeper had never adopted it despite
needing it more.

1. **A claim of "verified," "passed," "done," or "worked" requires a fresh
   check performed in this session** — re-run, re-imported, re-measured, or
   re-read — not inference from a prior session's summary, a plan, or an
   exit code alone. "The command completed" is not "the result is correct."
2. **State the number with its threshold.** A result reported without its
   acceptance criterion next to it is not a verified result — "ran" is
   never "passed."
3. **Never act on a guess.** Label the ground under every non-trivial
   claim: VERIFIED (checked this session), ASSUMED (inferred), or UNKNOWN.
   If something matters and it is ASSUMED or UNKNOWN, verify it before
   claiming it.
4. **Adversarial/verification steps are state transitions, not optional
   exercises.** A result is UNTRUSTED until the review or check that exists
   to catch it has actually run — a skipped review is an incomplete task,
   not a shortcut.
5. **Do not fabricate.** Never invent numbers, results, timings, or
   precedents. If you do not know, say so and go find out.

### Law 21 — A capability with no consumer is a bug, not neutral
Added 2026-08-20 from a real, live example: orbital-study's `launcher.py`
writes `ratings.json` (real human feedback — 1-5 scores per version pack)
and has done so for a while; `evolution.py` — the thing that actually
decides what gets bred next — never reads it. The tool was built, worked
correctly, and was completely disconnected from anything that used its
output. Nothing in the codebase or the process ever flagged this; it
surfaced only because the user asked a direct question about a specific
feature and an agent happened to grep for it.

This is the same root shape as Law 12's deferred-items gap (a thing exists,
nothing ever forces reconsidering it) applied to code instead of decisions
— so it reuses that fix rather than inventing a second mechanism (Law 3):

1. **When a change introduces something that produces output meant to be
   consumed** (a data file, a report, an API endpoint, a log another
   process is supposed to read) **— name the consumer, in the same
   session, before considering the work done.** "I wrote the data" is not
   "the data does something."
2. **If there is no consumer yet, that is not automatically wrong — but it
   must be an explicit, logged decision, not silence.** Add an entry to
   `docs/FUTURE_DIRECTIONS.md` with a real `Re-check when:` condition
   (Law 12), the same discipline already required for deferred ideas.
   A tool sitting unconsumed with no such entry is exactly the failure
   mode this law exists to prevent.
3. **When auditing existing code** (Law 14, Law 20), a producer/consumer
   mismatch is worth actively checking for, not just the specific thing
   being audited — this is how tonight's instance was found: investigating
   an unrelated feature request surfaced it as a byproduct, not a
   dedicated search. A dedicated periodic check is worth building; until
   then, treat "does anything read this?" as a standing question whenever
   reading code that writes structured output.

Violating any law is a constitutional violation. Log failures in
`docs/AI_FAILURE_PATTERNS.md`.
