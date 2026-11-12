# External scan — 2026-11-12

Weekly scheduled research pass. Scope per the routine's own brief: runtime/
`PreToolUse`-style agent governance, policy-decision algebras (allow/deny/ask),
git-hook distribution/enforcement patterns, and test-governance/oracle-
independence methodology. Not Windwright's domain (acoustics/CAD) and not
Falcun's (evolutionary mutation, epistemic-claim verification) — a harness's
other features are out of scope here even when its governance mechanism is
in scope.

**Access note, carried forward from 2026-11-05 and confirmed unchanged this
pass:** this session's egress proxy allows GitHub (`github.com`,
`raw.githubusercontent.com`, the `api.github.com` search endpoints) and
little else. Every non-GitHub host attempted this pass failed —
`open-plugins.com`, `arxiv.org`, `www.alphaxiv.org`, `agentpatterns.ai`,
`docs.snowflake.com`, `blog.trailofbits.com` all returned `getaddrinfo
ENOTFOUND` (checked directly against the proxy's own status endpoint,
`$HTTPS_PROXY/__agentproxy/status`, which confirms the allowlist is scoped to
GitHub + package registries + a short list of MCP/Anthropic hosts — this is
not a transient failure, it's the environment's actual configured scope).
`WebSearch` itself still works (it does not appear to go through the same
per-host allowlist as `WebFetch`), so this pass used search to find leads and
GitHub source to verify them, same pattern 2026-11-05 established. Everything
below marked "actually read" is GitHub-hosted — a project's own source files
or docs-source Markdown, fetched via `raw.githubusercontent.com` directly, or
inspected via a local `curl`+`grep`/`sed` pass against the downloaded file for
exact line numbers.

---

## 1. Gemini CLI's policy engine — a genuinely new primary source, and a real divergence from the deny>ask>allow convergence story

Found via `WebSearch`, surfaced by a small third-party tooling survey (§4
below) that named it as having "the cleanest published rule schema for this
job." Not previously read anywhere in this research base — Gemini CLI has
not appeared in `RESEARCH_agent_harness_landscape.md`,
`RESEARCH_harness_governance_survey.md`, or
`RESEARCH_harness_hook_mechanisms_survey.md` before this entry.

- **What was actually read:** `docs/reference/policy-engine.md` on
  `google-gemini/gemini-cli`'s `main` branch, fetched in full (505 lines) via
  `raw.githubusercontent.com` — this is Google's own current docs source for
  the mechanism, not a secondary writeup.
- **License:** Apache 2.0, confirmed by reading `LICENSE` directly.
- **The actual decision model, quoted from source:** rules live in `.toml`
  files; each rule carries `conditions` (tool name, `argsPattern`/
  `commandPrefix`/`commandRegex`, `interactive`, `modes`), a `decision`
  (`allow` | `deny` | `ask_user`), and a `priority` (0–999). **The core
  mechanism is explicitly priority-number-based, not a fixed-type
  precedence:** "the rule with the highest priority wins" — any decision
  type can win a given tool call purely by having a higher number, there is
  no hardcoded rule that `deny` always beats `ask_user` always beats `allow`
  the way Claude Code/Omnigent/dsh/Hermes/goose/Codex's own `PreToolUse`
  chain all independently converged on (confirmed by both prior surveys in
  this research base).
- **The tiering that makes this safe in practice, not just a flat priority
  number:** five tiers — Default (base 1) < Extension (2) < Workspace
  (3, currently disabled per a linked, open GitHub issue #18186) < User (4)
  < Admin (5) — with `final_priority = tier_base + (toml_priority / 1000)`.
  This guarantees Admin always outranks User/Workspace/Default regardless of
  the in-file `priority` value, while still letting an author order rules
  *within* a tier via the 0–999 number. This is a concrete, shipped
  implementation of exactly the "tiered policy precedence (session > agent >
  server-wide)" idea `RESEARCH_agent_harness_landscape.md` flagged from
  Omnigent as "a pattern worth stealing if lawkeeper ever needs per-branch or
  per-contributor rule variance" (Entry 1, point 2) — except Gemini CLI's
  version is priority-arithmetic, not Omnigent's session>agent>server-wide
  evaluation-order scheme, and the two are not interchangeable designs.
- **One more mechanism, not a precedence detail — `deny` has a side effect
  beyond blocking:** "For global rules (those without an `argsPattern`),
  tools that are denied are **completely excluded from the model's memory**"
  — the model never sees the tool as an option at all, which the docs frame
  as both more secure and a context-window saving. This is a different shape
  than every prior entry in this research base (all of which gate a call
  the model already attempted) — it's pre-emptive tool-list filtering, not
  post-hoc gating. `ask_user` degrades to `deny` automatically in
  non-interactive/headless mode, per the docs' own parenthetical — a third,
  independently-arrived-at instance (after dsh's `approval/policy: 'never'`
  and Hermes' `approvals.mode`) of a CI/headless-safe deterministic fallback
  for the ask tier specifically.
- **Does this overturn the "five independent systems converge on
  deny>ask>allow" finding from the hook-mechanisms survey?** No, but it
  sharpens it: Gemini CLI is a sixth independently-built system solving the
  same problem, and it **did not** converge on a fixed three-tier algebra —
  it solved rule-conflict resolution with pure numeric priority instead. Read
  honestly, this means the "natural algebra" claim from the prior survey
  should be scoped to the systems that actually have a fixed verdict-type
  ordering (still five, still a strong signal), not stretched to "all
  systems, no exceptions" — Gemini CLI is a real, sourced counter-example to
  universality, not a sixth confirmation. This is worth stating plainly
  rather than silently filed under the existing tally.
- **One concrete, worth-logging adoption for lawkeeper's own design:** the
  `final_priority = tier_base + (fine_grained / 1000)` formula is a cheap,
  concrete mechanism for "coarse tier always wins, fine-grained order
  preserved within a tier" that lawkeeper's own `src/guardrail/` could reuse
  directly if/when a tiered-authority model (e.g., an org-level law vs. a
  per-repo override) is ever actually needed — simpler to implement than
  Omnigent's evaluation-order-based tiering, at the cost of needing a
  numeric budget per tier decided up front.
- **Verdict: adopt-the-design (the tier-base-plus-fractional-priority
  formula, and the deny-removes-from-model-context idea) for a future
  tiered-authority extension to `src/guardrail/`; not a dependency** — Gemini
  CLI is a large Node/TypeScript-plus-Python host application, not something
  lawkeeper's Python git-hook tooling would realistically vendor for this one
  mechanism. Also log explicitly: **this is the first system in this
  research base found to deliberately not implement deny>ask>allow as a
  fixed ordering**, which matters for how confidently `EXECUTOR_CONTRACT.md`
  or any future design doc cites the convergence finding as universal.

---

## 2. Codex's `execpolicy` crate — a second, separate Codex governance mechanism, distinct from the `PreToolUse`/`PermissionRequest` hooks already covered

Found by following up on the same tooling-survey lead (§4) that named Gemini
CLI, which separately described a Codex "exec-policy engine" with a Starlark
rule language — a mechanism this research base had not read before. Every
prior Codex entry in this research base (`RESEARCH_EXTERNAL_SCAN_2026-10-08.md`
§2, `RESEARCH_EXTERNAL_SCAN_2026-11-05.md` §1) is about the hook engine
(`codex-rs/hooks/`, `PreToolUse`/`PermissionRequest` events) — a JSON-wire,
externally-scriptable layer. `execpolicy` is a structurally different,
built-in mechanism living in a separate crate.

- **What was actually read, via `raw.githubusercontent.com` against
  `openai/codex`'s `main` branch:**
  - `codex-rs/execpolicy/README.md` (full, 99 lines)
  - `codex-rs/execpolicy/examples/example.codexpolicy` (full — a real
    `.codexpolicy` rule file, not a snippet)
  - `codex-rs/core/src/exec_policy.rs`: the `BANNED_PREFIX_SUGGESTIONS`
    constant definition (lines 64–153) and its one call site inside
    `derive_requested_execpolicy_amendment_from_prefix_rule` (lines
    1065–1100)
  - `codex-rs/shell-command/src/bash.rs` (first ~40 lines: `try_parse_shell`
    and the doc comment and signature of
    `try_parse_word_only_commands_sequence`)
  - `codex-rs/shell-command/Cargo.toml` and `codex-rs/execpolicy`'s own
    directory listing (via `gh api search/code`, confirming file paths, not
    full file contents for every file named)
  - Confirmed directly: `LICENSE` at the repo root is Apache 2.0 (same
    license already confirmed for the hooks engine in an earlier entry).
  - **Not read:** `codex-rs/execpolicy/src/policy.rs`'s full
    `check`/`check_multiple` implementation bodies (only their signatures,
    via `grep`), `parser.rs`, `amend.rs`, or the Windows-specific tests —
    enough was read to confirm the rule language and composition semantics
    stated below, not the full evaluation engine internals.
- **The actual rule language, confirmed from the README and the example
  file, not inferred:** `prefix_rule(pattern=[...], decision?, justification?,
  match?, not_match?)` plus `host_executable(name=..., paths=[...])`,
  written in **Starlark** syntax (the same embeddable, deliberately
  non-Turing-complete DSL Omnigent chose for its own CEL-based untrusted-rule
  surface, documented in `RESEARCH_agent_harness_landscape.md`'s deeper pass
  — a second, independently-chosen instance of "use a sandboxed configuration
  language, not a general scripting language, for a rule an operator but not
  necessarily a maintainer writes"). `decision` takes exactly three values —
  `allow` (the default), `prompt`, `forbidden` — a three-tier vocabulary
  that maps directly onto the deny/ask/allow shape this research base has
  tracked throughout, under different names.
- **Composition across multiple matching rules — quoted directly from the
  README, not reconstructed:** "The effective `decision` is the strictest
  severity across all matches (`forbidden` > `prompt` > `allow`)." This is
  the same deny-beats-ask-beats-allow ordering as every fixed-tier system
  this research base has read, confirmed here in a seventh codebase (after
  Claude Code, Omnigent, dsh, Hermes, goose, and Codex's own separate hooks
  engine) — but it is worth being precise about what's actually being
  counted: this is the *same organization's* second mechanism, not a seventh
  independent team, so it should be logged as further confirmation of the
  algebra's robustness within one codebase choosing it twice independently
  (hooks engine and execpolicy are separate Rust crates with no shared
  evaluation code, per the crate layout), not tallied as a seventh
  independent *organization* alongside the hook-mechanisms survey's count of
  five (now six, after Codex's own hooks engine was already factored in
  there) plus Gemini CLI's explicit non-convergence (§1).
- **A genuinely novel idea this specific entry adds, not present anywhere
  else in this research base: policy rules carry their own inline unit
  tests, validated at load time.** The README states `match`/`not_match`
  "supply example invocations that are validated at load time (think of them
  as unit tests)" — confirmed directly in `example.codexpolicy`, where every
  `prefix_rule` ships 2–3 `match` examples and, for the one `forbidden` rule
  (`git reset --hard`), explicit `not_match` examples (`git reset --keep`,
  `git reset --merge`) proving the rule doesn't over-match a safer sibling
  command. If a rule's own examples fail against the rule's own pattern,
  the policy presumably fails to load (not independently verified — the
  actual load-time validation code in `parser.rs` was not read this pass,
  only the README's description of the behavior and the example file's
  consistent use of the convention). This is directly, concretely relevant
  to a known lawkeeper gap: `scripts/guard_branch.py` and friends have no
  self-test convention baked into the rule *data* itself — tests live
  entirely in `tests/test_guard_scripts.py`, separate from the rules they
  check. A rule-file format that fails to load unless its own stated
  examples pass is a cheap, concrete mechanism upgrade worth considering for
  any future declarative (not hand-written-Python) rule surface lawkeeper
  adds — directly actionable for the Law 15 branch-guard rules this research
  base has already flagged as a hardline-tier candidate.
- **The `BANNED_PREFIX_SUGGESTIONS` mechanism, confirmed precisely —
  narrower than a secondary source's characterization of it:** a search
  result characterized this list as refusing "to ever allow-list bare
  interpreters." Reading the actual call site (`exec_policy.rs:1077-1082`)
  shows this is more specific: the list is consulted only inside
  `derive_requested_execpolicy_amendment_from_prefix_rule` — the function
  that proposes an **auto-generated permanent allow-rule amendment** after a
  human approves a one-off command (an "approve this prefix forever" flow,
  the same shape as dsh's `'allowed-once'` vs. permanent-allowlist
  distinction already logged in the hook-mechanisms survey). If the
  user-approved command's prefix exactly matches one of ~40 banned prefixes
  (`bash`, `/bin/bash -c`, `python`, `env`, `git`, `cmd.exe`, `fish`, `lua`,
  etc. — interpreters, shells, and other prefixes too broad to safely
  blanket-approve), the function returns `None` and **no amendment is
  suggested at all** — the one-off approval still happens, but nothing gets
  auto-promoted to a standing allow rule. This is a guard on the
  *convenience auto-amendment path specifically*, not a hard block on ever
  writing such a rule by hand in a `.codexpolicy` file — a real, useful
  precision correction over the secondary source's looser framing, reached
  by reading the call site rather than trusting the characterization.
- **Compound-command decomposition, confirmed directly from source, resolving
  the specific mechanism a secondary source named but this research base had
  not verified:** `codex-rs/shell-command/src/bash.rs` does use
  `tree-sitter-bash` (confirmed in its own `Cargo.toml` and the `use
  tree_sitter_bash::LANGUAGE as BASH` import), via a function named
  `try_parse_word_only_commands_sequence` whose own doc comment states it
  parses "a script which may contain multiple simple commands joined only by
  the safe logical/pipe/sequencing operators: `&&`, `||`, `;`, `|`" and
  returns `None` — fails closed to "not safely decomposable," not a
  best-effort partial parse — the moment the parse tree contains anything
  outside an explicit allowed-node-kind list (parentheses, redirections,
  substitutions, control flow are named exclusions in the function's own
  comment). This is a materially more precise finding than the secondary
  source's "splits into sub-commands evaluated independently" framing: the
  real behavior is "decompose only when every sub-command is syntactically
  plain, otherwise refuse the decomposition entirely" — a fail-closed
  design, not a general splitter. Directly relevant if lawkeeper's own
  future command-string detection layer (already scoped in
  `RESEARCH_harness_hook_mechanisms_survey.md`'s closing recommendation)
  ever needs to handle compound/chained Bash commands rather than treating
  the whole string as one opaque unit — this is a concrete, sourced
  precedent for "decompose conservatively, fail closed on anything you can't
  cleanly split" rather than attempting a general shell parser.
- **Verdict: adopt-the-design (Starlark as the sandboxed rule DSL, rules
  shipping their own load-time-validated examples, fail-closed conservative
  compound-command decomposition via a real parser rather than regex
  splitting), not a dependency** — `codex-execpolicy` is a Rust crate
  embedded in a large CLI; vendoring it for lawkeeper's Python tooling has no
  realistic integration path, same reasoning already applied to every other
  non-Python system in this research base. The self-testing-rule-file idea is
  the single most concrete, lawkeeper-specific takeaway from this entry.

---

## 3. Codex's `core/src/tools/approvals.rs` — the open follow-up from 2026-11-05, now actually read

2026-11-05's §1 left this open: when a `PermissionRequest` hook fold resolves
to `None` (no hook decided), the module docstring said "the normal approval
flow continue[s]," but whether that flow defaults to a human prompt, an
auto-approve, or something else was unverified. Read directly this pass.

- **What was actually read:** `codex-rs/core/src/tools/approvals.rs`, the
  resolution logic specifically (lines ~600–710: the `match` on
  `run_permission_request_hooks`'s result, and `request_reviewer_approval`'s
  body), plus `ApprovalContext::requires_human_approval` (lines 70–76). Not
  read: the rest of the 1001-line file (telemetry/recording, MCP-specific
  and network-approval branches past the core resolution match, the
  `request_guardian_approval` implementation itself).
- **The actual fallback chain, confirmed from source, quoted precisely:**
  a comment directly above the match states the invariant outright —
  "Hook denials always win. Managed checkpoints require a person even when a
  hook allows the action or the session uses automatic review." The match
  arms: a hook `Deny` always wins regardless of anything else; a hook
  `Allow` is accepted as final **only if** `!ctx.requires_human_approval()`;
  and — this is the answer to last week's open question —
  `Some(PermissionRequestDecision::Allow) | None` (a hook explicitly
  allowing a managed-checkpoint action, *or* no hook deciding at all) both
  fall through to the same place: `request_reviewer_approval`. That
  function's own body is the real fallback chain: **(1)** if
  `requires_human_approval()` is true, go straight to `user_prompt.await` —
  a managed checkpoint always reaches a person, no automated review can
  substitute; **(2)** otherwise, try `request_guardian_approval` (Codex's
  automated/LLM-based reviewer, "Guardian") first; **(3)** if Guardian
  returns no decision, fall back to `user_prompt.await` as well. So "the
  normal approval flow continues" when no hook decides is **not** an
  auto-approve default of any kind — it's a reviewer chain that always
  terminates in either a human prompt or Guardian's own explicit decision,
  never a silent allow. This resolves last week's open question concretely,
  in lawkeeper's favor of the more cautious reading, not the more dangerous
  one.
- **One more detail worth logging, found while reading this:** the same
  match block re-runs `check_approval_requirement` *after* an `Approved`
  resolution, and can still downgrade it to `denied` — approval is not
  final the instant a reviewer says yes; a second, independent check can
  still veto post-approval (and separately, a human-required action whose
  cancellation token has already fired is converted to `Abort`, not treated
  as approved). This is a second-look/double-check pattern distinct from
  anything previously logged in this research base's survey of approval
  flows — worth naming as a candidate idea (a cheap, mechanical "re-verify
  right before acting on an approval, not just right after receiving it")
  for any future lawkeeper ASK-tier implementation that has a gap between
  "approved" and "the thing the approval was for actually executes."
- **Verdict: this follow-up is closed.** Adopt-the-finding (the reviewer
  chain never silently defaults to allow; a second post-approval check
  exists), not a dependency — same categorical reasoning as every other
  Codex-internal Rust mechanism in this research base.

---

## 4. The tooling survey that surfaced both new leads above (`YoraiLevi/claude-command-policy`) — a minor project, checked directly rather than cited from its own description

`WebSearch` for new policy-engine candidates surfaced a small, individual
GitHub repository whose own description read "Data-driven command-steering
PreToolUse hook for Claude Code (allow/ask/deny + custom teaching messages)."
Checked directly, per this research base's standing rule against trusting a
project's self-description.

- **What was actually read:** the repo's `README.md` (full) and
  `docs/TOOLING-SURVEY.md` (the first ~60 lines of a longer document,
  enough to read its entries on everything-claude-code, Claude Code's own
  `hookify` plugin, Gemini CLI, Codex's `exec_policy`, OpenHands, Cline, and
  goose — the two entries that led to §1 and §2 above). The repo's own
  engine (`command-policy.jq`, `command-policy.sh`) was read only via the
  README's description of its control flow, not the actual `jq`/`bash`
  source files.
- **What it actually is, confirmed from its own README, not just the
  description:** a **parked** (explicitly marked "PARKED... not wired into
  the live global settings") personal/house-style steering tool — matches
  shell command tokens against a JSON rules file and returns
  `permissionDecision` with a custom teaching message, **fail-open by
  design** if its own `jq` engine or config is missing ("Steering tool, not
  a gate" — the README's own words). Precedence is stated as
  "order-independent... deny > ask > allow" — **an eighth instance of the
  same ordering**, though from a single individual's personal, unstarred,
  currently-inactive project, not a production system with real usage —
  this research base's standing discipline (state what was actually
  verified, don't inflate a weak source) means this should be logged as a
  low-weight data point, not folded into the "N independent production
  systems" tally the hook-mechanisms survey already built from Claude
  Code/Omnigent/dsh/Hermes/goose/Codex.
- **License / stars / activity:** the GitHub API returned no license and no
  stargazer count for this repo (both fields came back `None`/absent) —
  flagged explicitly rather than guessed at. Not a dependency candidate for
  any reason, license included.
- **The one thing of lasting value from this entry: its own
  `docs/TOOLING-SURVEY.md` is a reasonably well-sourced map of ~48
  command-gating tools**, each tagged with a `kind` (host-agent, cc-hook,
  policy-engine, etc.) and a one-line mechanism summary, dated 2026-06-27.
  Two of its entries (Gemini CLI, Codex's `exec_policy`) led directly to the
  substantive, independently-verified findings in §1 and §2 above. The
  survey itself is a secondary source (a personal aggregation, not a vendor
  doc or a paper) and nothing in it was cited here as fact without
  independently re-reading the actual primary source first — it functioned
  as a lead-generation index, not as evidence in its own right.
- **Verdict: not-applicable as a dependency or a design pattern** (it's a
  thin personal convenience script, already "parked" by its own author);
  **its survey document is worth remembering as a re-findable index of
  candidates** the next time this routine needs a fast map of what's out
  there, but every individual claim in it still needs the same
  direct-primary-source check this pass gave two of its entries, not a
  cited-as-is pass-through.

---

## 5. goose's hook source, re-read on current `main` (v1.59.0) — refreshes the staleness `RESEARCH_EXTERNAL_SCAN_2026-11-05.md` flagged, but only partially

2026-11-05's "Re-check when" list flagged that the hook-mechanisms survey's
goose *source*-level claims (exact line numbers, Rust logic in
`tool_inspection.rs`/`permission_inspector.rs`/`hooks/mod.rs`) were still
keyed to a ~10-week-stale 1.39.0 backup, even after 2026-11-05 itself
refreshed the *docs*-level account. This pass re-reads `hooks/mod.rs`
directly from source.

- **What was actually read:** `crates/goose/src/hooks/mod.rs` on
  `block/goose`'s current `main` branch, fetched in full (2,224 lines) via
  `raw.githubusercontent.com`, then inspected with `grep -n`/`sed` for the
  specific declarations below. **Not re-read this pass:**
  `tool_inspection.rs` or `permission_inspector.rs` — those two files remain
  keyed to the stale 1.39.0 backup and should still be treated as
  unverified against current `main` until a future pass reads them
  directly; this entry closes only the `hooks/mod.rs` portion of the
  staleness flag, not all of it.
- **Version check:** `Cargo.toml` on current `main` reports `version =
  "1.59.0"` — ten minor releases ahead of the version 2026-11-05's own §2
  (docs-level) entry was written against context for (goose's docs don't
  carry a version number directly, but the source crate's version confirms
  this is materially newer than both the original 1.39.0 backup and
  whatever state existed on 2026-11-05).
- **Confirmed, with exact current-`main` line numbers (none of this
  contradicts 2026-11-05's docs-level account; it supplies the source-level
  citations that account was written without):**
  - `pub enum HookDecision { Allow, Deny { reason: String, plugin: String }
    }` — lines 349–352. Still binary, no third value, exactly as both prior
    entries found.
  - `enum OnFailure { #[default] Allow, Block }` — lines 185–189, confirming
    2026-11-05's docs-level finding (`on_failure` is now configurable
    per-rule, `Allow` the default) is accurate at the source level too, not
    just in the docs text.
  - `pub enum HookEvent` — lines 54–66, twelve variants, same list
    2026-11-05's docs-level read already named (`PreToolUse`,
    `PreToolUseResult`, `PostToolUse`, `PostToolUseFailure`, `SessionStart`,
    `SessionEnd`, `UserPromptSubmit`, `BeforeReadFile`, `AfterFileEdit`,
    `BeforeShellExecution`, `AfterShellExecution`, `Stop`) — confirmed at the
    source level, not just the docs.
  - `pub(crate) enum HookOutcomeCause { PolicyDenial, HookFailure }` — lines
    355–358, matching 2026-11-05's `cause: policy_denial | hook_failure`
    docs-level finding exactly, now also confirmed against source.
  - `error_type: "hook_failed"` (line ~397) vs. `error_type: "hook_denied"`
    (line ~404) — two distinct, separately-named failure strings for the two
    causes, confirmed in source, matching the docs' separate messaging
    ("could not complete... configured to block on failure" vs. a denial
    message that "includes 'Do not retry'").
  - A dedicated test (confirmed around line 1771) explicitly asserts
    `error_type == "hook_denied"` for the policy-denial path and
    (line ~1781) `error_type == "hook_failed"` for the infrastructure-failure
    path — the distinction is unit-tested, not just documented prose.
- **Verdict: partially closes the 2026-11-05 staleness flag.** `hooks/mod.rs`
  is now re-confirmed against current `main` with real line numbers;
  `tool_inspection.rs` and `permission_inspector.rs` remain open, carried
  forward to this pass's own "Re-check when" list below. No design
  conclusion changes — this is a citation refresh, not a new finding.

---

## What this pass found nothing new on

Per the task brief's own instruction: stated plainly rather than padded.

- **Test-governance/oracle-independence methodology:** `WebSearch` surfaced
  four specific, named candidates this pass could not verify directly
  because the hosts are blocked (see access note) — two carried over from
  2026-11-05 (arXiv 2606.18168, "All Smoke, No Alarm: Oracle Signals in
  Agent-Authored Test Code"; arXiv 2603.02601, AgentAssay) and two new this
  pass: **arXiv 2603.18059** (a March 2026 paper proposing a policy DSL with
  `allow`/`deny` rules plus a `REQUIRE_APPROVAL` outcome — directly
  ask-tier-shaped, if it holds up) and **arXiv 2606.19464** (a June 2026
  paper reportedly arguing flat permit/deny engines like Cedar and OPA lack
  first-class obligations/conflict-resolution support — a direct extension
  of the Cedar/OPA entries already in `RESEARCH_harness_governance_survey.md`
  §1). None of the four was read even in part; `arxiv.org`,
  `export.arxiv.org`, and `www.alphaxiv.org` (tried as an alternative mirror
  host, not a workaround of the arxiv.org block specifically — it is its own
  independently-existing platform — and also blocked) all failed with
  `ENOTFOUND` this pass. **Not reported as findings**, per this research
  base's standing rule against citing a search-snippet characterization as a
  verified result — recorded here as four named, re-findable leads for a
  future pass whose egress policy allows at least one of these hosts.
  GitHub repository search for new, general-purpose agentic-test-oracle or
  mutation-testing tools (`test oracle independence`, `agent authored tests
  mutation score`, `mutation testing oracle agent generated tests`) returned
  zero results each — no new GitHub-hosted candidate surfaced this pass
  beyond mewt (already logged, not-applicable, 2026-11-05 §5).
- **`docs.snowflake.com` and `blog.trailofbits.com`:** both re-attempted
  directly this pass (not just left as a carried-over flag) and both failed
  `ENOTFOUND`, same as 2026-11-05. Snowflake's Cortex Code Agent SDK
  `canUseTool` callback (named by search results again this pass) remains
  unverified from primary source.
- **`agent-plugins.org` / the Agent Plugins spec:** not re-investigated this
  pass — 2026-11-05 already settled that it is a distinct, non-substitute
  spec from Open Plugins; nothing new to add or re-check here.
- **pre-commit's own extension model:** per this task's own brief, already
  closed out by the 2026-10-01/2026-10-08 scans — not re-opened this pass,
  consistent with "settled stays settled."
- No Falcun-relayed report was encountered or relied on this pass; nothing
  here traces through a secondary research report from another repo.

## Re-check when

- **`open-plugins.com`** — re-attempted directly this pass, failed
  `getaddrinfo ENOTFOUND` (a fourth distinct failure surface across five
  attempts: queued 2026-09-06, `EGRESS_BLOCKED` 2026-10-01, `ENOTFOUND`
  2026-10-15, `403 CONNECT` 2026-11-05, `ENOTFOUND` again 2026-11-12). Still
  the single longest-queued unresolved item in this research base. Re-attempt
  directly whenever a future session's egress policy might differ; do not
  substitute Agent Plugins (settled as a different spec) and do not route
  around the block via a mirror (tried once on 2026-11-05, correctly
  refused by that session's own tool-use policy; not re-attempted since).
- **arXiv (`arxiv.org`/`export.arxiv.org`) and `www.alphaxiv.org`** — four
  named papers now waiting: 2606.18168, 2603.02601, 2603.18059, 2606.19464
  (see "What this pass found nothing new on" above). Try arXiv's own domain
  first if a future pass's policy allows it; alphaxiv.org is a candidate
  fallback host, also currently blocked.
- **`docs.snowflake.com`** — Snowflake's Cortex Code Agent SDK `canUseTool`
  callback is a named, re-findable lead, still unverified after two
  consecutive blocked attempts (2026-11-05, 2026-11-12).
- **`blog.trailofbits.com`** and **`agentpatterns.ai`** — the latter is new
  this pass (surfaced by search with content specifically about protecting a
  test oracle from the agent that writes it — directly on-topic for Law 18 if
  it turns out to be a real, substantive pattern rather than a thin blog
  post; unverified either way, blocked both times tried).
- **goose's `tool_inspection.rs` and `permission_inspector.rs`** — still
  keyed to the 1.39.0 backup; `hooks/mod.rs` was refreshed against current
  `main` this pass (§5), but these two files were not re-read and should be
  before anything in this research base cites their exact line numbers or
  logic again.
- **`codex-rs/execpolicy/src/policy.rs`'s `check`/`check_multiple` bodies,
  `parser.rs`'s load-time validation logic** — this pass confirmed the rule
  language and the strictest-severity composition rule from the README and
  example file, but did not read the engine internals that actually enforce
  "a rule's own `match`/`not_match` examples must pass or the policy fails
  to load" — worth a direct read before citing that specific mechanism as
  confirmed-from-source rather than confirmed-from-documentation.
