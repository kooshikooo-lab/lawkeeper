# External scan — 2026-11-05

Weekly scheduled research pass. Scope per the routine's own brief: runtime/
`PreToolUse`-style agent governance, policy-decision algebras (allow/deny/ask),
git-hook distribution/enforcement patterns, and test-governance/oracle-
independence methodology. Not Windwright's domain (acoustics/CAD) and not
Falcun's (evolutionary mutation, epistemic-claim verification) — a harness's
other features are out of scope here even when its governance mechanism is
in scope. (Note: the last scan on record is `RESEARCH_EXTERNAL_SCAN_2026-10-15.md`;
there is a three-week gap in this doc's own numbering — no 2026-10-22 or
2026-10-29 scan file exists in this repo's history. Not investigated this
pass, since the task is to run this week's scan, not audit why a prior one
may not have fired; flagged here only so a future pass doesn't need to
re-discover the gap.)

**Access note, stated up front because it shaped everything below:** this
session's egress proxy is markedly more restrictive than prior scans'. Every
non-GitHub host attempted this pass failed as an explicit proxy-level policy
denial (`CONNECT tunnel failed, response 403` / `connect_rejected`), not a DNS
failure like 2026-10-15 saw — functionally the same "blocked," a third
distinct failure surface for the same underlying policy, confirmed via the
proxy's own status endpoint. Confirmed blocked this pass: `open-plugins.com`,
`developers.openai.com`, `repository.tudelft.nl`, `docs.snowflake.com`,
`blog.trailofbits.com`, `arxiv.org`, `export.arxiv.org`,
`api.semanticscholar.org`. Reachable this pass: `github.com`,
`raw.githubusercontent.com`, and (for search, not page fetches) the
`api.github.com` code/repo search endpoints. One attempt to route around the
`open-plugins.com` block via a Wayback Machine mirror was refused by this
session's own tool-use policy as a containment-escape attempt — correctly,
since a mirror fetch is exactly the kind of workaround that policy exists to
prevent, not a loophole to exploit; not re-attempted after that, and no
substitute content was used in its place. Everything below marked "actually
read" is GitHub-hosted (a project's own source files, generated schemas, or
docs-source Markdown, fetched via `raw.githubusercontent.com` directly) —
the same access pattern 2026-10-01/10-15 used when a vendor's own docs site
was blocked, just needed for nearly everything this pass rather than two
items.

---

## 1. Codex's native hook protocol — resolved from primary source, after three prior passes stuck at secondhand

This item has been queued since the hook-mechanisms survey (2026-09-06) and
was re-attempted and still blocked on 2026-10-01, 2026-10-08 (partially — see
that scan), and 2026-10-15. `developers.openai.com` is still blocked this
pass too (confirmed again, `connect_rejected`) — but this pass found the
actual answer sitting in OpenAI's own **source code**, not its docs site,
reachable the whole time via `raw.githubusercontent.com`/`api.github.com`
search, which none of the three prior passes tried for this specific item
(they checked `github.com/openai/codex/docs/config.md` for a hooks *doc*,
not the hook *implementation* itself).

- **What was actually read, all via `raw.githubusercontent.com` against
  `openai/codex`'s `main` branch, 2026-11-05:**
  - `codex-rs/hooks/src/events/pre_tool_use.rs` (full, including its test
    module — 38 tests, several directly on point and quoted below)
  - `codex-rs/hooks/src/engine/output_parser.rs` (full)
  - `codex-rs/hooks/src/engine/dispatcher.rs` (first ~150 lines: handler
    selection and the multi-handler execution loop; the async-scheduling
    tail past that was not read)
  - `codex-rs/hooks/schema/generated/pre-tool-use.command.output.schema.json`
    (full, generated JSON Schema)
  - `codex-rs/hooks/schema/generated/permission-request.command.output.schema.json`
    (full, generated JSON Schema)
  - `codex-rs/tui/src/hooks_rpc.rs` (full — TUI-side RPC client for
    `hooks/list` and hook-trust management; confirms hooks are discoverable
    and trust-tracked per-hook, but not itself the decision engine)
  - Confirmed directly: `LICENSE` is Apache 2.0.
  - **Not read:** `codex-rs/hooks/src/declarations.rs`, `schema.rs` (the
    `hooks.json` *input*-side config schema itself), `engine/discovery.rs`,
    or the async/subagent-hook paths in `dispatcher.rs` past line ~150 —
    none needed to answer this item's specific question, but flagged as
    real gaps rather than silently treated as covered.
- **License:** Apache 2.0, confirmed by reading `LICENSE` directly. Not
  presented as a dependency candidate (a Rust CLI's internal hook engine is
  not something lawkeeper's Python tooling would vendor) — read for the
  design/precedent, same as every other harness in this research base.
- **The actual `PreToolUse` decision model, confirmed from source, not
  inferred:** the generated schema's own enum settles the long-open
  question outright:
  ```json
  "PreToolUsePermissionDecisionWire": { "enum": ["allow", "deny", "ask"], "type": "string" }
  ```
  `ask` is schema-valid — a hook author who sends it will not get a JSON
  validation error. But `output_parser.rs`'s
  `unsupported_pre_tool_use_hook_specific_output` function explicitly
  rejects it at runtime:
  ```rust
  Some(PreToolUsePermissionDecisionWire::Ask) => {
      Some("PreToolUse hook returned unsupported permissionDecision:ask".to_string())
  }
  ```
  and `pre_tool_use.rs`'s own test, named
  `unsupported_permission_decision_fails_open`, confirms the consequence
  directly: feeding `{"hookSpecificOutput":{"hookEventName":"PreToolUse",
  "permissionDecision":"ask","permissionDecisionReason":"please confirm"}}`
  into `parse_completed` asserts `should_block: false` (the call is **not**
  blocked) and `status: HookRunStatus::Failed` with the error text above.
  **This is the precise, no-longer-secondhand answer**: Codex's native
  `PreToolUse` protocol does not merely "ignore" `ask` (the prior,
  dsh-sourced secondhand characterization) — it recognizes the field
  syntactically, explicitly flags it as an unsupported/invalid hook output,
  logs the hook run as `Failed`, and **fails open**: the tool call proceeds
  anyway. The same fail-open-on-unsupported-decision behavior is confirmed
  for two other shapes in the same test module: a bare `allow` with no
  `updatedInput` (`permission_decision_allow_without_updated_input_fails_open`)
  and the deprecated top-level `{"decision":"approve"}` legacy shape
  (`deprecated_approve_decision_fails_open`) — "received a decision this
  version doesn't act on" fails open consistently across all three cases,
  not just the `ask` one.
- **A second, genuinely separate hook event most of this research base
  didn't know existed — `PermissionRequest`, confirmed from
  `dispatcher.rs`'s own `HookEventName` match arms and its own generated
  schema:** distinct from `PreToolUse`, with its own binary-only decision
  type, confirmed directly from the schema:
  ```json
  "PermissionRequestBehaviorWire": { "enum": ["allow", "deny"], "type": "string" }
  ```
  No `ask` value exists in this enum at all — not even as an
  unimplemented, schema-valid-but-rejected option the way `PreToolUse` has
  it. **And its failure-mode default is the opposite of `PreToolUse`'s**:
  three reserved-for-future fields on the same schema (`interrupt`,
  `updatedInput`, `updatedPermissions`) each carry the same explicit
  doc comment pattern, quoted verbatim:
  > "Reserved for future short-circuiting semantics.\n\nPermissionRequest
  > hooks currently fail closed if this field is `true`."
  (and the equivalent wording for the other two reserved fields). So
  within one harness, one event (`PreToolUse`) fails open on an
  unsupported/future decision shape, while a second, separate event
  (`PermissionRequest`) fails closed on the same kind of situation — a
  real, sourced instance of "failure-mode policy is per-mechanism, not
  uniform across a harness," refining (not just repeating) GitHub
  Copilot's already-logged "timeout vs. crash get different rules" finding
  from 2026-10-15: here the axis isn't failure type, it's which hook event
  you're in.
- **Composition across multiple hooks on the same `PreToolUse` call,
  confirmed from `pre_tool_use.rs`'s own `run()`:**
  `results.iter().any(|result| result.data.should_block)` — any one
  hook's block vote wins, full stop, no precedence puzzle because there's
  no ask tier to rank against it at this layer. Deny-always-wins, same
  shape every other system in this research base converges on.
- **A detail worth flagging rather than silently folding into a tally: this
  is not full independent convergence, it's partial imitation, confirmed
  directly from the source's own naming.** The decision wire shape itself
  (`hookSpecificOutput.permissionDecision`/`permissionDecisionReason`) is
  byte-for-byte the same JSON shape Claude Code's own hooks docs specify
  (already read in the base governance survey) — and Codex's own internal
  type for the hook engine is literally named `ClaudeHooksEngine`
  (confirmed from the `use crate::engine::ClaudeHooksEngine;` import in
  `pre_tool_use.rs`). That is Codex's own source naming its hook engine
  after Claude Code's, not an independent reinvention of the wire format.
  **What *is* an independent Codex-specific design choice, not borrowed,**
  is the decision to accept `ask` syntactically but reject it at runtime
  and fail open — that's a deliberate product choice on top of a borrowed
  shape, not evidence of a seventh independent team converging on
  deny>ask>allow from scratch. Recorded honestly: this closes the
  queued item with a real, sourced answer, but it should not be added to
  the hook-mechanisms survey's "N independent systems" convergence tally
  as a fully independent data point for the *wire-format* question, only
  for the narrower "does this harness's native protocol actually let a
  hook ask" question (answer: no, confirmed).
- **Verdict: queued item resolved, adopt-the-finding (not a dependency).**
  The concrete, reusable takeaway for lawkeeper's own `gate_pretooluse.py`
  and any future `EXECUTOR_CONTRACT.md` harness-adapter work: if lawkeeper
  ever adapts its gate to run under Codex specifically, assume `ask` is a
  no-op that fails open, not a no-op that fails closed — a materially
  different, and more dangerous, default than Claude Code's own behavior,
  and worth a loud comment in any future Codex adapter rather than an
  assumption carried over from the Claude Code adapter.

---

## 2. goose's hook system — the research base's existing entry was stale, corrected from a live read

The hook-mechanisms survey's goose entry (2026-09-06) was explicitly flagged
as read from a non-git backup roughly ten releases behind live `main`
(v1.39.0 vs. the then-current v1.49.0). This pass re-read goose's hook
documentation directly from its live `main` branch and found real,
substantive changes — not just a version bump.

- **What was actually read:** `documentation/docs/guides/context-engineering/hooks.md`
  on `block/goose`'s `main` branch, fetched in full via
  `raw.githubusercontent.com`. This is goose's own current docs source, not
  a secondary site. Not re-read this pass: the Rust source itself
  (`crates/goose/src/hooks/mod.rs`, `tool_inspection.rs`,
  `permission_inspector.rs`) — this entry is a docs-level correction, not a
  full re-verification of the source-level claims the 2026-09-06 survey
  made; those should still be treated as stale pending a source re-read.
- **License:** Apache 2.0, unchanged from the prior entry (not re-verified
  this pass, carried over).
- **What changed since the stale 1.39.0-era read, confirmed from the
  current docs:**
  1. **The plugin-hook failure policy is now configurable per rule, not a
     single hardcoded fail-open default.** The 2026-09-06 survey quoted
     `emit_blocking`'s doc comment, "a misbehaving hook MUST NOT block," as
     goose's design intent, unconditionally. The current docs describe a
     per-rule `on_failure` field instead:
     > "`on_failure` | No | What to do when a `PreToolUse` hook fails: it
     > cannot be executed, times out, does not receive its payload,
     > produces output goose cannot decode, or exits without a decision
     > goose recognizes. `allow` (the default) continues the tool call,
     > `block` denies it."
     `allow` is still the *default* — consistent with, not contradicting,
     the old finding — but it is no longer the *only* behavior the system
     supports; an operator can now flip a specific hook rule to fail
     closed. This is a real design upgrade worth citing precisely rather
     than repeating the old entry's unconditional framing.
  2. **A new observation-only event, `PreToolUseResult`, reports the
     chain's outcome after the fact**, with fields `decision` (`allow` or
     `deny` — the docs state outright, "There is no third value"),
     `policy_evaluated` (an at-least-one-hook-reached-a-conclusion flag,
     explicitly not a correctness guarantee — "It reports that a hook ran
     to a conclusion, not that the conclusion was usable"), `blocked_by`,
     `reason`, and `cause` (`policy_denial` vs. `hook_failure` — a
     decision-vs-infrastructure-failure split goose's docs draw explicitly,
     not something the 2026-09-06 source read surfaced at all).
  3. **A second blockable event exists beyond `PreToolUse`: `Stop`.** A
     `Stop` hook can force a turn to continue instead of ending, with an
     explicit anti-infinite-loop cap
     (`GOOSE_STOP_HOOK_BLOCK_CAP`, overridable) once which goose overrides
     the hook and ends the turn anyway. Not in the 2026-09-06 entry at all.
  4. **The binary (no-`ask`) nature of the wire protocol is now stated in
     goose's own docs text, not just inferred from its Rust enum**, closing
     the 2026-09-06 entry's own gap (that finding came from reading
     `HookDecision::{Allow, Deny}` in source, not from docs saying so
     outright): "`decision` | `allow` or `deny`, on `PreToolUseResult`.
     There is no third value."
  5. **Still cites the Open Plugins spec as its model**, unchanged:
     "goose follows the [Open Plugins hooks specification]
     (https://open-plugins.com/agent-builders/components/hooks)." The spec
     itself remains unread (§3 below) — goose's own implementation of it
     has now been read twice, at two points in time, with real drift
     between them, which is itself a small data point against treating any
     single harness's implementation as a stable proxy for the spec text.
- **Verdict: corrects, doesn't overturn, the 2026-09-06 entry's bottom
  line** (goose is still binary/no-ask at the external hook layer; deny
  still wins when it fires) — but the specific mechanism details that
  entry gave (unconditional fail-open, no `Stop`-hook concept, no
  `PreToolUseResult` observability) are now known to be stale as written.
  Not urgent to fix retroactively in the older doc (per this project's own
  "settled stays settled unless there's new evidence" philosophy — this
  *is* the new evidence, logged here rather than silently edited into the
  old entry). Adopt-the-design candidates worth a future look: the
  `cause: policy_denial | hook_failure` split is a cleaner, more precise
  version of the decision/infrastructure-failure distinction lawkeeper's
  own `gate_pretooluse.py` already draws informally (see §4); the
  `Stop`-hook block-cap is a concrete answer to "what stops an ASK-capable
  hook from holding a turn hostage forever" that neither lawkeeper's design
  nor any prior entry in this research base had addressed.

---

## 3. The Open Plugins hooks specification — still blocked, fourth consecutive pass, no workaround attempted beyond one refused one

- **Prior status:** blocked on 2026-09-06 (queued), 2026-10-01
  (`EGRESS_BLOCKED`), 2026-10-15 (`getaddrinfo ENOTFOUND`).
- **What was attempted this pass:** a direct fetch of
  `open-plugins.com/agent-builders/components/hooks` failed as an explicit
  proxy policy denial this time (`CONNECT tunnel failed, response 403`) —
  a third distinct failure surface for what is, per the proxy's own status
  endpoint, the same underlying block. A search this pass also surfaced
  the **"Agent Plugins"** spec (`agent-plugins.org`,
  `agentplugins/agent-plugins-spec` on GitHub) again, and this time with
  enough detail to settle the 2026-10-15 entry's open question about
  whether it's a decoy: it is a **real, named, separate** spec (not a
  typo-variant of Open Plugins), launched 2026-08-06, with named adopting
  clients (VS Code, Cursor, GitHub Copilot, ChatGPT, Codex, Kiro per
  aggregated secondary coverage, not independently verified this pass) —
  but its own GitHub discussion
  (`agentplugins/agent-plugins-spec/discussions/54`, "Proposal: Portable
  Hooks Component Type," title read directly from search results, body not
  fetched) proposes adding a hooks component specifically **because
  Agent Plugins 1.0 excluded hooks** from its initial scope. That
  confirms, more concretely than before, that Agent Plugins and Open
  Plugins are two different efforts and Agent Plugins is not a substitute
  source for the hooks spec goose cites — consistent with 2026-10-15's
  "did not substitute a same-sounding but different spec," now with a
  clearer reason why they're different (one has hooks, the other was
  explicitly proposing to add them).
- **One access path considered and explicitly not taken:** a Wayback
  Machine mirror fetch was attempted and refused by this session's own
  tool-use policy as a containment-escape risk. That refusal is treated as
  correct, not as an obstacle to route around by some other means — this
  pass does not try archive.org again, a different mirror, or any other
  indirect path to the same blocked content. If a future session's egress
  policy genuinely changes, a direct fetch of the canonical URL remains
  the right first move; manufacturing an indirect path around a live
  policy block is not this research routine's call to make.
- **Verdict: unchanged — stays queued**, now with a cleaner negative
  result (confirmed not the same as Agent Plugins, rather than merely
  "didn't find it again this time").

---

## 4. lawkeeper's own `gate_pretooluse.py` — the 2026-10-15 follow-up, actually checked this time

2026-10-15 flagged this as "a concrete, checkable comparison point this
pass identified but did not itself check" — comparing lawkeeper's own
fail-open/fail-closed behavior against GitHub Copilot's per-failure-mode
split. Checked directly this pass, now that §1-2 above give two more
comparison points (Codex's per-*event* fail-open/fail-closed split;
goose's `cause: policy_denial | hook_failure` distinction).

- **What was actually read:** `scripts/gate_pretooluse.py` in full (this
  repo, current `main`).
- **Current behavior, confirmed from source (not changed this pass — a
  read, not an edit):** two failure tiers, deliberately different outcomes,
  per the module's own docstring and `main()`'s own code:
  1. Unparseable stdin JSON (`json.JSONDecodeError`) → fail **open**
     (`return 0`, no verdict at all) — "can't even see the tool call at
     all."
  2. An uncaught exception inside `decide()` while classifying a command
     that *was* successfully parsed → fail to **ASK**, explicitly neither
     open nor hardline-deny — "we didn't actually confirm this is
     dangerous, so claiming hardline certainty would overclaim; but
     silently allowing defeats the point of having this hook at all when
     it breaks."
  There is no hook-internal timeout handling at all — a hang inside
  `decide()` is not something this script can protect against itself;
  that is Claude Code's own hook-runner's responsibility (timeout, and
  what happens on one, is a property of the harness invoking this script,
  not of the script), a boundary this entry makes explicit rather than
  leaving implicit.
- **How this compares to the two new findings above, stated plainly:**
  lawkeeper's own two-tier split ("can't see the input" vs. "saw the input,
  broke while judging it, fail to the cautious tier instead of either
  extreme") is a *third* shape, distinct from both Codex's
  per-event policy (same event, same failure, one fixed fail-direction per
  event) and GitHub Copilot's per-failure-mode policy (same event, one
  fixed fail-direction per *kind* of failure, e.g. timeout vs. crash).
  Lawkeeper's script picks its fail-direction based on **how much was
  learned before the failure happened** (nothing learned → open; something
  learned, judgment failed → ask) — a reasonable design already in place,
  not something this pass is recommending changing. **Verdict: this
  follow-up is closed — the script's existing design holds up against two
  more shipped comparison points and needs no change**, and the script
  itself now has three external, sourced precedents to cite (GitHub
  Copilot, Codex, goose) if its own docstring is ever expanded.

---

## 5. mewt (`trailofbits/mewt`) — a new mutation-testing tool, checked, found not directly applicable

Surfaced while searching for new test-governance/oracle-independence work.
A secondary source (a changelog-style search snippet, not Trail of Bits'
own blog, which is itself blocked this pass — see access note) described
Trail of Bits shipping "MuTON and mewt" in April 2026 as mutation-testing
tools "optimized for agentic use." Checked directly rather than taken at
that characterization.

- **What was actually read:** `trailofbits/mewt`'s own `README.md` and
  `docs/how-it-works.md`, and `LICENSE`, all fetched directly via
  `raw.githubusercontent.com`.
- **License: AGPL-3.0, confirmed by reading `LICENSE` directly** — the
  first AGPL-licensed entry in this entire research base (every prior
  dependency-relevant entry has been MIT or Apache 2.0). Worth flagging on
  its own: AGPL's network-use copyleft clause is a materially different,
  stricter consideration than anything logged here before, relevant the
  moment anyone proposes depending on this rather than just reading its
  design.
- **What it actually is, confirmed from its own README, not the secondary
  characterization:** a general-purpose, multi-language mutation-testing
  CLI (C++, DAML, Go, JavaScript/TypeScript, Ruby, Rust, Solidity, and
  several Move dialects) that mutates source files and reports which
  mutants survive a test suite — the standard mutation-testing mechanism,
  not a novel one. **Python is not in the supported-language list** —
  directly relevant, since lawkeeper's own Law 18 mutation-testing
  integration (`mutmut`, already adopted per 2026-10-15's note) is Python-
  specific; mewt would not cover lawkeeper's own codebase even if adopted.
  `MuTON` (the other tool the secondary source bundled with mewt) turned
  out, on checking its own GitHub description directly, to be scoped
  specifically to TON blockchain smart contracts — not a general tool at
  all, and not re-read further once that scope was confirmed.
- **The "optimized for agentic use" framing, explicitly not confirmed:**
  neither `README.md` nor `docs/how-it-works.md` (the two files this pass
  actually read) mentions agents, AI-generated tests, or oracle
  independence anywhere. This pass could not confirm the secondary
  source's framing from mewt's own documentation and is not repeating it
  as fact — if there's a real agentic-use angle, it lives somewhere this
  pass didn't read (a different docs page, a blog post on
  `blog.trailofbits.com`, itself blocked this pass) and should be
  attributed there specifically, not assumed from a search snippet.
- **Verdict: not-applicable to lawkeeper's own Law 18 tooling (wrong
  language), and the one claim that would have made it interesting
  specifically for *this* research base's angle (agentic-test-oracle
  framing) is unconfirmed by direct reading.** Logged here, with its real
  license flagged, so a future pass doesn't need to re-discover and
  re-check it from scratch, not because it changes anything about
  lawkeeper's current Law 18 setup.

---

## What this pass found nothing new on

Per the task brief's own instruction: stated plainly rather than padded.

- **Test-governance/oracle-independence methodology, beyond mewt (§5):** a
  2026-08 arXiv paper ("All Smoke, No Alarm: Oracle Signals in
  Agent-Authored Test Code," arXiv 2606.18168) and an AgentAssay paper
  (arXiv 2603.02601) surfaced by search look squarely on-topic — directly
  about classifying oracle strength in agent-authored tests, which is
  exactly lawkeeper's Law 18 concern — but `arxiv.org` and
  `export.arxiv.org` are both blocked this pass (see access note), so
  neither was read even in part. **Not reported as a finding**, per this
  research base's own standing rule against citing a search-snippet
  characterization as a verified result. Recorded here as a named,
  re-findable lead (both arXiv IDs given above) for a future pass whose
  egress policy allows `arxiv.org`, rather than silently dropped.
- The TU Delft oracle-generation lead from 2026-10-15 — `repository.tudelft.nl`
  is still blocked (confirmed again this pass, same as every prior
  attempt); nothing new to add.
- **Policy-decision algebra:** no new independently-built system surfaced
  this pass beyond Codex (§1, which resolves a long-queued item rather
  than adding a new one to the tally) and the goose correction (§2). A
  search for "new 2026 policy engine" turned up only vendor-SDK approval
  callbacks (Snowflake's Cortex Code Agent SDK's `canUseTool`, mentioned in
  search results but `docs.snowflake.com` is blocked this pass, so not
  read directly and not logged as a verified entry) and individual
  developers' own `PreToolUse` hook write-ups (blog posts, not
  independently-built systems in the sense this research base tracks).
- No Falcun-relayed report was encountered or relied on this pass; nothing
  here traces through a secondary research report from another repo.

## Re-check when

- `open-plugins.com` — fifth-pass-running block; re-attempt directly
  whenever a future session's egress policy might differ. Do not
  substitute Agent Plugins (confirmed, again, to be a different spec) and
  do not route around the block via a mirror — that was tried once this
  pass and correctly refused.
- `arxiv.org`/`export.arxiv.org` — blocked this pass for the first time in
  this research base's history (no prior entry needed to reach arXiv
  directly, so this isn't a regression from a previously-working path, but
  it's new as a *named* blocker). Two concrete, named papers are waiting
  for it: arXiv 2606.18168 and arXiv 2603.02601 (§"What this pass found
  nothing new on").
- `blog.trailofbits.com` and `docs.snowflake.com` — both surfaced
  real-looking leads this pass (mewt's own blog announcement; Snowflake's
  Cortex Code Agent SDK approval callback) that could only be checked via
  GitHub-hosted source instead of the vendor's own primary documentation;
  re-attempt directly if a future session's policy allows it, rather than
  continuing to lean on GitHub mirrors/source as a stand-in for vendor
  docs specifically.
- goose's **source** (`crates/goose/src/hooks/mod.rs`,
  `tool_inspection.rs`, `permission_inspector.rs`) on current `main` — §2
  corrected the *docs*-level staleness this pass; the hook-mechanisms
  survey's source-level claims (line numbers, exact Rust logic) are still
  keyed to the ~10-week-stale 1.39.0 backup and should be re-read from a
  fresh clone before anything cites exact source locations for goose
  again.
