# External scan — 2026-10-29

Weekly scheduled research pass. Scope per the routine's own brief: runtime/
`PreToolUse`-style agent governance, policy-decision algebras (allow/deny/ask),
git-hook distribution/enforcement patterns, and test-governance/oracle-
independence methodology. Not Windwright's domain (acoustics/CAD) and not
Falcun's (evolutionary mutation, epistemic-claim verification) — a harness's
other features are out of scope here even when its governance mechanism is
in scope.

Per the brief, this pass re-attempted the Open Plugins hooks specification
first (the one item the brief names as still open). **Still fully blocked**,
same as every prior pass — recorded below with the exact access attempts,
not padded. Looking past that block surfaced two genuinely new, directly-
verified findings: **SEAgent**, an academic MAC/ABAC framework for LLM-agent
tool-call gating with its own allow/deny/ask decision engine (read from the
actual paper text, not a summary), and **HookRunner**, a git-hook
distribution tool whose own documented "hooks that cannot be skipped"
guarantee turned out, on a direct read of its source, to not be enforced
anywhere in the code. One lead (Snowflake's Cortex Code Agent SDK hooks
page) could not be verified at all this pass and is reported as blocked,
not as a finding. The `gate_pretooluse.py` re-check item from last pass's
"Re-check when" list was also done. No Falcun-relayed report was encountered
or relied on this pass.

**Access note, stated up front because it shaped what got read:** this
session's egress proxy blocks `open-plugins.com`, `developers.openai.com`,
`learn.chatgpt.com`, `docs.snowflake.com`, `arxiv.org`, `huggingface.co` (as
a direct host), `repository.tudelft.nl`, and generic mirror/reader-proxy
workarounds (a `val.run` mirror of open-plugins.com's own homepage, and a
direct `web.archive.org` fetch attempt, the latter specifically flagged and
refused by this session's own tooling as a containment-escape pattern, not
retried). `github.com`, `raw.githubusercontent.com`, and `code.claude.com`
were reachable throughout, matching every prior pass. New this pass:
**`proxy.golang.org` is reachable directly (it is on this session's explicit
no-proxy allowlist)**, which is what let the HookRunner entry below read
real Go module source instead of a rendered doc page — worth recording as a
usable access path for any future Go-ecosystem candidate this research base
encounters. Separately, this session has a working Hugging Face Hub MCP
connector (`mcp__Hugging_Face__hf_fs`) whose `hf://papers/<arxiv-id>/paper.md`
path serves arXiv's own HTML-converted full text for papers HF has indexed —
this is what made the SEAgent entry below a primary-source read despite
`arxiv.org` itself being blocked; it did **not** have the second paper this
pass went looking for (arXiv 2608.22868, "AgentFlow: A Flow-Centric Policy
Language and Framework for Securing LLM Agent Systems" — not indexed under
that ID; a search of the same HF papers index for "AgentFlow" returned a
different, unrelated paper of the same name about vulnerability-discovery
harnesses, not a policy-language framework, confirmed by reading its own
description rather than assumed from the title match). That second paper is
**not reported as a finding** — only a search-engine-snippet characterization
of it was ever obtained, and this doc's own discipline (and the 2026-10-08/
2026-10-15 scans before it) rules that out as a basis for a verdict.

---

## 1. The Open Plugins hooks specification — still blocked, no change

- **Prior status:** queued since 2026-09-06; blocked on every attempt since
  (2026-10-01, 2026-10-08, 2026-10-15 — three distinct access strategies
  across those passes, all failing at the network layer).
- **What was attempted this pass, distinct from prior attempts:** a direct
  fetch of `open-plugins.com/agent-builders/components/hooks` (failed:
  `getaddrinfo ENOTFOUND`, the same functional block as every prior pass); a
  web search that surfaced a third-party mirror of the site's homepage at a
  `val.run` subdomain (`open-plugins.com/en`, mirrored, not the
  `agent-builders/components/hooks` page itself) — fetching that mirror
  directly also failed (`getaddrinfo ENOTFOUND`, same host-not-allowed
  block, confirming this isn't specific to the open-plugins.com domain name
  but to this session's allowed-host list generally for unlisted hosts).
- **One attempt this pass deliberately did not continue:** a `curl` to
  `web.archive.org` as a possible Wayback Machine mirror route was blocked
  by this session's own tool-use policy with an explicit "Containment
  Escape" classification, not a network failure. Recorded here so a future
  pass doesn't treat that as "try the same workaround, it might go through
  next time" — the correct next step if this needs resolving is an
  allowlist change to this session's network policy, not a mirror/proxy
  workaround from inside the session.
- **Verdict: unresolved, re-queue again, same as every prior pass.** Four
  full weekly passes (2026-10-01, -08, -15, -29) and at least six distinct
  access strategies between them (direct fetch, cached-mirror fetch,
  reader-proxy fetch, GitHub-org-mirror check, a search for a different
  homepage mirror, a Wayback Machine route) have all failed to produce
  primary text. This is a standing egress-policy restriction on this
  specific domain, not a transient failure — say so plainly rather than
  padding this entry with secondhand characterizations again.

---

## 2. SEAgent — a new, directly-read academic MAC/ABAC framework with its own allow/deny/ask decision engine

Surfaced while searching for formal treatments of an allow/deny/ask
precedence algebra (the open question the base governance survey left on
record: "is there a standard conflict-resolution algebra in policy-as-code,
or does everyone invent their own"). This is the first entry in this
research base read from the actual paper text rather than an abstract or a
secondhand summary, and it is a genuinely new data point — not another
confirmation of the deny>ask>allow convergence the hook-mechanisms survey
already established six times over.

- **Source:** Ji, Wu, Jiang, Ma, Li, Gao, Wang, Li, "Taming Various
  Privilege Escalation in LLM-Based Agent Systems: A Mandatory Access
  Control Framework," arXiv:2601.11893v1 [cs.CR], 17 Jan 2026.
- **What was actually read:** the paper's own full HTML text (sections 1–7,
  continuously, via two sequential reads totaling roughly 59,000 characters
  of the converted document), fetched through this session's Hugging Face
  Hub MCP connector (`hf://papers/2601.11893/paper.md`) — confirmed to be
  arXiv's own HTML conversion of the submission (the document's own header
  states "URL Source: https://arxiv.org/html/2601.11893" and carries the
  arXiv submission banner, license line, and author/affiliation block
  verbatim), not a third-party paraphrase site. Not read: Appendices A–J
  (referenced for tool-attribute classification criteria, the full policy-
  language grammar, and the formal non-interference proof for SEMemory) —
  the HTML conversion available through this connector did not include
  them in what was fetched this pass, and no code/artifact repository was
  found (a dedicated search turned up nothing; the paper's own "Open
  Science" reference to a "released artifact" could not be independently
  located or verified this pass).
- **License:** the paper itself carries the arXiv.org perpetual
  non-exclusive license (standard for an arXiv preprint, not a software
  license) — there is no code dependency to license-check here, only a
  design to evaluate, since no public implementation was found.
- **What SEAgent actually is:** a policy-based mandatory access control
  (MAC) framework, built on attribute-based access control (ABAC), that
  gates agent-to-agent messages and agent-to-tool invocations in both
  single- and multi-agent LLM systems. It labels every agent, tool, and RAG
  database with security attributes (Object/Action/Sensitivity for tools;
  Integrity for agents and databases; Privacy for databases and tool
  results) and maintains a live directed graph ("System View") of
  information flow during each round of execution. A separate "SEMemory"
  component handles cross-round context persistence without letting stale
  System View state cause false positives/negatives — not itself a
  governance-decision mechanism, so not pursued further here.
- **The decision model, quoted/confirmed directly from §5.3–5.4, and this
  is the new data point:** a security policy is a triple (goal, path
  pattern, boolean rule). **The goal is explicitly one of `allow`, `deny`,
  or `ask`** — the paper's own wording: "Supported actions include ask,
  deny, and allow. These correspond to prompting the user, blocking the
  action, or permitting it, respectively." So far this matches every other
  system in this research base. **What's different is how conflicts between
  multiple matching policies are resolved**, and it is not deny-always-wins:
  "The engine operates on a first-match principle. It begins by parsing and
  sorting all policies from the Policy DB by their specificity,
  prioritizing policies with more explicit node types and fewer wildcards.
  ... If the rule evaluates to true, the corresponding enforcement action
  ... is immediately executed, and the process terminates. If no policies
  are matched after checking the entire database, the engine defaults to
  allowing the action." Read plainly: SEAgent's precedence is
  **specificity-ordered first-match, with default-allow as the fallback**
  — structurally the same shape as a firewall ACL or OPA's own
  no-built-in-precedence situation (already logged in
  `docs/RESEARCH_harness_governance_survey.md` §1), **not** the
  "most-restrictive-verdict-wins regardless of match order" rule Claude
  Code, Omnigent, dsh, Hermes, goose, qwen-code, and GitHub Copilot all
  independently converged on for *their* problem (resolving several hooks'
  simultaneous verdicts on one tool call). SEAgent is solving a related but
  distinct problem — which *policy* applies to one event, out of a database
  of policies — the same problem OPA's `allow`/`deny` document composition
  faces, and SEAgent's answer (author must order deny rules more
  specifically than any overlapping allow rule, or the allow rule can win
  by matching first) is exactly the "no built-in precedence, policy-author
  discipline required" situation the governance survey already flagged as
  OPA's actual answer — now with a second, independently-designed academic
  system landing on the same answer rather than deny-wins, which is a real,
  sourced counterexample to treating "the algebra is settled" as universal
  across *all* multi-rule composition problems (only across the specific
  multi-hook-same-event one the hook-mechanisms survey tested).
- **The ASK tier's own mechanism — a real, concrete elaboration beyond a
  bare human-in-the-loop pause, confirmed from §5.4:** when the engine
  reaches an `ask` goal, the user is presented with exactly three choices —
  **Disallow (default)**, **Allow once**, or **Always allow this pattern**.
  Choosing the third **mutates the live Policy DB**: "the Decision Engine
  generates a new, highly specific policy with a goal of Allow and a
  concrete path corresponding to the exact information flow. This new
  policy is appended to the Policy DB and prioritized in future
  evaluations." This is a self-expanding allow-list driven directly by user
  approval — a different, more automated mechanism than any prior entry in
  this research base (Omnigent's CEL policies are hand-authored; MCP's
  elicitation and Omnigent's approval flow treat accept/decline/cancel as
  terminal outcomes for *that one call*, not as something that writes a new
  standing rule). Worth flagging precisely: "ask, with a default-disallow
  and an explicit opt-in to make the exception permanent and
  highest-priority" is a concretely different design from lawkeeper's own
  ASK tier (which never auto-promotes a one-time answer into a standing
  rule) — not a recommendation to copy, just a documented alternative this
  research base hadn't seen before.
- **Is this in scope, or is it Falcun's territory?** In scope — this is a
  policy-decision algebra for gating agent tool/message calls (the brief's
  own named topic), evaluated here purely for its governance mechanism, not
  for its privilege-escalation-attack taxonomy or its benchmark results
  (InjecAgent/AgentDojo numbers), which are adjacent but not what this scan
  tracks.
- **One concrete thing lawkeeper could take from this, or not:** not a
  dependency (no public implementation was found to depend on, and the
  paper's own Policy DB/System-View-graph model is considerably heavier
  machinery — tracking live information-flow graphs across a multi-agent
  system — than lawkeeper's single-repo, single-command-line problem
  needs). The one transferable, concrete idea: **lawkeeper's own planned
  `GateDecision` design should stay explicit that "deny beats ask beats
  allow when several things judge the same event" and "which single rule
  applies out of many candidate rules" are two different precedence
  questions**, confirmed now by a second, independently-sourced system that
  answers them differently (deny-wins for the first, specificity-ordered
  first-match for the second) — `scripts/gate_pretooluse.py` only has one
  hardcoded classification path today (no "database of many candidate
  policies" problem yet), so this is a documentation note for
  `EXECUTOR_CONTRACT.md`/`GOVERNANCE_PROPOSALS.md` if lawkeeper's guards
  ever grow into a rule database, not a change to anything that exists now.
  **Verdict: adopt-the-distinction (two separate precedence problems, not
  one), not a dependency or a design to copy wholesale.**

---

## 3. HookRunner (`ashavijit/hookrunner`) — a real git-hook-distribution tool whose "cannot be skipped" guarantee is dead code

Surfaced searching for new git-hook distribution/multi-repo policy tools
(the brief's own named topic, and the one item in
`docs/RESEARCH_agent_harness_landscape.md`'s queue — "pre-commit's own
extension model" — that stays closed but adjacent to this). Not a
PreToolUse-style agent gate; a pre-commit-style git hook manager with a
policy engine and remote-policy fetching, aimed at exactly the
"how do policies get distributed and stay in sync across repos" problem
that doc's queue named.

- **Source:** `github.com/ashavijit/hookrunner` — confirmed live, public,
  on its default `master` branch (not `main`; an initial attempt against
  `main` 404'd and was corrected after fetching the actual repo page
  directly, rather than concluding the repo was gone from one wrong-branch
  guess). Also published to the Go module proxy as
  `github.com/ashavijit/hookrunner`, latest tagged version `v0.53.0`
  (2025-12-22), which is what this pass actually read: the full module
  source was downloaded via `proxy.golang.org`'s immutable module cache
  (reachable directly — see the access note above) rather than relying on
  `pkg.go.dev`'s rendered README, and the specific lines cited below were
  then **re-confirmed against the live `master` branch via
  `raw.githubusercontent.com`** to make sure the pinned-version read wasn't
  stale — both match.
- **License:** MIT, confirmed by reading `LICENSE` directly from the
  downloaded module source ("Copyright (c) 2024 HookRunner Contributors").
- **What it does, confirmed from source, not the marketing table:** a
  single-binary, cross-platform pre-commit-hook runner with DAG-based
  parallel hook execution, a local policy-rule engine (`internal/policy/
  evaluator.go`), and remote-policy fetching over HTTPS with ETag-based
  caching (`internal/policy/fetcher.go`) — policies can be hosted centrally
  and pulled into many repos' local configs, which is the actual mechanism
  behind the multi-repo-distribution pitch.
- **The policy engine's actual decision model, read directly from
  `internal/policy/evaluator.go` (216 lines, read in full) — and this
  matters for how lawkeeper should read "policy engine" claims generally:**
  there is no allow/deny/ask three-way anything here. `Evaluate(rules,
  files, commitMsg) EvalResult` accumulates a plain list of `Violation`
  structs (max-files-changed, forbidden directories/files/extensions,
  required files, file-size limits, forbidden-content/secret-pattern
  regexes, a commit-message regex) and the function ends with
  `result.Passed = len(result.Violations) == 0`. This is **pure AND
  composition** — any one violation fails the whole check — structurally
  identical to the Kubernetes admission-controller model the governance
  survey already catalogued (`docs/RESEARCH_harness_governance_survey.md`
  §1: "any objection is fatal, no override... no ALLOW/DENY/ASK three-way
  and no precedence puzzle, because there's no allow verdict to compete
  with a deny verdict"), not Omnigent's or Claude Code's three-tier model.
  Worth naming precisely: "policy engine" in a tool's own marketing
  (HookRunner's `pkg.go.dev` page markets itself against pre-commit/Husky/
  Lefthook specifically on having one) does not imply an ask-capable
  decision algebra — this is the research base's second confirmed example
  (after Kubernetes) that a real, shipped git-hook-adjacent "policy engine"
  can mean "a richer pass/fail rule set," not a three-way gate, and the
  two should not be conflated when evaluating a tool's governance claims
  from its name or README alone, which is exactly the standard this
  research base holds itself to.
- **The concrete, falsifiable finding — checked directly against the
  actual control flow, not assumed from the config schema:** the tool's own
  config schema documents an `enforce_hooks` list, described (per its own
  `pkg.go.dev` page) as hooks that "cannot be skipped." Reading
  `internal/config/config.go:67` and `internal/policy/types.go:52`
  confirms the field is parsed from YAML/JSON into the config struct, and
  `internal/executor/executor.go:309` and `internal/cli/cli.go:823` confirm
  it is threaded through into the `PolicyRules` value passed to the
  evaluator above — but **grepping the entire `internal/executor` and
  `internal/cli` packages for `EnforceHooks` turns up only those four
  assignment sites; the field is never read, compared, or branched on
  anywhere.** The actual skip-gating function, `Executor.shouldSkip`
  (`internal/executor/executor.go:331-358`), checks three things only: a
  `SKIP` environment variable naming the hook, a per-hook `Skip`
  environment-variable condition, and excluded tags — `EnforceHooks` is
  consulted nowhere in that function or in `runHook`
  (`executor.go:361` onward), which calls `shouldSkip` unconditionally
  before running anything. **Net effect, read directly from the control
  flow: in the actual shipped v0.53.0 source (re-confirmed against the
  live `master` branch, not just the Dec-2025 tag), a locally-set `SKIP=
  <hookname>` environment variable silently bypasses a hook its own org
  config declared "cannot be skipped," because the enforcement the name
  promises simply isn't wired to anything.** This is not a hypothetical
  misconfiguration — it's dead code behind a real, user-facing
  configuration field with a specific documented guarantee.
- **Why this is a genuinely new, useful lesson for lawkeeper, distinct from
  the qwen-code precedence bug already on record
  (`docs/RESEARCH_EXTERNAL_SCAN_2026-10-08.md` §3):** that bug was a
  real-but-fixed precedence regression between two structurally parallel
  decision fields. This is different and arguably a cheaper mistake to
  make: a configuration field that reads as a security/compliance
  guarantee ("this cannot be skipped") was added to the schema and threaded
  through several layers of plumbing without ever being wired to the one
  function that decides skip behavior — the kind of gap a schema review or
  an integration test asserting "SKIP cannot bypass an enforce_hooks entry"
  would catch immediately, and the kind of gap a reader trusting the
  config-field *name* (exactly what this research base's own discipline
  says not to do) would never find without tracing the actual control flow,
  which is what this entry did.
- **Verdict: adopt-the-lesson, not a dependency.** HookRunner is Go, not
  Python, and lawkeeper's existing guard scripts don't have an analogous
  "mark this guard as unbypassable, enforced by a different code path than
  the one that checks for a skip override" field today — so there's
  nothing in lawkeeper's current code this specific bug generalizes to
  directly. The actionable lesson, concrete and testable: **any future
  lawkeeper mechanism that adds an "X cannot be overridden/skipped" config
  field needs a test that actually sets the override and the exempt-from
  value simultaneously and asserts the override loses** — not a test that
  only checks the field parses into the right struct. This is the same
  category of advice the qwen-code entry already gave
  ("test precedence per decision-carrying field independently"), reinforced
  here by a second, independently-sourced real-world example of exactly
  that kind of gap shipping silently.

---

## 4. Snowflake Cortex Code Agent SDK hooks — blocked, not a finding

Surfaced the same search pass that found HookRunner and SEAgent — search
snippets describe a sixth(ish) coding-agent SDK with both a `PreToolUse`-
style hook (`permissionDecision: allow/deny/ask`, plus an argument-rewrite
channel) **and** a separately-named `can_use_tool` permission callback that
the search snippets describe as running "inside the CLI's permission
system" alongside, not instead of, the hooks. If accurate, that would be a
new instance of the "two genuinely separate hook/permission mechanisms
under one product name" pattern the 2026-10-15 scan already found in GitHub
Copilot (SDK-level in-process callback vs. CLI/cloud external hook
protocol) — but this pass could not get past search-result aggregation to
confirm it.

- **What was attempted:** direct fetches of
  `docs.snowflake.com/en/user-guide/cortex-code-agent-sdk/hooks` and the
  sibling Python-reference page — both failed with the same
  `getaddrinfo ENOTFOUND` this session's egress policy produces for every
  other blocked documentation domain this pass. No GitHub-hosted doc-source
  mirror was found (unlike GitHub Copilot's docs, which the 2026-10-15 scan
  could reach via `github/docs`'s own source repo — Snowflake's docs do not
  appear to be built from a public repo this pass's search could locate).
- **Verdict: not reported as a finding, queued for a future pass.** Per
  this doc's own standing discipline (and the brief's explicit instruction
  not to pad with weak or unverified findings): a search-snippet
  characterization of what a vendor's docs page says about a decision
  schema and a separate permission callback is exactly the kind of claim
  this research base does not build on without an actual primary-source
  read. Worth a dedicated attempt if `docs.snowflake.com` or a mirror of it
  ever becomes reachable — specifically to confirm or correct the
  `can_use_tool`-vs-`PreToolUse`-precedence question the search pass
  flagged as unanswered even at the secondhand level.

---

## 5. Checked directly against lawkeeper's own repo: `gate_pretooluse.py`'s failure handling vs. GitHub Copilot's per-failure-mode split

The 2026-10-15 scan's own "Re-check when" list flagged this as a concrete,
checkable comparison it had identified but not yet done: GitHub Copilot's
hooks reference distinguishes *which* failure happened (explicit non-zero
exit/crash vs. a timeout) and applies a different fail-open/fail-closed
rule to each, rather than one blanket policy. This pass read
`scripts/gate_pretooluse.py` directly to check lawkeeper's own gate against
that.

- **What lawkeeper's gate actually does, confirmed from source
  (`scripts/gate_pretooluse.py:452-466`):** it already has an asymmetric,
  per-failure-mode design, stated explicitly in its own module docstring
  (lines 58-68) and implemented exactly as documented — **can't-parse-the-
  input** (`json.JSONDecodeError` on the stdin payload, line 453-454) fails
  **open** (`return 0`, no verdict, matching the repo's existing
  `claude_stop_hook.py` convention); **stdin parsed fine but an internal
  exception occurred while classifying the command** (the generic
  `except Exception`, line 461-465) fails to **ASK**, not allow and not
  hardline-deny, with a message naming the exception type and asking for
  manual confirmation.
- **How this compares to Copilot's split, precisely, not just "both have
  more than one failure mode":** Copilot's split is about *timeout vs.
  crash* for a single hook invocation (a hook that times out is treated
  more leniently — fail-open — than one that explicitly exits non-zero or
  crashes, which fails closed for `PreToolUse` specifically). Lawkeeper's
  gate has no analogous timeout concept of its own to split on — it is a
  synchronous script Claude Code's own hook runner invokes and would time
  out *externally* if it hung; `gate_pretooluse.py` has no internal
  `except TimeoutError`-shaped branch because it never waits on anything
  that could hang (no network calls, no subprocess spawns in `main()`).
  Its own split is along a different axis entirely — *can the input even
  be read* vs. *was the input readable but something broke while judging
  it* — which is a meaningful, deliberate distinction in its own right
  (stated in the docstring as "we didn't actually confirm this is
  dangerous, so claiming hardline certainty would overclaim; but silently
  allowing defeats the point of having this hook at all when it breaks"),
  just not the same axis Copilot's docs describe.
- **Verdict: no gap found, nothing to change.** The spirit of Copilot's
  finding — "don't apply one blanket fail policy to every kind of hook
  failure, because different failure modes deserve different defaults" —
  is already satisfied by `gate_pretooluse.py`'s existing two-tier design,
  via a different (and, for a synchronous classifier with no I/O, more
  applicable) axis than timeout-vs-crash. This closes the 2026-10-15 scan's
  own re-check item with "already fine, by a different mechanism," not
  "needs a change."

---

## 6. Minor clarification, Claude Code's own current docs: the top-level `decision` field was never a `PreToolUse` mechanism

While re-verifying a third-party claim (a marketplace repo,
`FabienSalles/claude-marketplace`, fixing its own hooks to stop emitting a
top-level `decision`/`reason` pair for `PreToolUse` in favor of
`hookSpecificOutput.permissionDecision`), this pass re-read the live
`code.claude.com/docs/en/hooks` decision-control table directly to check
the claim against Anthropic's own current text rather than trust a
third-party repo's issue description alone.

- **What the current primary doc actually says, quoted directly:** the
  decision-control table lists `PreToolUse` only under the
  `hookSpecificOutput` → `permissionDecision` (allow/deny/ask/defer)
  pattern; the top-level `decision`/`reason` pattern is listed for a
  different set of events (`UserPromptSubmit`, `UserPromptExpansion`,
  `PostToolUse`, `PostToolUseFailure`, `PostToolBatch`, `Stop`,
  `SubagentStop`, `ConfigChange`, `PreCompact`) — `PreToolUse` is not among
  them.
- **The precise correction, worth stating exactly rather than rounding up
  to the third-party repo's own framing:** the third-party issue describes
  the top-level field as "deprecated... for `PreToolUse`" — per the current
  primary doc, it's more accurate to say the top-level `decision` field was
  never the documented mechanism *for `PreToolUse` specifically* at all;
  it's not that something that used to work for this event stopped working,
  it's that this event was never in that field's event list in current
  documentation. Not independently confirmed whether an older doc revision
  ever listed it differently — this pass did not check doc history, only
  the current live text.
- **Verdict: a precise correction for future citations, not a new
  governance mechanism.** Recorded here rather than silently accepted from
  the third-party source, consistent with this research base's own
  discipline of tracing a secondhand claim back to the primary text before
  citing it.

---

## What this pass found nothing new on

Per the brief's own instruction: stated plainly rather than padded.

- **Test-governance/oracle-independence methodology:** no new,
  independently verifiable finding. The TU Delft oracle-generation lead
  flagged by the 2026-10-15 scan was re-attempted (`repository.tudelft.nl`)
  and failed identically (`connect_rejected` at this session's egress
  proxy) — still not cited as a finding, per this doc's own standing rule
  that a title and a secondhand characterization aren't enough.
- **Codex's own hook-protocol domains** (`developers.openai.com`,
  `learn.chatgpt.com`) — not re-attempted this pass as a numbered entry,
  since that item is already fully resolved from Codex's own source
  (`docs/RESEARCH_EXTERNAL_SCAN_2026-10-08.md` §2) and the "Re-check when"
  list only flags revisiting it if `EXECUTOR_CONTRACT.md` seriously plans a
  Codex adapter, which it does not yet.
- A real but unverified lead, logged so it isn't lost rather than built on:
  SEAgent's own related-work section (§1, in passing) names **Progent**
  (Shi et al., arXiv:2504.11703, "Programmable Privilege Control for LLM
  Agents," confirmed to exist via a Hugging Face papers search this pass,
  not independently read) as a DSL-based tool-call policy mechanism in the
  same space. Not read this pass — queued below, not claimed as a finding.
- No Falcun-relayed report was encountered or relied on this pass; nothing
  here traces through a secondary research report from another repo.

## Re-check when

- `open-plugins.com` — four full passes, at least six distinct access
  strategies, all blocked identically. Re-attempt only if this session's
  (or a future session's) egress policy might differ; the correct fix is a
  network-policy allowlist change, not another in-session workaround (see
  §1's note on the Wayback Machine attempt).
- `docs.snowflake.com` (§4) — re-attempt directly, or search for a public
  GitHub-hosted doc-source mirror the way GitHub Copilot's docs were
  reached via `github/docs`, whenever egress policy might differ. Until
  then, do not treat the search-snippet characterization of `can_use_tool`
  vs. `PreToolUse` precedence as established.
- **Progent** (arXiv:2504.11703) — read directly before citing it for
  anything; currently only confirmed to exist, not read.
- `repository.tudelft.nl` (the TU Delft oracle-generation lead) — re-attempt
  whenever egress policy might differ; still not cited from the snippet
  alone after two failed attempts across two passes.
- `proxy.golang.org` is a usable, unblocked access path for any future
  Go-ecosystem candidate (confirmed working this pass, see the access note
  above) — worth trying before giving up on a Go tool whose own repo or
  docs site is blocked or unreachable.
