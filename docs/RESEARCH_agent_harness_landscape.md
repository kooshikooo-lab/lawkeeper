# Agent-harness landscape — research knowledge base

Started 2026-09-05, prompted by the user's own course-correction: prior
lawkeeper design work (the enforcement stack, the policy ideas in
`GOVERNANCE_PROPOSALS.md`, the harness-adapter thinking in
`EXECUTOR_CONTRACT.md`) was done "blind" — without first checking what the
broader agent-harness/governance ecosystem already ships. That stops now.
This doc is the running knowledge base: one dated entry per project actually
read (not skimmed from a README), what's genuinely reusable or worth copying
the *design* of, and what's confirmed not applicable. Cross-reference from
here, don't duplicate into `GOVERNANCE_PROPOSALS.md` until something is
actually adopted.

**Operating note on cloning:** the C: drive is space-constrained. Any repo
cloned for this research lives under `G:\repos\`, not under lawkeeper's own
tree and not on C:. `G:\repos\omnigent` is the first.

## How an entry gets added here

Only after actually reading source (not just the README/marketing copy) for
the parts relevant to lawkeeper's problem: mechanically enforcing rules on
what an AI coding agent does. Each entry states license (relevant if we'd
ever vendor or depend on code, not just borrow a design), what was actually
read, the concrete mechanism, and an honest verdict — adopt-the-design /
worth-a-dependency / not-applicable — not just "interesting."

---

## Entry 1: Omnigent (omnigent-ai/omnigent)

- **Source:** https://github.com/omnigent-ai/omnigent, cloned to
  `G:\repos\omnigent` (commit at clone time: HEAD of `main`, 2026-09-05).
- **License:** Apache 2.0 — actually usable as a dependency or vendored
  source, not just a design reference.
- **What it is:** a "meta-harness" — a common orchestration layer sitting
  *above* Claude Code, Codex, Cursor, OpenCode, Hermes, Pi, and custom
  YAML-defined agents. It runs sessions (local or in cloud sandboxes:
  Modal, Daytona, E2B, Kubernetes, etc.), syncs them across devices, and
  layers governance ("policies") on top of whichever underlying agent
  harness is doing the actual coding.
- **What was actually read:** `AGENTS.md`, `README.md`'s policy section,
  `omnigent/policies/base.py`, `omnigent/policies/__init__.py`'s exports,
  the `builtins/` module list, and `docs/POLICIES.md` (setup + trust-model
  sections). Not read: the harness adapter internals (`claude_native.py`
  et al.), the sandbox provisioning code, the web/mobile client, the
  runtime engine (`omnigent/runtime/policies/engine.py`) that actually
  does the filter-gate-dispatch-compose loop `base.py` defers to.

### The core mechanism — where it differs from lawkeeper today

Lawkeeper's enforcement stack (Law 16) operates at **git boundaries**:
pre-commit, commit-msg, pre-push, plus a CI backstop that re-runs the same
checks. It never sees what the agent does *between* commits — a bad `rm -rf`
or an unreviewed shell command run mid-session is invisible until something
gets staged.

Omnigent's policy engine operates at **tool-call boundaries**, inside the
agent's own loop: every tool call (shell command, file write, MCP call) is
evaluated live and gets one of three verdicts before it executes:

- **ALLOW** — proceeds.
- **DENY** — blocked, agent gets an error back.
- **ASK** — paused for a human decision; approved becomes ALLOW, refused
  becomes DENY.

Policies compose in declaration order; a DENY from any policy short-circuits
the rest (`docs/POLICIES.md`, confirmed against `Policy.evaluate`'s contract
in `base.py`). Three configuration levels stack — server-wide (admin),
per-agent (developer), per-session (end user) — with **session policies
evaluated first**, so the most locally-set rule can veto before broader
defaults even run.

This is a different enforcement point than lawkeeper's, not a replacement
for it: lawkeeper catches what got committed; omnigent's model would catch
the tool call before it happens at all. They compose — the two failure modes
in lawkeeper's own README ("blind merge importing 20 conflicts", "agent
committing unverified work") are commit-boundary problems git hooks are
suited to; "agent ran a destructive command mid-session because an
instruction was vague" is exactly what an ALLOW/DENY/ASK tool-call gate is
for and a git hook structurally cannot see.

### Concrete things worth learning from (design, not code)

1. **A real decision algebra, not pass/fail.** Lawkeeper's guard scripts
   today are binary (block the commit or don't). ALLOW/DENY/ASK is a small
   but genuinely useful addition — most of lawkeeper's "pause and ask a
   human" cases (e.g. an `AUDIT:` marker being missing — is it forgotten or
   deliberate provisional work?) are actually ASK, not DENY, and currently
   get force-fit into a binary block.
2. **Tiered policy precedence (session > agent > server-wide).** Lawkeeper's
   laws are currently flat and repo-wide. The idea of a stricter local
   override evaluated first (vs. a looser default evaluated last) is a
   pattern worth stealing if lawkeeper ever needs per-branch or
   per-contributor rule variance instead of one constitution for everyone.
3. **Declarative composition over hardcoded guard scripts.** Policies are
   YAML entries pointing at `handler` callables with `factory_params` —
   adding a new rule is data, not a new Python file wired into the hook
   runner. Lawkeeper's guards are one-off scripts in `scripts/`; a
   registry-plus-factory pattern would make Law additions cheaper to author
   and easier to unit-test in isolation (each policy is just a pure
   function of `(context) -> verdict`).
4. **Framework-owned vs. user-authored instructions, kept separate and
   appended, not merged** (`AGENTS.md`'s "Framework-owned instructions"
   section). Directly relevant to lawkeeper's own constitution-authoring
   story: keep the mechanically-enforced law text separate from
   project-specific customization, composed rather than hand-merged, so a
   `lawkeeper init` upgrade doesn't clobber project-local additions.
5. **The harness-adapter pattern itself.** One adapter module per
   underlying coding agent (`claude_native.py`, `codex_native.py`,
   `cursor_native.py`, `opencode_native.py`, ...), each implementing the
   same bridge/forwarder/status contract. If lawkeeper's own
   `EXECUTOR_CONTRACT.md` ambitions ever extend past opencode/Claude, this
   is a working, Apache-licensed reference for what that adapter boundary
   looks like in practice — not something to depend on directly (adopting
   omnigent wholesale would be a much bigger bet), but a real precedent to
   check lawkeeper's own contract draft against.

### What's confirmed *not* applicable

Omnigent is a full orchestration platform (multi-device sync, cloud sandbox
provisioning, a native desktop/mobile app, a REST API, telemetry) — that's
not lawkeeper's problem. Pulling it in as a dependency to get the policy
engine would mean adopting a large surface lawkeeper doesn't need. The
verdict on this entry is **adopt-the-design of the policy algebra and
tiering, do not depend on the package.**

### Open follow-ups (not done yet)

- Haven't read `omnigent/runtime/policies/engine.py` — the actual
  gate-dispatch-compose loop `base.py`'s docstring defers to. That's where
  the real implementation detail of "stricter session rules checked first"
  would be verified, not just asserted from docs.
- Haven't checked how `ASK` is actually surfaced to a human synchronously
  (this matters most for lawkeeper — an `AUDIT:`-marker-missing case is the
  same "pause for the human" shape).
- Haven't looked at `omnigent/policies/builtins/cel.py` — CEL
  (Common Expression Language) as a policy-condition DSL is a second
  candidate pattern (declarative conditions without a full Python callable)
  worth a dedicated look before deciding what a lawkeeper policy DSL, if
  one gets built, should look like.

---

## Candidate projects queued for future entries

Not yet cloned or read — listed here so the queue survives across sessions
instead of living only in chat:

- **Open Policy Agent (OPA) / Rego** — the general policy-as-code prior art
  everything above (including likely omnigent's own thinking) draws from.
  Worth reading before designing any lawkeeper policy DSL, since it's the
  thing to deliberately converge with or deliberately diverge from, not
  reinvent uninformed.
- **pre-commit** (the framework, not just the hook lawkeeper already
  depends on) — lawkeeper already uses it as a mechanism; worth reading its
  own extension model for ideas on how lawkeeper's guard scripts are
  packaged/versioned/shared across repos (Windwright/orbital-study/falcun
  currently get copies, per `RESEARCH_governance_mechanism_audit.md` —
  that's exactly the "how do policies get distributed and stay in sync
  across repos" problem OPA/pre-commit both had to solve).
- **Anthropic's own Claude Agent SDK permission/hook system** — closest
  first-party analogue to omnigent's policy engine, and the one lawkeeper
  is most likely to actually integrate with rather than merely imitate,
  since lawkeeper already targets Claude Code sessions directly.

## Re-check when

Before any new lawkeeper governance mechanism (a new Law, a new guard
script, anything in `GOVERNANCE_PROPOSALS.md` moving to implementation) is
designed from scratch — check this doc first, and add an entry here before
adding a proposal there if the design was informed by outside research.
