# Harness hook-mechanism survey — three more coding-agent harnesses, source-read

Started 2026-09-06. `docs/RESEARCH_harness_governance_survey.md` found that Claude
Code's own `PreToolUse` hooks already implement a deny→ask→allow three-tier gate,
and that Omnigent's independently-built policy engine converged on the identical
precedence — a two-system finding. This survey checks whether that's a genuine
convergent algebra for "gate an agent's tool call before it runs" or a two-system
coincidence, by reading three more open-source coding-agent harnesses' own source
directly: **deepseek-harness** (`dsh`), **hermes-agent**, and **goose**. Same
discipline as the two docs above: every claim states what was actually read
(specific file paths) versus what's secondhand, and ends with a concrete verdict.

---

## 1. deepseek-harness (`deepseek-ai/deepseek-harness`, the `dsh` CLI)

- **Source:** local clone at `C:\Users\Admin\deepseek-harness`. Not re-cloned —
  the local checkout is current (latest commit `47f943859b`, 2026-08-13, "Merge
  pull request #2519 from deepseek-harness/feat/npm-public").
- **License:** MIT — confirmed by reading `LICENSE` directly (`Copyright (c) 2026
  DeepSeek`). Genuinely usable as a dependency or vendored source, not just a
  design reference, though see the verdict below on why that's not the live
  option today.
- **What was actually read:** `AGENTS.md`'s directory map and its "hooks/" /
  "interaction/" one-line descriptions; `packages/hooks/hook-protocol/README.md`
  (full) and `packages/hooks/hook-protocol/src/types.ts` (full); the directory
  listing of `packages/hooks/hooks-claude-code/` and `packages/hooks/hooks-codex/`
  (file names only, not their `src/index.ts` bodies — the per-dialect bridge
  implementations were NOT read, only the neutral library's description of what
  each bridge does); `packages/interaction/permission-presets/src/types.ts` and
  `src/index.ts` (both full); `packages/interaction/user-approval/src/types.ts`
  (full) and `src/index.ts` (lines 1–100 of a longer file — the request/answerer
  dispatch and cancellation internals past line 100 were not read); `packages/
  interaction/tool-ask-user/src/index.ts` (full, the model-facing `ask_user_
  question` tool). Not read: the actual `PreToolUse` interception call sites in
  dsh's own agent runtime, or `hooks-claude-code`/`hooks-codex`'s bridge source.
- **Is `dsh` its own harness, or only a wrapper?** Its own: it has a native
  TypeScript tool-execution loop (the `dsh` CLI) with its own `PreToolUse`/
  `PostToolUse`/etc. hook points — and it *additionally* ships two "dialect"
  bridge plugins (`dsh-hooks-claude-code`, `dsh-hooks-codex`) that reproduce
  Claude Code's and Codex's own `hooks.json` wire protocols closely enough that
  an existing Claude Code or Codex hook script can be dropped into a `dsh`
  project unmodified. The genuinely-shared parts of that wire protocol (matcher
  parsing, hook execution, output decoding, **merging**) live in the
  dialect-neutral `hook-protocol` library the two bridges both import — the
  README states this explicitly: "Codex deliberately reimplements a *subset* of
  the Claude Code hook protocol... The genuinely-shared parts live here; each
  bridge owns only what differs."
- **Does it have a `PreToolUse`-style live gate? What's the decision model?**
  Yes, and the decision model is explicit, not inferred. `hook-protocol/src/
  types.ts` documents `HookOutput.decision` as a normalized enum folding two
  distinct upstream channels ("the legacy top-level `decision` (`approve`/`block`
  only) and `hookSpecificOutput.permissionDecision` (`allow`/`deny`/`ask`)") into
  one: `'approve' | 'allow' | 'block' | 'deny' | 'ask'`. The README states the
  merge rule for when multiple hooks fire on one point in one sentence:
  **"permission precedence deny > ask > allow, halt sticky on the first
  `continue:false`"** — `mergeHookOutputs(outputs)`. This is dsh's own,
  independently-authored merge algebra, stated in its own documentation, not
  copied from Claude Code's docs or Omnigent's engine. **This is the survey's
  third independent codebase to state deny>ask>allow outright.**
- **A useful side finding, sourced from dsh's own comment, about a fourth
  harness (Codex):** `types.ts`'s docstring on `HookOutput.decision` says the
  bridge "decides which fields are meaningful for its hook point and which it
  ignores (faithful-but-degraded — e.g. Codex ignores `allow`/`ask`)." Read
  plainly, that means dsh's own maintainers, in the course of building a
  wire-compatible Codex hook bridge, found Codex's native hook protocol has **no
  ask concept at all** — only approve/block. This is **secondhand relative to
  Codex's own source** (this survey did not read Codex's docs or source
  directly, only dsh's comment about it) and is flagged as such, but it's a
  primary, first-party statement from a team that had to actually implement
  Codex-protocol-compatibility, which is stronger sourcing than a blog post.
- **A distinct, separate mechanism — session-level capability scoping,
  alongside the live gate, not instead of it:** `permission-presets/src/
  index.ts` composes two independent knobs into named presets: `sandbox/mode`
  (a `SandboxMode` — e.g. `workspace-write` / `danger-full-access`, set once per
  session, a structural boundary on what's reachable at all, not a per-call
  decision) and `approval/policy` (`'ask' | 'never'`, confirmed from
  `user-approval/src/index.ts` lines 88–97 — `'ask'` delegates to composed
  answerers, falling through to a fail-closed `'unavailable'` if none are
  composed; **`'never'` does not mean "always allow"** — it means "every ask
  resolves `'rejected'` deterministically," a fail-safe default for headless/CI
  runs, the opposite bias from a bypass-to-allow). The shipped default presets
  are `workspace-write` (sandbox: workspace-write, approval: ask) and
  `danger-full-access` (sandbox: danger-full-access, approval: never). This is a
  genuine, sourced example of "capability scoping decided once at startup"
  coexisting with a live per-call ask gate, exactly the third alternative shape
  the assignment asked each entry to distinguish from a per-call gate.
- **The ask outcome vocabulary:** `user-approval/src/types.ts` defines
  `ApprovalOutcome = 'allowed-once' | 'rejected' | 'cancelled' | 'unavailable'`,
  with the type doc stating "callers fail closed on `unavailable`." This
  independently converges with Omnigent's approve/decline/cancel-fails-closed
  split (landscape doc) and MCP's own elicitation accept/decline/cancel
  primitive (governance survey §5) — a third, independently-arrived-at instance
  of treating "explicit no," "dismissed without an answer," and "nobody was
  there to ask" as three distinct outcomes rather than one bucket.
- **Verdict: adopt-the-design, not a dependency.** `dsh` is TypeScript/Node;
  lawkeeper's guard scripts and planned `PreToolUse` hook are Python. Even
  though MIT licensing makes vendoring `hook-protocol` technically viable, there
  is no realistic integration path today. What's directly worth reusing as
  *design*: the `deny > ask > allow` merge rule stated as an explicit, testable
  function contract (not just a convention scattered across call sites); the
  sandbox-mode + approval-policy preset composition as a template for a future
  lawkeeper "CI mode" that needs to deterministically fail closed without a
  human present; and the four-way `ApprovalOutcome` split as the target shape
  for any future lawkeeper ASK-tier outcome type.

---

## 2. hermes-agent (`NousResearch/hermes-agent`)

- **Source:** local clone at `C:\Users\Admin\Desktop\hermes-agent`.
- **License:** MIT — confirmed by reading `LICENSE` directly (`Copyright (c)
  2025 Nous Research`).
- **Cross-referenced Omnigent's adapter first, then verified against Hermes'
  own source — both sides checked, not just one:**
  - Read in full: `G:\repos\omnigent\omnigent\hermes_native_permissions.py`
    and `hermes_native_bridge.py`. Omnigent's own comments describe Hermes'
    interactive TUI rendering a `prompt_toolkit` panel titled "⚠️ Dangerous
    Command" with numbered choices ("1. Allow once", "2. Allow for this
    session", "3./4. Add to permanent allowlist" / "Deny" — the exact digit for
    Deny shifts depending on whether the allowlist option is offered).
    `hermes_native_bridge.py`'s `write_policy_hook_config` shows Omnigent
    registers its OWN hook into Hermes by writing a `hooks.pre_tool_call` entry
    into a per-session `~/.hermes`-shaped `config.yaml`, with
    `hooks_auto_accept: true` and a pre-populated `shell-hooks-allowlist.json`
    so Hermes doesn't itself prompt for hook-registration consent.
  - Then read Hermes' own `agent/shell_hooks.py` (module docstring in full,
    lines 1–200) and `tools/approval.py` (module docstring plus ~1,300 lines:
    `HARDLINE_PATTERNS`, `DANGEROUS_PATTERNS`, `_match_user_deny_rule`,
    `_check_sudo_stdin_guard`, `detect_hardline_command`, and the approval-policy
    contextvar plumbing) directly, independent of Omnigent's description.
  - **The two sides match, confirming Omnigent's adapter map was accurate, not
    just plausible-sounding:** `shell_hooks.py`'s documented `hooks:` block
    schema (`pre_tool_call`/`post_tool_call` events, `hooks_auto_accept`,
    `ALLOWLIST_FILENAME = "shell-hooks-allowlist.json"`) is exactly what
    `write_policy_hook_config` writes into. **This survey confirmed Omnigent's
    reverse-engineered map against Hermes' own source directly — it did not
    rely on only one side.**
- **The generic external-hook layer (`agent/shell_hooks.py`) — binary, no ask
  in the wire protocol:** stdin carries `{"hook_event_name", "tool_name",
  "tool_input", ...}` as JSON; stdout may return a block directive in either
  `{"decision": "block", "reason": ...}` (Claude-Code-style) or `{"action":
  "block", "message": ...}` (Hermes-canonical) shape, or a `modify` action for
  either dialect. **Exit code 2 blocks, Claude-Code/Cursor-compatible, exactly
  as the docstring states.** Fails open by default (a spawn error, timeout, or
  unparseable stdout "logs a warning and contributes nothing"); a hook can
  opt into fail-*closed* per-entry via `fail_closed: true`. There is **no `ask`
  verdict anywhere in this wire protocol** — it is allow-by-default-unless-
  blocked, plus a separate `modify` action. Structurally this is a close cousin
  of goose's external hook layer (below) and dsh's Codex dialect: an
  arbitrary-script `PreToolUse`-equivalent that stays binary.
- **A separate, built-in (not externally-scripted) three-tier classifier,
  specific to the terminal/shell tool — and this one DOES implement deny→ask→
  allow, confirmed directly from source:** `tools/approval.py`'s dangerous-
  command system is structured, in its own code, into exactly three tiers:
  1. **`HARDLINE_PATTERNS`** (root-filesystem `rm -rf`, `mkfs`, raw block-device
     `dd`, fork bombs, `kill -1`, shutdown/reboot) plus the user-editable
     `approvals.deny` config list — **unconditional block, no ask escape hatch
     at all.** The block message is quoted directly from source: "This command
     is on the unconditional blocklist and cannot be executed via the agent —
     not even with `--yolo`, `/yolo`, `approvals.mode=off`, or cron approve
     mode." This tier is closer to Cedar's forbid-always-wins (governance
     survey §1) than to a three-way algebra — there is deliberately no ASK
     tier here at all, by design, not by omission.
  2. **`DANGEROUS_PATTERNS`** match (recursive delete, `chmod 777`, `git push
     --force`, `git reset --hard`, pipe-remote-to-shell, etc.) → triggers the
     interactive "Dangerous Command" approval panel (**ask**) — but this tier
     IS bypassable, via `--yolo`/`/yolo`, `approvals.mode: off` (confirmed at
     `tools/approval.py:4390-4393`, `:5021-5023`), or `approvals.mode: smart`
     (an auxiliary LLM auto-approves commands it judges low-risk, confirmed at
     `tools/approval.py:4626` and the `_prepare_smart_approval_observer`/
     `_observe_smart_approval_verdict` functions read above).
  3. Everything else → default allow.
  Read plainly, tier 1 > tier 2 > tier 3 is **deny(unconditional) > ask
  (bypassable) > allow(default)** — the same three-tier ordering as Claude
  Code/Omnigent/dsh, confirmed directly from Hermes' own source, in a different
  subsystem shape (a hardcoded pattern classifier, not a generic hook-merge
  function). **This is the survey's fourth independent confirmation of the
  ordering**, and its first sourced example of the ordering appearing in a
  built-in classifier rather than a pluggable hook/policy engine.
- **Verdict: adopt-the-design (the hardline-floor / bypassable-ask / default-
  allow tiering), not a dependency.** `tools/approval.py` is a single ~5,400-
  line file deeply coupled to Hermes' own shell-execution and TUI model — not
  something to vendor. What's directly useful: this is a second **shipped,
  production** implementation (after Cedar's *design*, per the governance
  survey) of "some decisions should have literally no ASK escape hatch, not
  even under a global override flag" — directly relevant to lawkeeper's planned
  canonical-branch/force-push protection, which is exactly hardline-floor-
  shaped (Law 15's branch-deletion guard already has no-ASK framing per the
  governance survey's Cedar entry; Hermes is now concrete precedent that a real
  product ships that carve-out as a named, separate tier, not an oversight).

---

## 3. goose (`block/goose`)

- **Source:** a backup copy at `E:\Desktop-Backup\goose-main` — **not a git
  clone** (`git log` fails: "not a git repository"). Staleness was checked
  explicitly: `Cargo.toml` reports `version = "1.39.0"`, and file mtimes
  cluster around 2026-06-27. A direct fetch of `github.com/block/goose/releases`
  this pass shows the live project at **v1.49.0, released 2026-09-03** — this
  backup is roughly ten releases / ten weeks behind live `main`, and that gap's
  release notes mention "numerous security fixes" among other changes. Every
  claim below is therefore about **1.39.0-era goose, confirmed by reading this
  backup's source directly — not necessarily current HEAD**, and is stated that
  way rather than presented as goose's current behavior.
- **License:** Apache 2.0 — confirmed by reading `LICENSE` directly.
- **What was actually read:** `crates/goose/src/permission/mod.rs` (full, 11
  lines — a re-export shim); `crates/goose/src/config/permission.rs` (full,
  including its test module); `crates/goose/src/permission/permission_judge.rs`
  (full); `crates/goose/src/permission/permission_inspector.rs` (lines 1–220 of
  a longer file — the LLM-based read-only-detection tail past line 220 was not
  read); `crates/goose/src/tool_inspection.rs` (lines 1–280 of a longer file,
  covering `InspectionAction`, `ToolInspectionManager`, and
  `apply_inspection_results_to_permissions` in full; the test module past that
  was not read); `crates/goose/src/hooks/mod.rs` (full, including its test
  module).
- **Two distinct, separately-named mechanisms — both confirmed by source, and
  they answer the assignment's question two different ways:**
  1. **The in-process tool-inspection/permission system — has the three-tier
     algebra, stated explicitly in code.** `config/permission.rs` defines
     `PermissionLevel::{AlwaysAllow, AskBefore, NeverAllow}` per tool (a
     "principal," keyed by tool name), tracked in two independent categories —
     a `user`-set override and a `smart_approve` cache (populated either from a
     tool's own `read_only_hint` annotation or an LLM's read/write
     classification, per `permission_judge.rs`'s `detect_read_only_tools`).
     `permission_inspector.rs`'s `PermissionInspector::inspect` resolves these
     under a `GooseMode` (`Chat`/`Auto`/`Approve`/`SmartApprove`), checking user
     permission FIRST and only falling through to smart-approve/LLM-detection
     when no explicit user permission exists (lines 145–182) — user override
     always wins over the cache. Multiple `ToolInspector` implementations
     (permission, and at least one other referred to by the string `"security"`
     at `tool_inspection.rs:266`, not itself read this pass) each emit
     `InspectionAction::{Allow, Deny, RequireApproval(Option<String>)}`, and
     `apply_inspection_results_to_permissions` (`tool_inspection.rs:170-257`)
     folds them into one `PermissionCheckResult{approved, needs_approval,
     denied}` with the precedence **stated in the code's own comments, not
     inferred**: a `Deny` result strips the request from `approved`/
     `needs_approval` and forces it into `denied`; a `RequireApproval` strips it
     from `approved` and adds it to `needs_approval`; the `Allow` branch's
     comment reads verbatim: *"This inspector allows it, but don't override
     other inspectors' decisions — if it's already denied or needs approval,
     leave it that way."* That is **deny > ask > allow**, asserted as source
     code, not reconstructed from behavior. **This is the survey's fifth
     independent confirmation of the ordering.**
  2. **A separate, external plugin-hook system (`crates/goose/src/hooks/
     mod.rs`) — binary, no ask in the wire protocol, and explicitly modelled on
     a THIRD-PARTY spec new to this survey.** The module docstring states it
     is "modelled after the Open Plugins [hooks specification]
     (https://open-plugins.com/agent-builders/components/hooks)" — i.e. goose
     did not invent this hook shape itself, it's implementing an external,
     named, cross-vendor standard this survey had not previously checked (see
     the landscape-doc follow-up below). Hooks live in `<plugin-root>/hooks/
     hooks.json`, support `PreToolUse`/`PostToolUse`/`PostToolUseFailure`/
     `SessionStart`/`SessionEnd`/`UserPromptSubmit`/`BeforeReadFile`/
     `AfterFileEdit`/`BeforeShellExecution`/`AfterShellExecution`/`Stop`
     events, and the decision type is a plain binary enum: `HookDecision::
     {Allow, Deny{reason, plugin}}` (`hooks/mod.rs:224-227`). A hook denies via
     exit code 2 (reason from stderr) or `{"decision":"block","reason":"..."}`
     on stdout — the identical Claude-Code/Cursor-compatible convention Hermes'
     `shell_hooks.py` and dsh's Codex dialect also use. **Every other failure
     mode (spawn error, timeout, non-zero exit without block JSON) is
     explicitly treated as Allow** — the code comment states the design intent
     outright: *"a misbehaving hook MUST NOT block"* (`emit_blocking`'s doc
     comment, `hooks/mod.rs:359-363`) — fail-*open* by unconditional design,
     the opposite default from Hermes' opt-in `fail_closed`. There is no ask
     concept anywhere in this wire protocol.
- **`GooseMode` is a session-level policy dial gating the live per-call ask —
  not capability scoping, and the difference matters, exactly as the
  assignment anticipated.** `Chat` never asks (no tool calls happen at all in
  that mode), `Auto` always allows without asking, `Approve`/`SmartApprove`
  route through the tiered permission check above. This is a third,
  independent instance (after dsh's `approval/policy` and Hermes' `approvals.
  mode`) of "a coarse, session-level policy knob decides whether the live
  per-call gate is even consulted" — but unlike dsh's `sandbox/mode`, `GooseMode`
  does not structurally restrict what's *reachable* (no sandboxing/containment
  is implied by the mode itself); it only changes how permissively the same
  reachable tool surface is gated. Confirming this distinction was explicit in
  the assignment and is a real, sourced one: a policy-strictness dial and a
  capability/sandbox boundary are different mechanisms even when both are
  "decided once, not per call."
- **Verdict: adopt-the-design, not a dependency.** Apache-2.0 makes vendoring
  technically viable, but goose is a full Rust desktop/CLI/server application —
  not an integration lawkeeper's Python git-hook tooling would realistically
  take on for this one mechanism. What's directly useful: goose is the
  clearest single example in this survey of the exact split the closing
  synthesis needed — an external, arbitrary-script hook layer that stays
  binary for portability/simplicity, sitting alongside a separately-named,
  richer, three-tier decision layer that actually governs execution. Also
  worth a standalone follow-up: the Open Plugins hooks spec goose implements is
  a candidate cross-harness hook standard this survey had not previously
  checked (queued below, not read this pass).

---

## Convergence verdict — does deny→ask→allow generalize?

Before this survey, the governance survey had **two** independently-built
systems (Claude Code, Omnigent) asserting the identical deny>ask>allow
precedence. This survey adds **three more, independently**:

1. **dsh** (`deepseek-ai/deepseek-harness`) — `mergeHookOutputs`'s documented
   merge rule, "permission precedence deny > ask > allow," in its own native
   hook-protocol library.
2. **hermes-agent** — its built-in dangerous-command classifier
   (`tools/approval.py`): hardline-unconditional-deny > bypassable-ask >
   default-allow, stated in its own block-message text.
3. **goose** — `apply_inspection_results_to_permissions`'s explicit merge
   comment: deny always wins, ask beats allow, allow never overrides either.

That is **five** independently-built codebases — two written in Python
(Omnigent, Hermes), one in TypeScript documentation (Claude Code's own docs)
plus a second, separate TypeScript implementation (dsh), and one in Rust
(goose) — by at least four different organizations (Anthropic, an
independent Omnigent team, Nous Research, Block, DeepSeek), all converging on
the identical three-tier ordering for the identical problem: deciding whether
an agent's tool call executes. **This is no longer a two-system coincidence.**
Five independent teams solving the same problem landing on the same ordering
is about as strong a "this is a natural algebra for the problem, not a house
style" signal as a source-reading survey of this kind can produce without a
formal impossibility proof (the kind of thing Cedar's SMT-backed analysis,
governance survey §1, could in principle attempt but that no system in this
survey has actually done).

**The refinement this survey adds, beyond "yes it generalizes":** the ask tier
does not always live at the same layer. In three of the five systems checked
across both surveys (goose's plugin hooks, Hermes' `shell_hooks.py`, and —
secondhand via dsh's own comment — Codex's native hook protocol), the
**external, arbitrary-script hook wire protocol is binary allow/deny only,
with no ask verdict at all** — even though two of those same three systems
(goose, Hermes) have a three-tier, ask-capable decision layer *somewhere else*
(goose's in-process `ToolInspector` pipeline; Hermes' built-in dangerous-
command classifier). Only Claude Code's own hook protocol and dsh's native
hook-protocol library were confirmed to carry `ask` in the wire format a hook
script itself can return. So the practical lesson is two-part: **the
deny>ask>allow algebra is a safe, well-evidenced target for lawkeeper's own
`GateDecision` type** — but **if lawkeeper's harness-adapter ambitions
(`EXECUTOR_CONTRACT.md`) ever generalize past Claude Code, don't assume every
target harness's own hook JSON schema can express "ask" directly** — several
shipped ones can't, and route ask-worthy decisions through a different,
harness-specific mechanism instead (a built-in approval UI, a separate
in-process policy layer) rather than the generic hook channel.

**A second pattern surfaced by all three new reads, distinct from the algebra
question:** three of five systems (goose's `GooseMode`, dsh's `approval/
policy`, Hermes' `approvals.mode`) each separately found it necessary to add a
**session-level policy dial ABOVE the per-call gate** — something that decides
whether the live ask is even consulted (so a CI/headless run can behave
deterministically without a human present) — and two of those three (dsh's
`sandbox/mode`, Hermes' `HARDLINE_PATTERNS`/`approvals.deny`) also added a
**hardline floor BELOW it** that no override, including that same policy dial,
can bypass. Lawkeeper's design docs to date model law enforcement as a single
flat script per guard; this survey found that every system with enough
production mileage to need one independently grew both a strictness dial above
the per-call gate and an unconditional floor below it. That's not part of
lawkeeper's currently-scoped `PreToolUse` build, but it's now a
well-evidenced "you will probably want this eventually" rather than a
speculative feature.

---

## Recommendation — does lawkeeper's planned build change?

**Proceed with the planned `PreToolUse`-hook build as scoped — canonical-
branch/force-push protection, reusing `guard_branch.py`'s branch classification,
a new command-string detection layer, core decision logic in `src/guardrail/`
decoupled from the Claude-Code-specific adapter.** Nothing in this survey
argues for a different design or a larger scope. Three concrete, additive
refinements this survey earns, none of which change the plan's shape:

1. **Treat `deny > ask > allow` as a settled target for lawkeeper's
   `GateDecision` merge logic, not a Claude-Code-specific quirk to hedge
   against.** Five independently-built systems now confirm it (Claude Code,
   Omnigent, dsh, Hermes, goose) — cite this survey, not just the governance
   survey's two-system finding, when `src/guardrail/`'s decision type is
   implemented and tested.

2. **Model the canonical-branch/force-push guard specifically as a hardline
   tier with no ASK escape hatch, structurally distinct from any other,
   ask-capable guard lawkeeper adds later.** This was already flagged as a
   Cedar-style carve-out worth having in the governance survey; this survey
   adds two more shipped, sourced precedents for exactly that carve-out
   (Hermes' `HARDLINE_PATTERNS` + `approvals.deny`, goose's Deny-always-wins
   merge) — implement the hardline tier as a distinct code path/type from the
   ask-capable tiers from the start, not as a `GateDecision::Deny` that
   happens to never get an ask variant by convention.

3. **A documentation note for `EXECUTOR_CONTRACT.md`, not a change to today's
   build:** if lawkeeper's harness-adapter ambitions ever extend past Claude
   Code, the hook wire protocol on the other side may not support `ask` at
   all (confirmed for goose and Hermes; secondhand-but-sourced for Codex, via
   dsh's own bridge-implementation comment) — a future non-Claude-Code adapter
   would need to either route ask-worthy decisions elsewhere or degrade them
   to a conservative deny, not assume the hook channel itself can ask.

**One structural pattern this survey confirms lawkeeper's plan already gets
right:** every system read this pass keeps "detect/classify" and "speak the
harness's hook wire dialect" as separate code, the same split
`EXECUTOR_CONTRACT.md` already intends for lawkeeper (`src/guardrail/`'s core
logic decoupled from the Claude-Code-specific adapter). Hermes' `tools/
approval.py` (detection) versus `agent/shell_hooks.py` (wire dialect), dsh's
`hook-protocol` (neutral) versus `hooks-claude-code`/`hooks-codex` (dialects),
and goose's `tool_inspection.rs`/`permission_inspector.rs` (decision) versus
`hooks/mod.rs` (external wire protocol) are three more working examples of
that split — direct, additional confirmation for a design choice lawkeeper had
already made, not a new idea to adopt.

## Open follow-ups this survey surfaces, not resolved here

- **The Open Plugins hooks specification** (open-plugins.com/agent-builders/
  components/hooks) — goose implements it explicitly; this survey has not read
  the spec itself, only goose's implementation of it. Worth checking directly:
  if this is a genuine cross-vendor standard (not just goose's own name for its
  own format), it may be a more durable citation for lawkeeper's hook-wire
  design than any single harness's docs.
- **Codex's own native hook protocol, read directly** — this survey only has
  dsh's secondhand-but-sourced comment ("Codex ignores allow/ask"). Worth a
  dedicated read of Codex's own docs/source before citing "Codex's hook
  protocol is binary" as a confirmed (not secondhand) fact anywhere load-
  bearing.
- **dsh's `hooks-claude-code`/`hooks-codex` bridge source itself** — this
  survey read the neutral `hook-protocol` library and inferred the bridges'
  behavior from its README's description of the division of labor, not the
  bridge implementations directly.
- **goose's live `main` branch** — this survey's goose entry is confirmed
  against a backup roughly ten weeks behind current release (1.39.0 vs. live
  1.49.0); re-check `permission_inspector.rs`/`tool_inspection.rs`/`hooks/
  mod.rs` against a fresh clone before relying on exact line numbers or
  behavior details for anything beyond this survey's own directional
  conclusions.
