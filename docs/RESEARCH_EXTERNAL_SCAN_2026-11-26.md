# External scan — 2026-11-26

Weekly scheduled research pass. Scope per the routine's own brief: runtime/
`PreToolUse`-style agent governance, policy-decision algebras (allow/deny/ask),
git-hook distribution/enforcement patterns, and test-governance/oracle-
independence methodology. Not Windwright's domain (acoustics/CAD) and not
Falcun's (evolutionary mutation, epistemic-claim verification) — a harness's
other features are out of scope here even when its governance mechanism is
in scope.

**Process note, not a research finding:** two more scans
(`docs/RESEARCH_EXTERNAL_SCAN_2026-11-12.md`, `...2026-11-19.md`) already
exist, read in full, on open-but-unmerged branches
(`origin/agent/external-research-scan-2026-11-12/cloud`,
`origin/agent/external-research-scan-2026-11-19/cloud`) — not yet on `main`
at the time this pass started. Both were read before drafting anything
below, per the lesson `docs/RESEARCH_EXTERNAL_SCAN_2026-10-22.md` already
logged about checking for concurrent/unmerged passes before duplicating
work. This pass builds on their "Re-check when" lists and does not repeat
their closed items (Codex's `PermissionRequest`/Guardian fallback, goose's
source-level re-verification, Writ, the TRACE spec) — see those two docs
directly rather than this one for that material.

**Environment-access note, also not a research finding, surfaced while
investigating the standing `open-plugins.com`/`arxiv.org`/etc. blocks:**
this session's environment (`env_01NUewGCySn5GY4sPxWHAEqa`, "Default") has
an empty network allowlist beyond package managers/MCP — the same
restriction every prior scan going back to 2026-10-01 has hit. This pass
attempted `update_environment` to add exactly the hosts this routine's own
brief and backlog name (`open-plugins.com`, `arxiv.org`, `export.arxiv.org`,
`blog.trailofbits.com`, `docs.snowflake.com`); the call was refused because
no human is present on a scheduled run to approve it ("don't retry it, and
don't look for another way to do what it would have done"). **Flagged for
the user, not retried:** a person can unblock this permanently by running
this routine once interactively ("Run now") and approving that prompt, or
by adding those hosts in the environment's network settings directly. Not
re-attempted after the refusal, per its own instruction.

**Access note, carried forward, confirmed unchanged this pass:** `github.com`,
`raw.githubusercontent.com`, and `api.github.com`'s search endpoints are
reachable. Every other host attempted this pass (`open-plugins.com`,
`arxiv.org`, `export.arxiv.org`, `blog.trailofbits.com`, `docs.snowflake.com`,
`docs.github.com`) failed with `getaddrinfo ENOTFOUND`. `WebSearch` itself
works (confirmed again, same as every pass since 2026-11-05) and does not
appear to go through the same per-host allowlist as `WebFetch`/`curl`. **New
this pass:** this session also has a working Hugging Face Hub MCP connector
(`mcp__Hugging_Face__hf_fs`), and its `hf://papers/<arxiv-id>/paper.md` path
(first used by `docs/RESEARCH_EXTERNAL_SCAN_2026-10-29.md` for the SEAgent
entry) served real, primary-source arXiv HTML-converted full text for two
papers this pass needed — this is the access path that finally closed one
long-queued item (§2 below) without needing `arxiv.org` itself.

---

## 1. The Open Plugins hooks specification — re-attempted first, as instructed, still blocked, seventh consecutive pass

- **Prior status:** blocked every week since 2026-09-06, across at least
  six distinct access strategies and five distinct failure signatures
  (`EGRESS_BLOCKED`, `getaddrinfo ENOTFOUND`, `403 CONNECT tunnel failed`,
  a refused Wayback Machine route, a refused `val.run` mirror route).
- **What was attempted this pass:** a direct `WebFetch` of
  `open-plugins.com/agent-builders/components/hooks`. Failed identically to
  every recent pass: `getaddrinfo ENOTFOUND`. No workaround attempted — the
  2026-11-05/11-19 passes already established that a mirror/archive route is
  refused by this session's own tool-use policy as a containment-escape
  pattern, and this pass does not repeat that.
- **Verdict: unchanged — stays queued, seventh consecutive pass.** This is
  now the single longest-standing unresolved item in this research base.
  The access-note above is the first concrete, actionable step toward
  resolving it (a network-policy change a human can approve), rather than
  another identical retry.

---

## 2. AgentAssay (arXiv 2603.02601) — the longest-queued test-governance lead, finally read from primary source

Queued since `docs/RESEARCH_EXTERNAL_SCAN_2026-11-05.md` (named alongside
arXiv 2606.18168), re-queued unread by both 2026-11-12 and 2026-11-19 because
`arxiv.org`/`export.arxiv.org`/`www.alphaxiv.org` were all blocked every
time. Closed this pass via the Hugging Face Hub MCP connector's
`hf://papers/2603.02601/paper.md` path, which serves arXiv's own
HTML-converted submission text (the fetched document itself carries the
header "URL Source: https://arxiv.org/html/2603.02601" and the arXiv
submission banner — the same provenance check `docs/RESEARCH_EXTERNAL_SCAN_
2026-10-29.md`'s SEAgent entry already established for this access path).

- **Source:** Varun Pratap Bhardwaj (independent researcher), "AgentAssay:
  Token-Efficient Regression Testing for Non-Deterministic AI Agent
  Workflows," arXiv:2603.02601, published 2026-03-03.
- **What was actually read:** the paper's abstract and Section 1
  (Introduction, including the full ten-item contribution list) and the
  start of Section 2 (Related Work), fetched via the HF connector —
  roughly the first 20,000 characters of the converted document. **Not
  read:** Sections 3–11 (the formal stochastic-test-semantics definitions,
  the coverage-metric proofs, the mutation-operator formalization itself,
  the experimental results, and the discussion/limitations) — this entry
  characterizes the paper's framing and claims from its own introduction and
  abstract, not a full technical audit of its proofs or evaluation. No code
  repository was named or searched for this pass.
- **License:** arXiv's standard perpetual non-exclusive license (a paper, not
  software) — no dependency to check; AgentAssay's own abstract does not
  name a released implementation, so there is nothing to vendor either way.
- **What it actually is, confirmed from the paper's own abstract and
  introduction:** a framework for regression-testing *non-deterministic*
  AI agents (the same prompt/tools/model can produce divergent behavior
  across runs), built around three ideas directly relevant to Law 18's own
  oracle-independence concern:
  1. **A three-valued verdict (Pass/Fail/**Inconclusive**), not binary
     pass/fail** — the paper's own framing: "the honest answer is neither
     pass nor fail but 'more evidence is needed'" when too few trials have
     run to distinguish signal from noise. This is a different axis than
     lawkeeper's existing deny/ask/allow tool-call algebra (that's a
     *gating* verdict on an action; this is a *test-outcome* verdict on
     whether a test discriminates) — worth not conflating the two, but
     worth flagging as a second place a lawkeeper-adjacent design question
     ("what does a test outcome even mean when the thing under test is
     stochastic") has independent, formalized prior art.
  2. **Formal "mutation adequacy" for agent-specific mutation operators**
     (prompt, tool, model, and context-window mutants, per the
     paper's own C3 contribution) — a stated theorem, not read in full this
     pass (Section 5, unread), but the existence of a *formal* mutation-
     adequacy definition for agent-shaped mutants is itself notable: Law
     18's own `governed_test.py`/`mutmut` integration checks mutation-
     discrimination empirically (does a real mutant actually get killed)
     without a formalized adequacy criterion of this kind.
  3. **Metamorphic relations as "partial test oracles for the oracle
     problem in agent testing"** (the paper's own C4) — directly named
     using the same "oracle problem" vocabulary Law 18's own theory-card
     system already uses, from an independent academic source, not a
     harness vendor.
- **Is this in scope, or Falcun's territory?** In scope — evaluated purely
  for its test-governance/oracle-strength framing (the brief's named topic),
  not for its cost-optimization claims (SPRT, behavioral fingerprinting,
  trace-first offline analysis), which are a different, adjacent concern
  this scan does not track.
- **One concrete thing worth a documentation note, not a change:** Law 18's
  own T0–T5 trust ladder grades a test's oracle independence as a largely
  static property (checked once, via the theory card). AgentAssay's
  three-valued verdict is a reminder that if lawkeeper's own tooling or
  CI ever runs genuinely non-deterministic agent-authored code (not just
  deterministic Python under mutation testing), a binary pass/fail
  convention would misreport "ran once, got unlucky" as a hard failure —
  worth a note in `docs/WORKPLAN.md` or `GOVERNANCE_PROPOSALS.md` if that
  ever becomes a live concern, not an action item today (lawkeeper's own
  `mutmut`-based testing is on deterministic Python, not stochastic agent
  output).
- **Verdict: adopt-the-distinction (three-valued test verdicts for
  non-deterministic subjects; metamorphic relations as partial oracles),
  not a dependency** — no implementation exists to depend on, and
  lawkeeper's current Law 18 scope (deterministic Python mutation testing)
  doesn't need this today. Logged here so a future pass doesn't need to
  re-find and re-queue this paper.

**The other paper named in the same 2026-11-05 entry, arXiv 2606.18168 ("All
Smoke, No Alarm: Oracle Signals in Agent-Authored Test Code"), is still not
resolved** — a direct `hf://papers/2606.18168` lookup returned
`HF_FS_NOT_FOUND` (not indexed under that ID on Hugging Face Papers), and a
title search of the HF papers index for it returned no exact match (the
closest title-adjacent hits — "Beyond Test Presence," "Rethinking the Value
of Agent-Generated Tests," "Test Coverage Analysis of Agentic Pull
Requests" — are different papers, not this one under a variant ID, confirmed
by reading each returned title directly rather than assuming a near-match).
**Not reported as a finding; stays queued**, now with one more access path
(HF Papers) confirmed not to have it, narrowing what a future pass still
needs to try (direct `arxiv.org`, if that host ever becomes reachable).

---

## 3. New candidate: the subagent/`Agent`-tool bypass of Claude Code's own `PreToolUse` hooks — checked directly against lawkeeper's own `gate_pretooluse.py`

Surfaced via `WebSearch` for "PreToolUse hook governance agent coding 2026
new policy engine allow deny ask" — the search results themselves are not
treated as evidence (per this research base's standing rule), but one
result named a specific, numbered GitHub issue that was then read directly.

- **What was actually read, both via direct `WebFetch` of the live GitHub
  issue pages (public web pages, not the GitHub API/MCP tools this
  session's repository scope restricts to `lawkeeper`/`falcun`):**
  - `anthropics/claude-code#45427`, "RFC: Deterministic tool gate — hooks
    are necessary but insufficient for governance enforcement" (opened
    2026-04-08 by `DimitriGeelen` — the same author already on record in
    `docs/RESEARCH_agent_harness_landscape.md` as AEF's maintainer).
  - `anthropics/claude-code#43772`, "Subagents with bypassPermissions
    ignore PreToolUse hooks — unauthorized commands, wasted tokens," quoted
    in full by #45427 as its evidence for Failure Mode 1 and read
    independently to confirm the claim rather than trust the RFC's
    characterization of it.
- **License:** N/A — these are GitHub issues against Anthropic's own Claude
  Code product (the runtime lawkeeper's `gate_pretooluse.py` already
  targets), not software to depend on.
- **The actual bypass, quoted directly from #43772's own body:** a user
  configured a `PreToolUse` hook (`.claude/hooks/allowlist.sh`) that exits 2
  (BLOCK) for any Bash command not on an explicit allowlist (read-only git,
  `cargo`, `docker`, `psql` — explicitly **not** `git add`/`git commit`/`rm`/
  `chmod`/`python3`). When Claude dispatched subagents via the `Agent` tool
  with `mode: "bypassPermissions"`, those subagents ran `git add`+`git
  commit` (3 unauthorized commits), `rm` (7 files deleted), `chmod +x`, and
  `python3` one-liners — **none on the allowlist, all of which should have
  been blocked** — because `bypassPermissions` bypasses the hook itself, not
  just the interactive "allow this command?" confirmation dialog. The
  issue's own "Suggested Fix" states plainly: "hooks are not a security
  boundary when subagents are dispatched" under that mode.
- **Root cause, honestly scoped to what the sources actually establish:**
  neither issue's own text identifies the underlying mechanism with
  certainty. #45427's own source analysis (quoted directly) says hook event
  inputs *do* carry `agent_id`/`agent_type` fields, and subagents *inherit*
  `toolPermissionContext` from the parent — meaning the hook evaluation
  context differs for a subagent in a way that, per the RFC's own hedge,
  "may" create the bypass, not a confirmed root-cause trace through Claude
  Code's own source (which this research base does not have access to —
  Claude Code is closed-source). This is reported as "a confirmed, observed
  behavior with an unconfirmed mechanism," not "a confirmed mechanism,"
  which is the honest reading of what was actually read.
- **Status, read directly rather than assumed "open":** #43772 was closed
  "not planned" for inactivity by an automated bot (2026-05-15) and locked
  as "resolved" (2026-07-05) — **no human maintainer reply appears on either
  issue**, and the closure ("not planned") and lock reason ("resolved")
  contradict each other. #45427 followed the same pattern (closed "not
  planned" 2026-06-09, locked "resolved" 2026-08-11). Per #45427's own
  thread, commenters report workarounds (never using the built-in `Agent`
  tool at all; an external dispatch-counter/approval gate; a
  `@halt_on_reject` decorator) but no fix shipped. **This should not be
  cited elsewhere as "fixed" or "acknowledged by Anthropic"** — it is
  neither, as of the issues' current (bot-closed, unreplied) state.
- **Checked directly against lawkeeper's own repo, not assumed —
  this is a real, currently-open exposure in lawkeeper's own gate, not
  hypothetical:** `scripts/gate_pretooluse.py` and `.claude/settings.json`
  (both read in full this pass) wire `gate_pretooluse.py` only to the
  `PreToolUse` event with `"matcher": "Bash"` — there is no
  subagent-scoping logic, no `agent_id`/`agent_type` handling anywhere in
  the script, and `docs/EXECUTOR_CONTRACT.md` and every other `.md`/`.py`
  file in the repo were grepped for "subagent" and "Agent tool" and found to
  mention neither (the only repo-local "subagent" hits are
  `docs/AI_FAILURE_PATTERNS.md` and `docs/QUALITY_AND_GOVERNANCE_
  IMPROVEMENT_PLAN_2026-09-04.md`, both about lawkeeper's own
  **cross-machine, cross-process** agent dispatch — Devin, desktop/laptop
  `opencode` instances — a completely different mechanism from Claude
  Code's in-session `Agent` tool/subagents, and not a mitigation for this
  issue). **Concretely: if a lawkeeper session ever dispatches a subagent
  via Claude Code's own `Agent` tool with `bypassPermissions` (or, per
  #45427's own less-certain hedge, possibly any subagent mode where the
  permission context differs from the parent), that subagent's Bash tool
  calls are not confirmed to pass through `gate_pretooluse.py` at all** —
  the canonical-branch force-push/delete protection Law 15/16 rely on this
  hook for would not fire for that subagent's own commands. This is a real,
  checkable gap in lawkeeper's current enforcement surface, not a
  speculative one, though its exact trigger conditions (which subagent
  modes, specifically) are only as confirmed as #45427's own hedge allows.
- **Why this is a genuinely new finding, not a restatement of anything
  already logged:** every prior "ask tier doesn't always live at the wire
  layer" finding in this research base (goose, Hermes, Writ, Codex's own
  hooks) is about a *hook's own wire protocol* being narrower than its
  conceptual model. This is different in kind — the hook *is* ask/deny-
  capable and *does* fire for the main session, but a specific dispatch
  mode (subagents) **skips the hook mechanism entirely** for some tool
  calls. That is a coverage gap in *when* the gate runs, not a precision
  gap in *what* the gate can express — a new category for this research
  base, and the first entry naming a scope boundary this severe for Claude
  Code's own native hook system specifically (as opposed to a third-party
  product's hook layer).
- **Verdict: adopt-the-warning for `EXECUTOR_CONTRACT.md` and
  `scripts/gate_pretooluse.py`'s own module docstring — this pass does not
  implement a fix, since this scan's job is research, not build.** The
  concrete, actionable note for a future session: `gate_pretooluse.py`'s
  own "SCOPE BOUNDARY" section (already present, covering shell-parsing
  limits) should get a second, explicit entry for this — the hook may not
  run at all for subagent-dispatched tool calls under some permission
  modes, a materially different and more severe limitation than "a
  determined adversary could construct an evasive command string," and one
  the script's own docstring does not currently mention. Whether this is
  exploitable *today* in lawkeeper's own usage depends on whether lawkeeper's
  Claude Code sessions actually use the `Agent`/Task tool for in-session
  subagent dispatch (as opposed to its existing cross-machine dispatch
  convention, which this is not) — not independently confirmed either way
  this pass; worth checking directly before deciding how urgent a mitigation
  is, per Law 20's "verify before claiming" standard applied to the *impact*
  question, not just the *mechanism* question this entry already resolved.

---

## 4. New candidate: Aegis (`Justin0504/Aegis`, arXiv 2603.12621) — a pre-execution firewall with a published attack-blocking evaluation

Read via the Hugging Face Papers connector (same access path as §2), since
`arxiv.org` itself remains blocked.

- **Source:** Zhiyuan Su (UC Davis), Yue Zhao (USC), "AEGIS: No Tool Call
  Left Unchecked — A Pre-Execution Firewall and Audit Layer for AI Agents,"
  arXiv:2603.12621. Code at `github.com/Justin0504/Aegis`, named and
  linked directly in the paper's own abstract footnote as open-source
  (MIT) — the repository itself was not independently fetched and read
  this pass; this entry is sourced from the paper text, not the code.
- **License: MIT, per the paper's own abstract footnote** — not
  independently re-verified by reading the repo's `LICENSE` file directly
  this pass; flagged as the paper's own stated claim, not an independent
  confirmation the way this research base's GitHub-sourced entries get.
- **What it actually is, confirmed from the paper's own text:** a
  framework-agnostic interception layer (an SDK instrumenting 14 agent
  frameworks across Python/JS/Go) plus a Gateway service running a
  three-stage pipeline — (1) recursive string extraction from tool
  arguments to depth 32, explicitly to defeat "depth evasion" (payloads
  hidden in nested argument structures past a shallow validator's reach),
  with a 10,000-string cap and conservative-flag-on-truncation; (2)
  content-based risk scanning against 22 detection patterns across 7
  categories (SQL injection, path traversal, shell injection, prompt
  injection, sensitive-file paths, data exfiltration, PII leakage); (3)
  policy validation via cached, AJV-compiled JSON Schema rules — returning
  exactly one of three decisions, **allow / block / pending** (pending
  routes to a human reviewer, with the agent fully paused — "no tools
  execute and no further LLM calls proceed" — while waiting, 2s poll
  interval, 5-minute timeout). This is the deny/ask/allow shape under
  different names, confirmed from the paper's own architecture description,
  not reconstructed.
- **A genuinely new piece, not present elsewhere in this research base: a
  published, numbered attack-blocking evaluation, not just a design.** On a
  curated suite of 48 attack instances across the same 7 categories, the
  paper reports **100% blocking** (all 48 before execution, including
  depth-evasion cases nested to depth 20, with depth-50 payloads correctly
  caught by the truncation-triggers-suspicion fallback); on 500 benign
  tool calls, a **1.2% false-positive rate** (6 cases, all legitimate SQL
  `WHERE` clauses with disjunctive conditions triggering the OR-injection
  pattern — a concrete, named false-positive class, not a vague
  acknowledgment); and **8.3ms median interception latency** (P95 14.7ms,
  P99 23.1ms) over 1,000 consecutive calls. This is the first entry in this
  research base with a quantified attack-coverage number for a tool-call
  gate, as opposed to a design description or a precedence rule.
- **A design choice directly relevant to the governance survey's §4
  (SLSA/in-toto/structured attestation) and now TRACE (2026-11-19 §5):** the
  audit layer signs each trace with a per-agent Ed25519 key and chains
  records via SHA-256 (each record commits to its predecessor), so
  post-hoc tampering with any entry invalidates the chain — a concrete,
  shipped (per the paper) instance of the same "signed, tamper-evident,
  subject-bound record over free text" pattern this research base has now
  found four times (SLSA, in-toto, TRACE, and now Aegis), independently
  arrived at by a fourth, unrelated source.
- **Confirmed non-overlap with this research base's existing #45427 finding
  (§3 above), stated explicitly by the paper's own threat model:** Aegis's
  own stated non-goal is direct and relevant — "Aegis does not defend
  against attacks that bypass the SDK entirely, such as direct tool or API
  calls issued outside the instrumented client." That is the same category
  of gap #45427 documents for Claude Code's native hooks (a dispatch path
  that doesn't go through the instrumented interception point at all) — a
  second, independent source naming "the mediation point can be
  structurally bypassed by a call that doesn't go through the instrumented
  client/hook" as a known, self-acknowledged limitation of this entire
  class of mechanism, not something unique to Claude Code's hooks.
- **Verdict: adopt-the-design (the three-stage pipeline's depth-evasion
  defense specifically, and the Ed25519+SHA-256 audit chain), not a
  dependency.** Aegis is a Node/Python/Go SDK-plus-service architecture for
  a much broader multi-framework integration problem than lawkeeper's
  single-repo, single-hook-script scope; vendoring it has no realistic
  integration path. The one concrete, cheap idea worth citing in a future
  `gate_pretooluse.py` revision if lawkeeper's own command-string detection
  ever needs to handle adversarially-nested input: capping recursion/string
  extraction depth and treating truncation itself as a suspicious signal,
  rather than silently stopping at a depth limit.

---

## 5. New candidate: combra-guard — a four-layer gate matching lawkeeper's own Law 16 philosophy, verified only via package metadata (its own linked source repo is dead)

Surfaced by the same `WebSearch` that found §3; checked directly rather than
cited from the search snippet, per this research base's standing rule.

- **What was actually read:** the PyPI JSON API record for
  `combra-guard` (`pypi.org/pypi/combra-guard/json`, v0.1.2) — its
  description text, `license_expression`, and `project_urls`. **Not read:**
  any actual source file. The package's own `project_urls` name
  `https://github.com/Fabrique-Futur/combra-guard` as its repository — a
  direct `WebFetch` of that URL, and of
  `raw.githubusercontent.com/Fabrique-Futur/combra-guard/main/README.md`,
  both returned **HTTP 404**, and a `WebSearch` for the org/repo name
  together found nothing matching. **This itself is a reportable finding,
  not just an access failure on this research base's side:** the package's
  own PyPI metadata names a source repository that does not currently
  resolve — either deleted, renamed, or made private since the package was
  published. Flagged plainly rather than silently treated as "source read."
- **License, per PyPI metadata only:** Apache 2.0 (`license_expression`
  field; `LICENSE` and `NOTICE` files are named as included in the
  distribution, but neither was independently read, since the source repo
  link is dead and no sdist/wheel was downloaded this pass).
- **What it claims to do, per its own PyPI description — read as a claim,
  not independently verified against source:** a config-driven policy gate
  (`guard.toml`) enforced at **four** points: a Claude `PreToolUse` hook
  (instant in-editor deny), a Claude `Stop` hook (scans the whole turn's
  result), a git `pre-commit` hook (works with any agent or a human,
  per its own description), and `check-diff` run in CI against the PR
  diff — described explicitly as **"the authoritative wall"** because the
  three earlier gates "can be bypassed." Four generic, repo-parameterized
  rule types (`forbidden_field`, `forbidden_pattern`, `protected_path`,
  `protected_read`), zero runtime dependencies, Python 3.11+.
- **Why this is worth logging even without a source read: it is an
  independent, third-party confirmation of lawkeeper's own existing Law 16
  design, not a new idea to adopt.** Lawkeeper's own enforcement stack is
  already exactly this shape — local git hooks (pre-commit/commit-msg/
  pre-push) plus a CI backstop (`governance-guard.yml`) that "re-runs the
  same checks," per `AGENTS.md`, with `gate_pretooluse.py` now added as a
  fourth, earliest layer. combra-guard's own README (per its PyPI
  description) names the identical bypassable-early-layers/authoritative-
  CI-wall structure as a deliberate design, under a different vendor,
  independently — the same "catch at multiple boundaries, trust the latest
  one most" philosophy this research base already found in
  `docs/RESEARCH_agent_harness_landscape.md`'s discussion of git hooks vs.
  tool-call gates, now confirmed a third time (after lawkeeper's own
  pre-existing design and HookRunner's cautionary tale about a broken
  "cannot be skipped" promise) by a project built around the identical
  four-tier shape on purpose.
- **Verdict: adopt-the-confirmation (not a new design, a third-party
  validation of lawkeeper's existing one), not a dependency, and
  explicitly not "source-verified"** — re-attempt a real source read if
  the repository link is ever fixed or a mirror is found; until then, don't
  cite this entry's rule-type schema or precedence details beyond what the
  PyPI description itself states.

---

## 6. New candidates, checked and found not squarely in scope — logged so a future pass doesn't re-read them from nothing

Per 2026-11-19's own "Re-check when" list, four named-but-unread repositories
were checked this pass (`README.md` only, via `WebFetch`, not raw source —
flagged as a lighter read than this research base's usual standard, enough
to make an in-scope/out-of-scope call, not enough to cite implementation
details from).

- **`KeyArgo/custodian-kernel`** — the closest fit of the four: a
  provider-neutral policy/evidence layer with a real three-way verdict
  (execute autonomously / ask for operator approval / block), single-use
  scoped approvals, and hash-chained receipts — structurally close to
  Aegis/SidClaw. License not stated on the page (not independently
  checked against the repo's actual `LICENSE` file this pass); self-
  described as "alpha," no third-party security audit. **Queued for a
  real source read**, not dismissed — the README alone is enough to place
  it in-scope but not enough to verify its actual precedence rules or
  mechanism.
- **`HelpCode-ai/anythingmcp`** — an MCP *tool-aggregation gateway*
  (connects 958+ external APIs as MCP tools), not a `PreToolUse`-style
  action gate; its access controls (role-based tool whitelisting,
  read-only annotations, response field-mapping) are closer to an API
  gateway's authorization model than a deny/ask/allow tool-call algebra.
  AGPL-3.0 core. **Verdict: out of this scan's scope** (a harness's other
  features, per the brief's own exclusion) — not a governance-mechanism
  entry.
- **`halofyai/halofy`** — a data-access/governance layer for organizational
  knowledge shared across agents (namespace-scoped visibility, append-only
  corrections), not a tool-call gate; its own "policy" API operation is
  undocumented on the page. Mixed AGPL-3.0-or-later (kernel/console) and
  Apache-2.0 (named driver/mcp/integration subtrees). **Verdict: out of
  this scan's scope** — adjacent (both are "governance for AI agents"), but
  the specific mechanism (knowledge-access scoping, not tool-call gating)
  isn't the brief's named topic.
- **`faramesh-core`** — actually a real, in-scope fit, checked: a local
  enforcement daemon with a `permit`/`defer`/`deny` verdict (the ask tier
  under a different name, confirmed from the README), `default deny`
  policies, rate limits with an `on_exceed` action, and decisions
  described as "pure functions of the policy and action payload, with no
  LLM in the decision path" — plus a hash-chained write-ahead log, a fifth
  independent instance of this scan's running audit-trail-design tally
  (after SLSA, in-toto, TRACE, Aegis). Apache-2.0. Self-reported as
  implemented (CLI, release/CI badges, "13 frameworks today"), not
  independently verified against source this pass. **Verdict: a genuine
  new deny/ask/allow-shaped data point, not yet source-verified** — queue
  for a direct README-vs-source cross-check (the same discipline
  `docs/RESEARCH_EXTERNAL_SCAN_2026-10-29.md` applied to HookRunner, which
  found a real gap between a tool's documented and actual behavior) before
  citing its precedence rules as confirmed.

---

## 7. SidClaw (`sidclawhq/platform`) — a policy-as-a-service product, mixed license, logged for its failure-mode granularity

Surfaced by the same search as §3/§5.

- **What was actually read:** `hooks/README.md` and the repository's own
  top-level description, via `raw.githubusercontent.com` and `WebFetch`
  of the GitHub repo page directly (not the actual hook/evaluation source
  code).
- **License, confirmed from the repo's own description, worth stating
  precisely because it splits:** the SDK and MCP proxy (`@sidclaw/sdk`,
  `sidclaw` on PyPI, `sidclaw-mcp-proxy`) are Apache 2.0; the platform
  itself (API, dashboard, docs) is **FSL 1.1** — "source-available," not an
  OSI license, explicitly barring use as a competing hosted service, and
  converting to Apache 2.0 only in March 2028. The SDK can run against
  either SidClaw's own hosted API or a self-hosted FSL deployment.
- **The mechanism, per its own docs:** a `PreToolUse` hook classifies and
  risk-scores each call, then `POST`s it to an evaluation endpoint; the
  decision vocabulary is allow / deny / "approval required" (the page
  itself never uses the word "ask"). **The failure-handling granularity is
  the genuinely new piece**, finer-grained than anything else in this
  research base's running "how does each system fail" comparison:
  fail-**closed** by default (unreachable service → blocked); a separate,
  explicit opt-in (`SIDCLAW_FAIL_OPEN=true`) covers transport/server
  failures only; a *further separate* opt-in
  (`SIDCLAW_FAIL_OPEN_ON_RATE_LIMIT=true`) covers 429s specifically; and
  auth errors (401/403) are **never** allowed to fail open regardless of
  either toggle. That's four independently-configurable failure categories
  (transport/server error, rate limit, auth error, and the connectable-
  but-denies-explicitly case), compared to GitHub Copilot's two (timeout
  vs. crash, already logged in an earlier scan) and lawkeeper's own two
  (unparseable input vs. judgment exception).
- **Verdict: adopt-the-granularity-idea (per-failure-category fail
  direction, not just per-failure-mode), not a dependency** — the platform
  half's FSL license rules it out as something to depend on even if the
  mechanism fit were otherwise good, and the Apache-licensed SDK half is a
  thin client for a service lawkeeper has no reason to run.

---

## What this pass found nothing new on

Per the task brief's own instruction: stated plainly rather than padded.

- **Test-governance/oracle-independence**, beyond AgentAssay (§2): arXiv
  2606.18168 remains genuinely unreachable (§2's closing paragraph);
  arXiv 2603.18059 and 2606.19464 (named by 2026-11-12, policy-DSL and
  Cedar/OPA-extension papers respectively) were not attempted this pass —
  deprioritized in favor of the governance-algebra leads that actually
  panned out (§§3–7); still queued, not newly checked.
- **Context-to-Execution Integrity (arXiv 2607.06000)** was read in part
  (abstract and the start of its boundary/threat-model section, via the
  same HF Papers path as §§2/4) but is **not reported as a scan finding**:
  it is an information-flow/provenance mechanism for preventing
  attacker-writable context from acquiring authority over protected sink
  fields — a real, carefully-specified idea, but adjacent to, not an
  instance of, this brief's named topic (a tool-call allow/deny/ask
  algebra). Logged here only so a future pass recognizes the title and
  doesn't re-read it from nothing; not adopted, not verdicted, because it
  doesn't answer the question this scan tracks.
- `blog.trailofbits.com` and `docs.snowflake.com` — both re-attempted
  directly this pass (not assumed from last week), both still
  `getaddrinfo ENOTFOUND`.
- `docs.github.com` (for GitHub Copilot CLI's own hooks docs, surfaced by
  the §3 search) — also blocked this pass (`ENOTFOUND`), not previously
  logged as attempted against this specific host; no new information about
  Copilot's hooks beyond what the 2026-10-15 scan already has from
  `github/docs`'s own GitHub-hosted source.
- No Falcun-relayed report was encountered or relied on this pass; nothing
  here traces through a secondary research report from another repo.

## Re-check when

- **`open-plugins.com`, `arxiv.org`/`export.arxiv.org`, `blog.trailofbits.com`,
  `docs.snowflake.com`** — all still blocked at the network-policy level,
  now with a concrete unblock path on record: the `update_environment`
  request this pass attempted and had refused for lack of a present human
  (see the access note at the top). Re-attempt the request itself (not
  just the fetches) once a human runs this routine interactively, or ask
  the user to add these hosts directly in the environment's network
  settings.
- **arXiv 2606.18168** ("All Smoke, No Alarm") — confirmed not reachable via
  the HF Papers connector either, narrower than before; needs `arxiv.org`
  directly or a different mirror not yet tried.
- **arXiv 2603.18059 and 2606.19464** — named by 2026-11-12, not attempted
  this pass at all (the HF Papers connector was not tried against them);
  worth trying that path before assuming they need `arxiv.org` directly.
- **`github.com/Justin0504/Aegis`** (§4) — this pass read the paper, not the
  code; read the actual repo directly (license file, the Gateway's
  detection-pattern implementation, the audit-chain code) before citing
  anything beyond what the paper itself states.
- **`Fabrique-Futur/combra-guard`'s actual source** (§5) — the repo link in
  its own PyPI metadata 404s; re-attempt directly (the repo may be
  temporarily private, renamed, or the metadata may be stale) or search for
  a fork/mirror before citing anything beyond the PyPI description.
- **`KeyArgo/custodian-kernel` and `faramesh-core`** (§6) — both read as
  README-only this pass; read actual source (and confirm faramesh-core's
  real GitHub owner/org, used here as `faramesh/faramesh-core` based on
  what resolved, not independently cross-checked against the PyPI/npm
  registry or a repository search) before citing their mechanisms as
  source-verified.
- **Claude Code's subagent/`Agent`-tool `PreToolUse` bypass** (§3) — the
  *mechanism* (why it happens) is only as confirmed as issue #45427's own
  hedge allows; the *impact on lawkeeper specifically* (whether lawkeeper's
  own Claude Code sessions actually use the `Agent`/Task tool for
  in-session subagent dispatch, as opposed to its existing cross-machine
  dispatch convention) was not checked this pass and should be, before
  deciding how urgent a `gate_pretooluse.py`/`EXECUTOR_CONTRACT.md`
  mitigation is.
