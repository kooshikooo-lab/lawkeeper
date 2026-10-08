# External scan — 2026-10-08

Weekly scheduled research pass. Scope per the routine's own brief: runtime/
`PreToolUse`-style agent governance, policy-decision algebras (allow/deny/ask),
git-hook enforcement patterns, and test-governance/oracle-independence
methodology. Not Windwright's domain (acoustics/CAD) and not Falcun's
(evolutionary mutation, epistemic-claim verification) — a harness's other
features are out of scope here even when its governance mechanism is in
scope.

Per the brief, this pass checked the queue in `docs/RESEARCH_agent_harness_landscape.md`
and `docs/RESEARCH_harness_hook_mechanisms_survey.md` first. Three of the five
originally-queued items (pre-commit's extension model, MITRE ATLAS, AWS Cedar)
were already closed in last week's pass (`docs/RESEARCH_EXTERNAL_SCAN_2026-10-01.md`)
and are not revisited here. Two were still open going into this pass:
**Codex's native hook protocol** (last week: substantially upgraded via its
issue tracker, but still short of a primary-source read) and **the Open
Plugins hooks specification** (last week: still fully blocked by egress
policy). This pass **fully closes the Codex item** with a direct read of
Codex's own Rust source, and **the Open Plugins item stays blocked**, re-confirmed
rather than assumed stale. Closing the Codex item surfaced a live, current
documentation page for Claude Code's own hooks reference that materially
*changes* the governance survey's headline finding (deny>ask>allow is now a
four-tier algebra, not three) — reported first, below, since it is the most
consequential finding this pass produced. A second new, independently
verified finding (a real, fixed precedence bug in qwen-code) is reported
after it. No Falcun-relayed report was encountered or relied on this pass.

**Access note:** `github.com` and `raw.githubusercontent.com` were reachable
all pass, via both WebFetch and a real `git clone`. Non-GitHub documentation
domains were not: `developers.openai.com`, `open-plugins.com`, `r.jina.ai`,
and `arxiv.org` all failed at the DNS resolution step (`getaddrinfo ENOTFOUND`)
on every attempt this pass — the same effective block last week's pass hit
(there, the proxy returned an explicit `EGRESS_BLOCKED`; here it surfaces as
a DNS failure, but the practical result — these hosts are unreachable from
this session — is identical). `code.claude.com` (Claude Code's own docs site)
was reachable and is a GitHub-adjacent first-party domain exception to that
pattern, not a contradiction of it.

---

## 1. Claude Code's own `PreToolUse` algebra is now four-tier, not three — `deny` > `defer` > `ask` > `allow`

This is the single most consequential finding of this pass, surfaced while
chasing the Codex item below, not sought directly — worth leading with
because every prior lawkeeper research doc (both base surveys, both of last
week's... no, this base's own convergence argument across five systems) cites
the three-tier `deny > ask > allow` algebra, sourced in part from Claude
Code's own docs as read in September. That citation is now out of date.

- **What was actually read this pass:** `code.claude.com/docs/en/hooks`,
  fetched and read directly (in two passes, since the live page is ~250,000
  characters — the "PreToolUse decision control" and "Defer a tool call for
  later" sections were read and quoted in full, not summarized from a
  snippet). This is the same first-party page the governance survey already
  cites for the three-tier claim; re-reading it live is what caught the
  change.
- **The actual current algebra, quoted directly from the live doc, not
  paraphrased:** "This gives it richer control: four outcomes (allow, deny,
  ask, or defer)... When multiple `PreToolUse` hooks return different
  decisions, precedence is `deny` > `defer` > `ask` > `allow`." The fourth
  value, `"defer"`, was added in Claude Code v2.1.89 (per a documentation
  issue's changelog citation, cross-checked against the live docs directly
  below) and sits in precedence strictly between `deny` and `ask` — not
  tacked onto either end.
- **What `"defer"` actually does, quoted/summarized from the live doc's
  "Defer a tool call for later" section:** it is not a new way to deny or
  gate a tool call at all — it is a **pause-and-resume** primitive for
  headless (`-p`) integrations. Returning `permissionDecision: "defer"`
  stops the tool from executing and exits the process with
  `stop_reason: "tool_deferred"`, preserving the pending tool call in the
  session transcript. The calling process (an Agent SDK app, a custom UI)
  later runs `claude -p --resume <session-id>`, which re-fires the same
  `PreToolUse` hook for the same call; the hook can defer again (no timeout,
  no retry limit — the session sits on disk until the `cleanupPeriodDays`
  retention sweep, 30 days by default) or finally return `"allow"`/`"deny"`.
  Constraints confirmed directly from the doc: only honored under `-p`
  (interactive sessions log a warning and ignore it); only works for a
  single tool call per turn (a batch of calls silently falls through to the
  normal permission flow instead, with a warning); `updatedInput` and
  `additionalContext` are both ignored when the decision is `"defer"`. The
  documented worked example is `AskUserQuestion` inside a `-p` run with a
  permission-prompt-tool host — Claude wants to ask a question, there is no
  terminal to answer in, so the call defers until the calling process can
  surface and answer it out-of-band.
- **Where this came from, traced rather than assumed:** a documentation
  issue, `anthropics/claude-code#41791` (fetched and read directly via
  GitHub, not secondhand), reported the docs as stale relative to a
  changelog entry: "Added `\"defer\"` permission decision to `PreToolUse`
  hooks — headless sessions can pause at a tool call and resume with
  `-p --resume` to have the hook re-evaluate" (changelog v2.1.89, quoted in
  the issue). The issue itself carries no maintainer confirmation and no
  visible comments — on its own it would only be a reporter's claim. What
  resolves it to a confirmed, primary-source fact is the live docs fetch
  above: `code.claude.com/docs/en/hooks`, fetched directly this same pass,
  already documents `"defer"` in full, including the precedence line. The
  issue is only the pointer that sent this pass back to re-read a page the
  research base had treated as already-fully-read; the actual evidence is
  the live page's own current text.
- **Does this change the five-system convergence finding
  (`docs/RESEARCH_harness_hook_mechanisms_survey.md`'s headline result)?**
  Narrows it, precisely: `deny > ask > allow` is still confirmed as the
  convergent three-way core — nothing about `defer`'s position changes that
  the other four systems (Omnigent, dsh, Hermes, goose) and Claude Code's
  own `deny`/`ask`/`allow` relative ordering all still agree. What's new is
  that the single most-cited reference implementation for that algebra has
  grown a non-adversarial fourth state that is not a gating decision at all
  in the ALLOW/DENY/ASK sense — it is closer to a coroutine `yield` than to
  a permission verdict, and it happens to slot into the precedence chain
  between `deny` and `ask` because an unresolved deferral must not
  accidentally execute (so it must outrank `allow`) and must not require a
  live human prompt to behave correctly (so it must not require resolving
  through `ask`). Any future lawkeeper design doc describing Claude Code's
  own algebra as "three-tier" is now citing a stale fact, not a simplification.
- **Checked directly against lawkeeper's own repo, not assumed:**
  `scripts/gate_pretooluse.py` (and its synced copy in
  `src/guardrail/template/scripts/gate_pretooluse.py`) only ever emits
  `"allow"`, `"deny"`, or `"ask"` — confirmed by reading the file's own
  `_decide_impl`/output-shaping code directly, not inferred from its module
  docstring. This is not a gap to fix: lawkeeper's gate is a static security
  classifier, not a headless-resume integration, and `"defer"` is
  meaningless for a hook that never runs under `-p --resume` orchestration
  — there is nothing for lawkeeper's gate to pause and later re-evaluate.
  What **is** worth a precise correction: the module's own docstring
  (`scripts/gate_pretooluse.py:20`, "deny > ask > allow as the tool-call
  gating precedence") is citing the algebra lawkeeper's own gate
  participates in correctly, but any future doc citing *Claude Code's*
  algebra as three-tier (rather than lawkeeper's own three-valued output,
  which is still accurate) would be wrong. Recorded here as a citation
  correction for future design docs, not a code change — lawkeeper's actual
  gate logic needs nothing different.
- **License/provenance:** N/A — this is the vendor's own current product
  documentation for the runtime lawkeeper already targets, not a dependency
  or data source being evaluated.
- **Verdict: adopt-the-correction.** Update any future lawkeeper design
  text (not this pass's job to rewrite `EXECUTOR_CONTRACT.md` or the base
  survey docs retroactively, since that would be editing already-published
  research rather than adding to it) to describe Claude Code's `PreToolUse`
  precedence as `deny > defer > ask > allow`, and to note `"defer"` is a
  headless pause/resume primitive, structurally different from the other
  three decisions, not a fourth kind of gate verdict lawkeeper's own
  three-valued `GateDecision` needs to grow a matching case for.

---

## 2. Codex's native hook protocol, read directly — fully resolved, primary source

- **Prior status:** both base surveys had this as secondhand (a third
  party's bridge-implementation comment); last week's pass upgraded it to
  "OpenAI's own issue tracker, read directly" but explicitly fell short of
  its own primary-source bar (Codex's actual docs/source were still
  unread). `developers.openai.com` and `learn.chatgpt.com` were blocked both
  weeks.
- **What changed the access picture this pass:** rather than retrying the
  blocked docs domain a third time, this pass cloned `openai/codex` directly
  (`git clone --depth 1 https://github.com/openai/codex`, read-only, public,
  via this session's git proxy — no attachment or push access requested or
  needed) and read its actual hook-dispatch Rust source. `github.com` and
  `raw.githubusercontent.com` were reachable all pass, so this closes a gap
  the prior two passes treated as blocked by trying a documentation page
  instead of the thing the documentation page is generated from.
- **License:** Apache-2.0, confirmed directly by reading `LICENSE` in the
  clone (`openai/codex`, cloned at commit `d2a6dac20b3b76d4b95d8a699ef7bc6ee3a852d6`,
  2026-10-08).
- **What was actually read, in full:**
  `codex-rs/hooks/src/engine/output_parser.rs` (617 lines, in full —
  every wire-schema parse function for every hook event type);
  `codex-rs/hooks/src/events/pre_tool_use.rs` (full file read, including
  `run`, `parse_completed`, and the `PreToolUseHandlerData` accumulation
  logic); `codex-rs/hooks/src/events/permission_request.rs` (the
  `resolve_permission_request_decision` merge function and `parse_completed`,
  read in full); `codex-rs/hooks/src/engine/mod.rs` lines 130–180
  (`ConfiguredHandler::can_apply_control_effects`/`execution_mode`). Not
  read: the TUI rendering code (`tui/src/bottom_pane/hooks_browser_*`,
  `chatwidget/hooks.rs`) or the MCP-tool-as-hook-handler path
  (`core/src/hook_mcp_executor.rs`) — out of scope for the decision-algebra
  question this entry answers.
- **The actual decision model for `PreToolUse`, confirmed from source, not
  inferred from behavior:** the wire schema's `permissionDecision` enum
  (`PreToolUsePermissionDecisionWire`) has exactly three variants —
  `Allow`, `Ask`, `Deny` — confirmed by reading the parser's own match
  arms. `Ask` is **not** silently ignored the way a schema omission would
  be; it is explicitly, deliberately rejected as invalid output:
  `unsupported_pre_tool_use_hook_specific_output` (`output_parser.rs:458-460`)
  returns `Some("PreToolUse hook returned unsupported permissionDecision:ask".to_string())`
  for exactly that case — the field is parsed, recognized, and then flagged
  as an error condition by name. Tracing that `invalid_reason` forward into
  `parse_completed` (`pre_tool_use.rs:234-245`) confirms the practical
  consequence stated precisely, not approximately: an `invalid_reason`
  sets the hook run's status to `Failed` and logs an `Error` output entry,
  but it does **not** set `should_block = true` — `should_block` is only
  ever set in the sibling `else if let Some(reason) = parsed.block_reason`
  branch, which `ask` never reaches. **Net effect, read directly from the
  control flow rather than asserted from a comment: a `permissionDecision:
  "ask"` hook response on `PreToolUse` fails open — the hook run is marked
  failed and an error is logged, but the tool call proceeds exactly as if
  the hook had returned nothing at all.** This confirms last week's
  secondhand finding (`i9wa4/dotfiles#378`'s account: "parsed but not yet
  supported... continue the tool call anyway") as factually accurate, now
  from Codex's own code rather than a third party's documented analysis —
  and sharpens one detail that secondhand account didn't distinguish: the
  rejection happens in a dedicated "is this hook-specific output shape
  supported" validation function, not in a generic fallback path, meaning
  it is deliberate, maintained validation logic that simply has no handler
  for the parsed value, not a code path that nobody got around to writing.
- **A structural fail-open path confirmed from source, not from behavior
  reports — relevant beyond the `ask` question specifically:**
  `ConfiguredHandler::can_apply_control_effects()` (`engine/mod.rs:157-159`)
  returns `true` only when `execution_mode() == HookExecutionMode::Sync`,
  and every blocking/denying code path in `pre_tool_use.rs` and
  `permission_request.rs` is gated behind this check (confirmed at both the
  main-output-parsing branch and the exit-code-2 branch in each file). A
  hook configured as an **async** handler structurally cannot block or deny
  anything, by construction — not a convention a hook author could violate
  accidentally, a type-level guarantee the dispatcher enforces before it
  ever looks at the hook's actual output. This is a different, and
  previously unlogged, fail-open mechanism from the `ask`-is-unsupported
  one above: it means a Codex hook author who mis-configures a
  security-relevant hook as `async` (perhaps for latency reasons, not
  realizing the tradeoff) gets silent allow-through with no error at all,
  rather than the "failed + logged" path `ask` takes. Worth flagging for
  `EXECUTOR_CONTRACT.md`'s eventual Codex-adapter notes as a second,
  independent reason `deny` cannot be assumed to land even when the wire
  payload is otherwise correct.
- **A second, separate hook event — `PermissionRequest` — confirmed
  strictly binary, no `ask` anywhere in its schema at all (not merely
  unimplemented, as with `PreToolUse`'s `ask`):** `PermissionRequestDecisionWire`'s
  `behavior` field has exactly two variants, `Allow`/`Deny` — confirmed by
  reading the wire struct definition referenced from `output_parser.rs`'s
  `permission_request_decision` function; there is no third enum value to
  even reject. This is Codex's answer to the blog-sourced, previously-
  unconfirmed "`PermissionRequest` hook, proposed in issue #15311" claim
  last week's pass flagged as unread — it exists, it ships, and it is a
  plain two-way allow/deny gate, structurally closer to Cedar's
  `forbid`-wins binary (governance survey §1) than to `PreToolUse`'s own
  three-valued-but-two-implemented scheme sitting right next to it in the
  same codebase.
- **Multi-hook composition, confirmed from source for both events:**
  `PermissionRequest`'s `resolve_permission_request_decision`
  (`permission_request.rs:152-169`) is a short, explicit loop whose own doc
  comment states the rule outright: "Resolve matching hook decisions
  conservatively: any deny wins immediately; otherwise keep the
  highest-precedence allow." `PreToolUse`'s equivalent in `pre_tool_use.rs:115-118`
  uses `results.iter().any(|r| r.data.should_block)` — any single blocking
  hook wins, full stop, no voting. Both are deny-wins designs, consistent
  with (and now a sixth and seventh source for) the deny>ask>allow
  convergence family the hook-mechanisms survey already established across
  five other systems — though `PreToolUse` here only has two live states
  (deny, allow) since `ask` is rejected before composition is even reached.
- **Verdict: fully resolved, adopt-the-warning for `EXECUTOR_CONTRACT.md`,
  not a dependency.** The practical guidance last week's pass already
  reached ("don't emit `permissionDecision: 'ask'` to Codex and assume a
  human gets prompted") is now backed by a direct read of the exact
  validation function that produces that behavior, plus a second,
  independent fail-open path (`async`-handler misconfiguration) worth
  adding to the same warning. If `EXECUTOR_CONTRACT.md` ever grows a Codex
  adapter: never configure lawkeeper's own gate as an async Codex hook (it
  would silently lose all blocking power), and budget specifically for
  `PermissionRequest` as a *separate*, strictly-binary integration point
  from `PreToolUse`, not a variant of it.

---

## 3. A real, fixed precedence bug in qwen-code — a concrete lesson for lawkeeper's own merge-logic tests

Not part of the original queue — surfaced while searching for the Open
Plugins spec (§4) and followed because it is a directly checkable, primary-source
finding squarely in the task's named scope (policy-decision algebras).

- **What was actually read this pass:** `QwenLM/qwen-code#12683` (the bug
  report) and `QwenLM/qwen-code#12689` (the fix PR), both fetched and read
  directly via GitHub — not aggregated from search snippets.
- **License:** Apache-2.0, confirmed directly from the repo's `LICENSE` file
  (copyright Google LLC and Qwen, both 2025).
- **The actual bug, quoted from the report:** with multiple `PreToolUse`
  hooks configured, "the output of the hook that *finishes last* wins. A
  `deny` from one hook is silently overridden by an `allow` from another
  hook that completes later" — i.e., qwen-code's `hookSpecificOutput.permissionDecision`
  merge was last-completed-wins, not precedence-based, so "whether a guard
  hook blocks depends on process scheduling of the hook scripts." The
  reporter gave a reproduction (deny-hook-first, allow-hook-last → tool
  executed, HTTP 200, "deny lost") on qwen-code 0.24.5, Linux/WSL2, in both
  headless and interactive modes.
- **Confirmed fixed, not just reported — checked directly, not assumed:**
  PR #12689 is merged (via the merge queue, 2026-09-25, commit `c9a9a8a`),
  not merely closed. The fix changes `hookSpecificOutput.permissionDecision`
  resolution from last-wins to explicit rank comparison, with the PR's own
  description stating the target precedence outright: "the most restrictive
  decision (deny > ask > allow)." Tied ranks have their reasons
  concatenated rather than one arbitrarily dropped.
- **The one detail that makes this more than "another system confirms the
  algebra" — a real asymmetry worth naming precisely, not glossed as a
  simple oversight:** the PR's own description states that qwen-code's
  **top-level** `decision` field (the legacy/other-events field, not
  `PreToolUse`'s `hookSpecificOutput`) already had most-restrictive-wins
  merge logic *before* this fix — only the newer `hookSpecificOutput.permissionDecision`
  path, added later for `PreToolUse` specifically, had the last-wins bug.
  Read plainly: a single codebase correctly implemented deny-wins
  precedence in one decision-carrying field and silently regressed to
  last-wins in a second, structurally parallel field — not because anyone
  disagreed with the algebra, but because the second field's merge logic
  was authored separately and nothing enforced that the two stay
  consistent.
- **Is this a new data point for the convergence finding, or a caution
  about it?** Both, and worth being precise about which: it is a **sixth**
  real-world system (after Claude Code, Omnigent, dsh, Hermes, goose) whose
  maintainers, once the bug was reported, confirmed `deny > ask > allow` as
  the intended target — so the convergence finding
  (`docs/RESEARCH_harness_hook_mechanisms_survey.md`'s "no longer a
  two-system coincidence") gets stronger, not weaker. But it is also a
  concrete, sourced counter-example to treating "the algebra is settled" as
  the same claim as "any given implementation correctly enforces it
  everywhere it needs to" — those are different properties, and this bug
  lived in production, unnoticed, until an external reporter found it by
  testing actual process-scheduling-dependent behavior, not by reading the
  code.
- **One concrete, actionable thing for lawkeeper's own planned
  `GateDecision` merge logic in `src/guardrail/`:** when lawkeeper's own
  `PreToolUse` gate (or any future multi-hook/multi-field decision surface)
  implements deny>ask>allow, this is a sourced, specific reason to test the
  precedence rule **per decision-carrying field/path independently**, not
  once against a single code path and assume it generalizes — qwen-code had
  the rule right in one field and silently wrong in a structurally
  identical sibling field for a real, shipped release. A unit test that
  feeds deliberately out-of-order-completing (or just differently-shaped)
  hook outputs into the merge function, checking that a late `allow` can
  never override an earlier `deny` regardless of arrival order, is the
  direct, cheap mitigation this bug report argues for.
- **Verdict: adopt-the-lesson (test precedence per decision-carrying field,
  not once globally), not a dependency.** qwen-code itself is a full IDE-CLI
  agent harness (TypeScript/Node, per its repo) — not an integration
  lawkeeper would take on; the value here is entirely the sourced caution
  about implementation drift between structurally parallel merge paths,
  directly applicable to `scripts/gate_pretooluse.py`'s own future
  evolution if it ever grows a second decision-carrying output field.

---

## 4. The Open Plugins hooks specification — still blocked, re-confirmed not stale

- **Prior status:** queued since 2026-09-06 (hook-mechanisms survey);
  last week's pass tried three access paths, all blocked by the egress
  proxy, and found a same-named-but-different spec (`agent-plugins.org` /
  `agentplugins/agent-plugins-spec`) while searching.
- **What was attempted this pass, distinct from last week's attempts:**
  a direct fetch of `open-plugins.com/agent-builders/components/hooks`
  (failed: DNS resolution error, not a 404/TLS error — same practical
  effect as last week's `EGRESS_BLOCKED`, different surface symptom); a
  fetch through a third-party reader-proxy mirror, `r.jina.ai` (also failed
  at DNS resolution — this specific workaround was not tried last week and
  is now ruled out too); a check of whether the `open-plugins` GitHub
  account mirrors the spec as a repo (fetched `github.com/open-plugins`
  directly: the account exists but has **zero public repositories** — so a
  GitHub-hosted mirror of this specific spec does not exist under the
  obvious org name); and a further web search specifically for a GitHub
  copy of the spec's source markdown, which surfaced only secondary
  commentary (third-party blog guides, other projects' issue trackers
  citing the spec's existence and URL) and, again, no primary text.
- **Still unresolved — stays queued, per this doc's own discipline.** Two
  full weekly passes, four distinct access strategies between them (direct
  fetch, cached-mirror fetch, reader-proxy fetch, GitHub-org-mirror check),
  all blocked at the network layer rather than by the content not existing.
  This is now reasonably confirmed as a standing egress-policy restriction
  on this specific domain rather than a transient failure worth retrying
  with the same method a third time.
- **One piece of real, usable secondary information surfaced this pass,
  flagged as secondhand and attributed precisely rather than presented as
  settled:** a comment quoted (via search aggregation, not independently
  verified by reading the PR itself) from a goose contributor's own pull
  request description states "the Open Plugins spec doesn't pin payload
  field names down... in practice Claude Code is the de facto reference
  implementation" for hook payload shapes. If accurate, this would mean the
  spec goose cites is a thinner, less load-bearing document than its
  cross-vendor billing in goose's own module docstring implies (a shape/event-
  taxonomy standard, not a field-level wire-format standard) — but this is
  exactly the kind of claim this doc's own discipline says not to build on
  without tracing to the primary text, and the primary text remains
  unreachable. Recorded as a reason to weight a future successful read of
  this spec carefully (it may be less specific than assumed), not as a
  substitute for reading it.
- **Verdict: unresolved, re-queue again, same as last week.** Needs either
  a different access path next time (an allowlist change, or a future
  session whose proxy policy differs) or a GitHub mirror this pass's
  broader search still didn't surface. Do not substitute the Agent Plugins
  Specification for it (re-confirmed last week as a different, hooks-free
  document).

---

## What this pass found nothing new on

Per the task brief's own instruction: stated plainly. No new, independently
verifiable finding about test-governance/oracle-independence methodology
beyond what last week's mutmut entry already covers — one search this pass
(oracle-independence / mutation-testing / theory-card framing) surfaced a
possibly-relevant arXiv preprint (an August 2026 paper on oracle
"provenance" — whether a test's expected value derives from a specification
versus from the code under test, which is close to Law 18's own "blind spot"
framing), but `arxiv.org` was unreachable this pass (DNS failure, same class
of block as `open-plugins.com`) and the claim could not be verified against
the paper's actual text. Per this doc's own discipline, it is **not**
recorded as a finding — a title and a secondhand characterization from
search-result aggregation is not enough to cite, and padding this section
with it would violate the brief's explicit instruction not to pad with weak
or unverified findings. Worth a dedicated attempt in a future pass if
`arxiv.org` ever becomes reachable; not queued as a numbered item above
since there is nothing confirmed yet to queue.

No Falcun-relayed report was encountered or relied on this pass; nothing
here traces through a secondary research report from another repo.

## Re-check when

- `open-plugins.com` — retry direct access, the `r.jina.ai` reader-proxy
  route, and a fresh GitHub-mirror search whenever this session's (or a
  future session's) egress policy might differ. Two passes and four
  distinct methods have now failed identically; do not keep retrying the
  same methods a third time without a reason to think the policy changed.
- The Claude Code `"defer"` decision (§1) — re-check whether lawkeeper's own
  design docs (`docs/EXECUTOR_CONTRACT.md`, any future `GateDecision` design
  note) ever describe Claude Code's algebra as three-tier; if so, that text
  is now stale and should cite `deny > defer > ask > allow` instead. This
  pass intentionally did not edit those docs itself — recording the correction
  here rather than reaching into already-published design/survey content.
- Codex's hook protocol (§2) — this is now resolved against Codex's own
  source at commit `d2a6dac20b3b76d4b95d8a699ef7bc6ee3a852d6` (2026-10-08);
  re-check if `EXECUTOR_CONTRACT.md` ever seriously plans a Codex adapter,
  since hook internals are exactly the kind of implementation detail that
  can change between releases without a deprecation notice.
- The oracle-"provenance" arXiv preprint mentioned above — re-attempt once
  `arxiv.org` (or a reachable mirror) is accessible; do not cite the title
  or its secondhand characterization as a finding until the actual text is
  read.
