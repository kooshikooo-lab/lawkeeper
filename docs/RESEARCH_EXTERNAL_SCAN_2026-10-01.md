# External scan — 2026-10-01

Weekly scheduled research pass. Scope per the routine's own brief: runtime/
`PreToolUse`-style agent governance, policy-decision algebras (allow/deny/ask),
git-hook distribution/enforcement patterns, and test-governance/oracle-
independence methodology. Not Windwright's domain (acoustics/CAD) and not
Falcun's (evolutionary mutation, epistemic-claim verification) — a harness's
other features are out of scope here even when its governance mechanism is
in scope.

Per the brief, this pass **prioritized closing the five items already queued**
in `docs/RESEARCH_agent_harness_landscape.md` and
`docs/RESEARCH_harness_hook_mechanisms_survey.md` before looking for anything
new: pre-commit's own extension model, the Open Plugins hooks specification,
Codex's native hook protocol read directly, MITRE ATLAS's actual technique
matrix, and AWS Cedar's own policy reference. **Three of five are fully
closed** this pass with a direct primary-source read (pre-commit, MITRE
ATLAS, AWS Cedar); **one (Codex) is substantially upgraded but stays
queued** — the evidence improved from a single third party's comment to the
vendor's own issue tracker, but still falls short of this doc's own
primary-source bar (§5 says so explicitly, and that status, not "closed,"
is what the per-entry verdict below actually states); **one (Open Plugins)
is still fully blocked** and stays queued, with a real disambiguation
finding recorded so it doesn't get conflated with a same-sounding but
different spec. One new candidate
(mutmut, for Law 18's mutation-testing requirement) is added afterward, since
oracle-independence/mutation-testing methodology is named in-scope and had
no prior entry in any of the three base documents at all — checked by
grepping `docs/RESEARCH_governance_mechanism_audit.md` for
"mutation|oracle|metamorphic|Law 18|theory card" before starting: zero hits,
confirmed not previously covered.

**Access note, stated up front because it shaped what got read:** this
session's egress proxy blocks a large set of documentation domains outright
(`pre-commit.com`, `open-plugins.com`, `developers.openai.com`,
`learn.chatgpt.com`, `docs.cedarpolicy.com`, `en.wikipedia.org`,
`discovery.ucl.ac.uk`, `web.eecs.umich.edu`, and aval.run mirror tried as a
workaround for one of them — all returned `EGRESS_BLOCKED` from the fetch
tool itself, not a TLS or 404 error, so no retry was attempted per the
proxy's own "do not retry 403s" guidance). `github.com` and
`raw.githubusercontent.com` were not blocked, so every entry below that
reads "actually read" means a GitHub-hosted primary source (source file,
official docs mirrored in a `-docs` GitHub repo, or a project's own issue
tracker) — not the vendor's own docs site, even where the vendor's own docs
site is the more obvious citation. This is noted per-entry too, not just
here.

---

## 1. MITRE ATLAS's actual technique matrix — resolved, previously unconfirmed

- **Prior status:** both base surveys flagged this as the weakest-sourced
  entry in the whole research base — every fetch attempt against
  `atlas.mitre.org` 404'd or returned an empty SPA shell, and whether ATLAS
  covers agentic tool-use techniques at all (vs. only classical ML
  evasion/poisoning) was explicitly unconfirmed.
- **What was actually read this pass:** the live ATLAS data repository's own
  release artifact, fetched and read directly —
  `raw.githubusercontent.com/mitre-atlas/atlas-data/main/dist/v6/
  ATLAS-2026.09.yaml` (resolved from the `ATLAS-latest.yaml` symlink the
  repo's own `dist/` manifest points at — this is the current, live release
  as of this pass, not a stale mirror). Also read the repo's own `README.md`
  directly (`mitre-atlas/atlas-data`), which documents the `dist/`
  versioning scheme (content version `YYYY.MM.N`, format version semver,
  separated since 2026.05/6.0.0) and confirms `atlas-navigator-data` (the
  repo both base surveys' queue entry pointed at) is itself deprecated in
  favor of this one — a real, checkable correction to the queue entry's own
  pointer, not just a content update.
- **License:** Apache-2.0 — confirmed directly by reading the repo's own
  `LICENSE` file (`mitre-atlas/atlas-data`, copyright MITRE 2021-2026). Worth
  recording even though the verdict below isn't a dependency call: the data
  itself is a taxonomy, not executable software, but the same reuse
  diligence this doc applies everywhere else still applies to it, not just
  to things being evaluated as a dependency.
- **The actual finding — confirmed, not secondhand:** the matrix has
  genuinely current (this release, 2026.09) agentic-AI-specific tactics and
  techniques, not just classical ML attack content:
  - Two tactics beyond the classical-ML-attack set both base surveys
    anticipated: **AI Model Access** and **AI Attack Adaptation**.
  - Techniques naming agent tooling specifically, quoted by ID directly from
    the data file: **AML.T0010.005 "AI Agent Tool"**, **AML.T0011.002
    "Poisoned AI Agent Tool"** (tactic: Execution — "a victim may invoke a
    poisoned tool when interacting with an AI agent"), **AML.T0110 "AI Agent
    Tool Poisoning"** and **AML.T0099 "AI Agent Tool Data Poisoning"** (both
    tactic: Resource Development — "adversaries may target AI agent tools as
    a means to compromise a victim's AI supply chain"), **AML.T0084
    "Discover AI Agent Configuration"**, **AML.T0083 "Credentials from AI
    Agent Configuration"**, **AML.T0006.003 "Probe AI Agent Trigger
    Channels"**, and **AML.T0034.002 "Agentic Resource Consumption"**.
  - Checked specifically and explicitly **not found**: no technique in this
    release names bypassing or subverting an *agent harness's own*
    enforcement/gating/permission mechanism (the thing `gate_pretooluse.py`
    is) as its own distinct technique. The closest matches (the tool-
    poisoning and tool-data-poisoning techniques above) are about a
    malicious *tool* being invoked, not about defeating the gate that
    decides whether a tool call executes. This is a real, checked-for gap
    in ATLAS's current coverage, not an assumption that it must be covered
    somewhere.
- **Does this change anything about lawkeeper's own OWASP-gap finding** (the
  governance survey's finding that Law 11/19's team-channel protocol has no
  adversarial framing at all)? No — ATLAS's agent-tool techniques are about
  a compromised *tool* an agent calls, a different threat shape from a
  forged *delegation message* between two lawkeeper-trusted machines. Worth
  stating plainly rather than stretching the fit: this doesn't retroactively
  cover that gap, it's adjacent to it.
- **One concrete thing to check against lawkeeper's own threat model:**
  AML.T0011.002's description ("a victim may invoke a poisoned tool") is a
  real, named precedent for treating an MCP tool server or a Claude Code
  plugin itself as untrusted supply chain — lawkeeper's constitution has no
  law about vetting a tool/MCP-server source before an agent is allowed to
  call it at all (Law 16's enforcement is entirely about what the agent
  *does*, not what external tools it's been given access to). Not urged as
  a new Law here — recorded as a gap this pass can now name specifically
  and with a citable ID, where before it could only gesture at "agentic
  supply chain" vaguely via the OWASP secondhand summary.
- **Verdict: not a dependency (a taxonomy, not software) — adopt as a
  citable threat-model cross-reference.** When lawkeeper's own docs discuss
  the OWASP-identified gaps, cite specific ATLAS technique IDs (AML.T0110,
  AML.T0011.002, AML.T0084, AML.T0083) instead of the vaguer "agentic
  supply-chain vulnerabilities" category name — these are now confirmed,
  current, directly-read IDs, not a secondhand category label. The
  harness-gate-bypass gap (checked, not found) is worth flagging back to
  MITRE's own contribution process at some point, not something lawkeeper
  can resolve itself.

---

## 2. AWS Cedar's own policy reference — resolved, previously partial/secondhand

- **Prior status:** the governance survey had only an AWS blog post (a real
  first-party source, but about Cedar's *use* in Bedrock AgentCore, not
  Cedar's own spec) — `docs.cedarpolicy.com` and the `cedar-policy/cedar`
  repo both hit TLS errors every attempt that pass.
- **What was actually read this pass:** Cedar's own documentation source,
  found via `cedar-policy/cedar-docs` (the GitHub repo the live
  `docs.cedarpolicy.com` site is built from — confirmed from that repo's own
  `README.md`, read directly) — specifically
  `docs/collections/_auth/authorization.md` and
  `docs/collections/_policies/syntax-policy.md`, both fetched and read
  directly via `raw.githubusercontent.com` after `docs.cedarpolicy.com`
  itself was egress-blocked (not a TLS error this time — a hard proxy
  block, so no retry). The top-level `docs/authorization.md` and
  `docs/syntax-policy.md` paths from the governance survey's own citations
  turned out to be Jekyll redirect stubs with no body content — the real
  text lives one level deeper, under `docs/collections/_auth/` and
  `docs/collections/_policies/`, found by reading the repo's own directory
  listing rather than guessing the path a second time.
- **License:** Apache-2.0 — confirmed directly from `cedar-policy/cedar`'s
  own repo page this pass (the governance survey's note that this was
  "secondhand, not independently verified" is now resolved).
- **The actual algorithm, quoted directly from Cedar's own docs, not a
  paraphrase of the AWS blog post:**
  - Default deny, stated outright: "no request is authorized (decision
    `Allow`) unless there is a specific `permit` policy that grants it; by
    default, the decision is `Deny`."
  - The combination rule is three sequential checks, quoted verbatim: "If
    any `forbid` policy evaluates to `true`, then the final result is
    `Deny`. Else, if any `permit` policy evaluates to `true`, then the final
    result is `Allow`. Otherwise..., the final result is `Deny`."
  - Forbid overriding permit is unconditional and order-independent,
    confirmed directly rather than taken from the blog post's paraphrase:
    "even if a `permit` policy is satisfied, any satisfied `forbid` policy
    *overrides* it, producing a `Deny` decision."
  - Strictly two-way, confirmed by direct quote, not inferred from the
    algorithm's shape: "returns `Allow`... or `Deny`..." — no ask/maybe
    value exists anywhere in the authorizer's output.
- **This confirms, rather than changes, the governance survey's existing
  verdict** (adopt the forbid-always-wins precedence idea for a specific
  carve-out — an unconditional-forbid tier with no ASK escape hatch, the
  Law-15 canonical-branch-deletion candidate already named) — but now on a
  direct read of Cedar's own spec text instead of a secondary blog post
  describing it. No new mechanism surfaced beyond what was already logged;
  the upgrade is evidentiary (secondhand-but-first-party → directly read),
  not substantive.
- **Verdict: not-applicable as a dependency (SMT-backed policy analysis is a
  far heavier investment than lawkeeper's current problem), confirmed
  adopt-the-precedence-idea for the no-ASK hardline carve-out** — same
  verdict as before, now resting on primary text instead of a blog post.

---

## 3. pre-commit's own extension model — resolved, new finding against lawkeeper's own repo

- **Prior status:** queued since the first landscape doc (2026-09-05),
  explicitly kept out of scope for both base surveys. The stated reason to
  care: Windwright/orbital-study/falcun reportedly get hand-copied guard
  scripts rather than a shared, versioned distribution (per
  `RESEARCH_governance_mechanism_audit.md`, not independently re-checked
  against those repos this pass — out of this session's GitHub access
  scope, see below).
- **What was actually read this pass:** pre-commit's own source, not its
  marketing docs (`pre-commit.com` itself was egress-blocked this pass, so
  this is a schema-level read rather than the prose docs) —
  `raw.githubusercontent.com/pre-commit/pre-commit/main/pre_commit/
  clientlib.py` (the actual `cfgv`-based schema definitions for
  `MANIFEST_HOOK_DICT` and `CONFIG_REPO_DICT`/`CONFIG_HOOK_DICT`, fetched and
  read directly — this is pre-commit's own enforcement of its manifest
  format, not a description of it) and a real manifest in the wild,
  `raw.githubusercontent.com/pre-commit/pre-commit-hooks/main/
  .pre-commit-hooks.yaml`, fetched and read directly.
- **License:** MIT (`pre-commit/pre-commit`, per the project's well-known
  licensing — not re-verified by reading its LICENSE file directly this
  pass, flagged as such).
- **The actual mechanism, confirmed from schema code, not prose:** a hook
  author ships a `.pre-commit-hooks.yaml` manifest in their own repo
  declaring each hook's `id` (required), `name` (required), `entry`
  (required — the actual command), `language` (required, from a fixed
  enum), plus optional `additional_dependencies`, `args`, and
  `language_version`. A **consuming** repo's `.pre-commit-config.yaml` never
  copies that script's source — it references the hook author's repo by
  `repo:` (a URL) and `rev:` (a pinned tag/SHA), naming only the `id`s it
  wants; pre-commit itself clones that repo at that `rev` into a per-
  language isolated environment and runs it from there. `CONFIG_HOOK_DICT`
  only requires `id`; every other field (`language`, `entry`, dependencies)
  is inherited from the pinned manifest unless explicitly overridden. A
  dedicated `WarnMutableRev` validator fires specifically when `rev` is
  **not** `local`/`meta` and looks like a moving reference (a branch or a
  non-SHA tag) rather than a pin — the framework's own schema layer treats
  "the hook source isn't actually pinned" as a validation-time warning, not
  just a convention.
- **The real, checkable finding against lawkeeper's own repo:** lawkeeper
  does **not** use the pre-commit framework at all today — confirmed
  directly, not assumed from the name collision. There is no
  `.pre-commit-config.yaml` or `.pre-commit-hooks.yaml` anywhere in this
  repo (`find . -iname ".pre-commit-*.yaml"` returns nothing). Every
  "pre-commit" reference in lawkeeper's own source (`scripts/
  validate_pre_commit.py`, `scripts/git-hooks/pre-commit`,
  `install_hooks.py`'s `core.hooksPath` wiring) is the literal git hook
  named `pre-commit`, wired directly via `git config core.hooksPath`, not
  the PyPI `pre-commit` framework. Lawkeeper does have its own distribution
  mechanism for exactly the problem the queue entry named — `lawkeeper init`
  (`src/guardrail/cli.py`'s `cmd_init`) scaffolds a whole
  `src/guardrail/template/` tree (constitution, guard scripts, CI config,
  `.claude/settings.json`) into a consuming repo by **copying files**, not
  by referencing a pinned external source. Checked directly: there is no
  `lawkeeper update`/`sync` subcommand anywhere in `cli.py` — the only lever
  past first-run is `lawkeeper init --force`, which the code's own comment
  describes as "overwrite existing governance," i.e. a full clobber with no
  diff, no field-level merge, and (per the governance-mechanism audit's own
  prior claim about Windwright/orbital-study/falcun, not re-verified this
  pass) no way for a consuming repo to pull just the upstream fixes while
  keeping its own local customizations.
- **What pre-commit's model offers that lawkeeper's `init --force` doesn't,
  stated concretely rather than as a vague "versioning is good" gesture:**
  (1) the hook's source code never lands in the consuming repo's own git
  history at all — only a `repo`+`rev` pointer does, so an upstream fix is a
  one-line `rev` bump, not a file-tree merge; (2) `WarnMutableRev` is a
  precedent worth being precise about rather than overselling — it is
  **advisory, not enforcement**: its own implementation (confirmed by
  reading it directly) is a bare `logger.warning`, not a raised error, and
  its heuristic ("mutable" means no `.` in the rev AND it doesn't match
  `^[a-fA-F0-9]+$`) has a real false-negative gap — a dotted mutable tag
  like `v2.0` or `release.1` skips the check entirely. Still a reusable
  precedent for lawkeeper's own cross-repo pinning discipline (the AEF
  clone pinned to a specific commit SHA, logged in the landscape doc), which
  today does zero mechanical checking at all — but "an advisory check with
  known gaps" is the honest bar to copy, not "pin enforcement"; (3) per-hook
  `id` selection means a consumer can take an upstream update to one guard
  without being forced to accept every other file `init --force` would also
  overwrite.
- **One concrete thing lawkeeper could adopt, scoped honestly:** not a
  migration to the `pre-commit` framework itself (lawkeeper's own hooks are
  plain git hooks invoked via `core.hooksPath`, already a different and
  equally valid mechanism — swapping it for pre-commit-the-tool would be a
  bigger, unjustified architecture change for what is really a
  *distribution*, not an *execution*, gap). The scoped version: add a
  `lawkeeper update` command that re-fetches the template tree pinned to a
  specific `lawkeeper` package release (the version already recorded in
  `.guardrail.json` at init time, if that file records it — not checked
  this pass) and does a real diff against what's already on disk, instead
  of `--force`'s blind overwrite; and consider a `WarnMutableRev`-style
  check wherever lawkeeper's own docs record a pinned external commit (the
  AEF clone, this doc's own git-based research clones) rather than leaving
  "was this actually pinned to an immutable ref" as an unchecked convention.
- **Verdict: adopt-the-design (pinned-reference distribution + a schema-
  level mutable-ref warning), not a dependency.** The `pre-commit` package
  itself is not something lawkeeper's own hook execution needs — it already
  has a working git-hook mechanism — but its *distribution* model is a real,
  concrete answer to a gap this pass could verify still exists in
  lawkeeper's own `cli.py` today, not just in the three sibling repos this
  session has no access to check.

---

## 4. The Open Plugins hooks specification — still blocked, one real disambiguation finding

- **Prior status:** queued since the hook-mechanisms survey (2026-09-06) —
  goose's own `crates/goose/src/hooks/mod.rs` states its plugin-hook system
  is "modelled after the Open Plugins [hooks specification]
  (open-plugins.com/agent-builders/components/hooks)," not read directly at
  that time.
- **What was attempted this pass, and the outcome:** three separate fetch
  attempts, all blocked outright by the egress proxy (not a 404 or TLS
  failure — `EGRESS_BLOCKED` from the fetch tool itself, so none were
  retried, per the proxy's own guidance not to retry a policy denial):
  `open-plugins.com/agent-builders/components/hooks` directly; a cached
  mirror of the same URL surfaced by search
  (`*.web.val.run/https://open-plugins.com/...`) — also blocked, same
  domain-policy class of failure, not a different problem; and a search for
  a GitHub-hosted copy of the spec itself. **Still unresolved — this entry
  stays queued, exactly as the honesty discipline requires**, not closed on
  secondhand confidence.
- **A real finding from the search attempt, worth recording precisely so it
  doesn't get conflated later:** search results surfaced a *different*,
  confusingly similarly-named spec — **"Agent Plugins Specification"**
  (`agent-plugins.org`, GitHub repo currently reachable at
  `github.com/vercel-labs/open-plugin-spec`, maintained by an "agentplugins"
  org per its own README) — fetched and read directly this pass. Confirmed
  directly: this is version 1.0.0 (1.1.0 in working draft), defines a
  package format for **Agent Skills and MCP servers** (a `plugin.json`
  manifest, a `skills/` directory of markdown skill files), and its own
  README **contains no mention of hooks, `PreToolUse`, or any
  policy/permission event at all** — it is not the same specification goose
  cites, despite the near-identical name and overlapping subject area
  (agent-extension packaging). **This is logged explicitly so a future pass
  doesn't cite "Agent Plugins Specification" as if it covered the hooks
  mechanism open-plugins.com's own spec describes** — it doesn't, confirmed
  by direct reading, not assumed from the name.
- **Verdict: unresolved, re-queue again** — needs either a different access
  path next time (the person operating this routine may be able to
  allowlist `open-plugins.com` for a future session, or a future session's
  proxy policy may simply differ) or a GitHub mirror this pass's search
  didn't surface. Do not substitute the Agent Plugins Specification for it.

---

## 5. Codex's native hook protocol, read directly — substantially upgraded, still not a first-party doc read

- **Prior status:** every claim about Codex's hook protocol in both base
  surveys was secondhand, sourced through a single comment in
  deepseek-harness's own bridge-implementation code ("faithful-but-degraded
  — e.g. Codex ignores `allow`/`ask`") — a real, first-party statement from
  a team that had to implement compatibility, but still one step removed
  from Codex's own docs or source.
- **What was attempted this pass:** `developers.openai.com/codex/hooks` and
  its current redirect target `learn.chatgpt.com/docs/hooks` were both
  egress-blocked outright this pass (same `EGRESS_BLOCKED` class as above,
  not retried). `github.com/openai/codex`'s own `docs/` directory was
  readable (fetched and read directly) but does not contain a dedicated
  `hooks.md` — the closest file, `docs/config.md`, was fetched directly and
  its own "Lifecycle hooks" section (quoted directly: admins can set
  `allow_managed_hooks_only = true` in `requirements.toml` to restrict which
  hook configs apply) confirms hooks are a real, current Codex feature, but
  this file does not contain the wire-format details.
- **What closed most of the gap instead — OpenAI's own issue tracker,
  fetched and read directly, not a third party's reverse-engineering:**
  three GitHub issues on `openai/codex` itself (the maintainers' own
  tracker, filed by users reporting real, reproduced behavior against the
  shipped product), plus one detailed external issue that explicitly quotes
  the official doc text with citations. All fetched and read directly this
  pass, not aggregated from search snippets alone:
  - **`openai/codex#27833`**: a project-scoped `PreToolUse` hook on
    `apply_patch` fires and reports `Failed`, but the write proceeds anyway
    — reproduced through *both* documented deny channels (exit code 2 with
    a stderr message, and `hookSpecificOutput.permissionDecision: "deny"` on
    stdout), reported on `0.133.0`/`0.138.0-alpha.7`. **Behaviour varies by
    version and platform** (issue and all comments re-read directly via the
    GitHub API on 2026-10-02 from a session with full access; still open):
    a 2026-08-09 comment reports `deny` for `apply_patch` **enforced** on
    `0.147.0` (macOS, bash); comments from 2026-07-06 (Codex Desktop,
    `shell_command`) and 2026-09-15 (**Windows, Codex CLI `0.154.0`**,
    Bash/PowerShell calls) report the same non-enforcement -- but the
    2026-09-15 reporter also found the identical hooks **enforced** on the
    same `0.154.0` build with a fresh, empty `CODEX_HOME`, so configuration
    state matters, not only version or platform. So: an open enforcement gap
    that depends on version, platform, tool-call type and configuration
    state; not a confirmed product-wide fact and not shown fixed.
  - **`openai/codex#49736`** (single open report, filed 2026-09-30, no
    replies as of 2026-10-02): a `PreToolUse` hook matching `spawn_agent`
    (Codex's sub-agent-spawn tool call) was **not invoked** when a
    sub-agent was spawned in the reporter's interactive session — the
    reporter verified their own hook script works by piping the identical
    payload into it by hand, which points at Codex's dispatch rather than
    the guard script. Unconfirmed by anyone else yet.
  - **`i9wa4/dotfiles#378`**: not a bug report against Codex, but a careful,
    citation-backed analysis of Codex's own documented contract — states
    plainly, citing the official docs directly, that `permissionDecision:
    "ask"` is **"parsed but not yet supported"**: Codex's hook dispatcher
    recognizes the field but has no code path that acts on it, and the
    documented behavior for any unsupported/unparseable hook response is to
    mark the hook run `Failed`, log an error, and **continue the tool call
    anyway** — fail-open, not fail-closed, confirmed as Codex's own stated
    design, not inferred from absence. The same issue states `"allow"` is
    only meaningfully supported paired with `updatedInput` (a rewrite); a
    bare `"allow"` hits the same unsupported-value fail-open path as `"ask"`.
- **Does this change the prior "Codex's hook protocol is binary, no ask"
  claim?** Refines it in a way worth being precise about: the wire format
  itself is **not** binary by design the way goose's or Hermes'
  external-hook protocols are (those simply have no `ask` field in their
  JSON schema at all) — Codex's own schema *does* parse a three-valued
  `permissionDecision`, including `"ask"`. The practical behavior is binary
  anyway, for a different reason: `"ask"` is accepted syntactically but has
  **no implemented handler**, so it fails open to "continue," which is
  observably identical to never having had an `ask` concept in the wire
  format at all. That's a materially different fact than dsh's comment
  implied (schema omission vs. unimplemented-but-present field) and matters
  if lawkeeper's `EXECUTOR_CONTRACT.md` ever needs to describe *why* a
  Codex adapter can't use `ask` — "the field exists and is silently a
  no-op, don't rely on it" is a sharper, more dangerous-if-missed warning
  than "the field doesn't exist."
- **A second, independent finding beyond the ask question — stated as what
  was actually read, not as a settled current-state claim:** two open,
  filed bug reports (`apply_patch` in `#27833`, `spawn_agent` in `#49736`)
  describe `deny` not being enforced for those specific tool calls, each
  with the reporter's own reproduction steps and version numbers (`0.133.0`
  and `0.138.0-alpha.7` for `#27833`). The cloud pass that wrote this could
  not see `#27833`'s comments (fetch-tool limitation); a follow-up read of
  the issue and all its comments through the GitHub API on 2026-10-02 found
  them: one report of `deny` **enforced** on `0.147.0` (macOS) and two later
  reports of **non-enforcement** (Codex Desktop `shell_command`, 2026-07-06;
  Windows CLI `0.154.0` Bash/PowerShell, 2026-09-15). Codex's current
  source was **not** read in either pass, so the reviewer's note that it
  maps a valid `deny` to `Blocked`/`should_block` and wires `apply_patch`
  and `spawn_agent` hooks is SECONDHAND here. **So, stated carefully: open,
  reports whose outcome depends on version, platform, tool-call type and
  configuration state (non-enforcement on Windows `0.154.0` with a long-used
  `CODEX_HOME`, enforcement on the same build with a fresh one); not a
  settled product-wide claim either way** — don't read "deny isn't enforced" as true everywhere today,
  and don't read the `0.147.0` macOS result as a fix. Worth
  recording as a concrete reason a future non-Claude-Code adapter in
  `EXECUTOR_CONTRACT.md` would need its own characterization tests per
  tool-call type, version and configuration state (exactly the discipline
  `tests/test_gate_pretooluse_scope_boundary.py` already applies to
  lawkeeper's own Claude Code hook), precisely because this doc's own
  attempt to pin down current behavior from the issue tracker alone hit a
  real limit here.
- **Honesty about what's still not done:** this is still not a read of
  Codex's own first-party documentation page or its hook-dispatch source
  code directly — it's three directly-read GitHub issues, one of which
  itself quotes the official docs secondhand. That is a real evidentiary
  upgrade from "one third party's implementation comment" to "the
  maintainers' own issue tracker plus a citation-backed independent
  analysis," but it is not yet the primary-source bar this doc's own
  discipline sets for a "fully resolved" entry — re-attempt
  `developers.openai.com`/`learn.chatgpt.com` directly in a future session
  if the egress policy ever allows it, rather than treating this as closed.
- **Verdict: adopt-the-warning for `EXECUTOR_CONTRACT.md`, not a
  dependency.** If lawkeeper ever adapts to Codex: do not emit
  `permissionDecision: "ask"` and assume a human gets prompted — it is
  parsed and silently ignored, continuing the tool call, per Codex's own
  documented behavior as quoted (not inferred) in `i9wa4/dotfiles#378`;
  budget for `deny` itself needing a per-tool-call-type characterization
  test, not a single blanket assumption that the documented contract holds
  for every tool.

---

## 6. New candidate: mutmut (Python mutation testing) — compared against Law 18's own T4 mechanism

Not part of the queue — added because the task brief names
test-governance/oracle-independence methodology as explicitly in scope, and
a direct grep of `docs/RESEARCH_governance_mechanism_audit.md` for
"mutation|oracle|metamorphic|Law 18|theory card" returned zero hits before
starting this entry — confirmed, not assumed, that no prior pass in any of
the three base research docs has looked at an actual mutation-testing tool
against lawkeeper's own Law 18 mechanism.

- **What was actually read this pass:** `scripts/governed_test.py`'s own
  `run_mutation` function (lawkeeper's own T4 "discrimination check"
  implementation, read in full, not summarized from the module docstring
  alone) and, externally, `github.com/boxed/mutmut`'s own README, fetched
  and read directly.
- **License:** BSD-3-Clause, confirmed directly from the repo's own LICENSE
  badge/file.
- **What lawkeeper's own mechanism actually does, confirmed by reading the
  code, not the theory-card convention's prose description:** a theory
  card's `mutation` block names exactly one `file`/`attr`/`new_value`
  triple; `run_mutation` regex-substitutes a single module-level
  `attr = <value>` assignment line, runs the real test suite against the
  mutated file, confirms the **baseline** (unmutated) run passes first
  (a real bug this function itself was patched for, 2026-09-06, per its own
  comments — a broken baseline previously produced false "discriminates"
  results), then restores the original file in a `finally` block. This is
  exactly one hand-authored mutation per card, chosen by whoever wrote the
  card, with no mechanism checking whether other mutations to the same code
  would also be caught.
- **What mutmut does differently, confirmed from its own README:** mutation
  generation is automatic and comprehensive across an entire target file or
  package, not one hand-declared edit — documented operator classes include
  integer-literal increment (`0`→`1`), comparison-operator swaps (`<`→`<=`),
  and control-flow inversions (`break`↔`continue`), applied everywhere they
  occur; it tracks survived-vs-killed mutants and reports an aggregate
  mutation score (`mutmut badge` for a Shields.io-style badge,
  `mutmut export-cicd-stats` for CI reporting), and supports scoped
  exclusion (`# pragma: no mutate`, block/range variants, and
  config-level `do_not_mutate`/`only_mutate` file patterns) for mutations a
  maintainer has deliberately decided not to require coverage for.
- **The actual tradeoff, stated concretely rather than as "more mutation
  testing is better":** lawkeeper's hand-declared single mutation is
  *legible* — a reviewer can read the theory card and know exactly what
  blind spot this specific test was checked against, which is the whole
  point of Law 18's "blind spot" field — but it has **no coverage
  guarantee** beyond whatever blind spot the card's author happened to
  think of; a mutant mutmut would generate and the test would fail to kill,
  but that nobody wrote into a card, is invisible to lawkeeper's current T4
  check entirely. mutmut's comprehensive, automatic generation has the
  opposite tradeoff — a mutation score is a real coverage signal across the
  whole file, but a single aggregate score doesn't carry the
  per-mutation "this is the specific blind spot we checked" narrative Law
  18's card format is built around.
- **One concrete thing lawkeeper could adopt, scoped — and scoped honestly
  about what mutmut itself does vs. what would need building:** not a
  replacement for the theory-card mutation field (that's doing real,
  different work — documenting *which* blind spot was deliberately checked,
  for a human reviewer) but a **supplementary, non-blocking mutmut pass**
  over files a theory card already covers. mutmut on its own has no concept
  of a theory card and would only report its own ordinary survived/killed
  mutant counts — it cannot produce a "survived mutants not covered by any
  declared card" figure by itself. Getting that specific, more useful
  number would mean a separate, lawkeeper-authored mapping step: for each
  survived mutant mutmut reports, check whether its target `file`/`attr`
  matches any theory card's declared `mutation` block, and report only the
  unmatched survivors as the actual gap signal. Recorded as two distinct,
  separately-sized pieces of future work — plain mutmut adoption (small),
  and the card-correlation step on top of it (its own real scope, not
  included for free) — not urged for immediate implementation either way.
- **Not read this pass, flagged rather than silently assumed equivalent:**
  `cosmic-ray` (the other commonly-cited Python mutation-testing tool) —
  named here only because it came up adjacent to mutmut in search results,
  not independently evaluated; if a future pass pursues the supplementary-
  pass idea above, compare both rather than defaulting to mutmut on name
  recognition alone.
- **Verdict: worth-a-dependency for a supplementary, non-blocking coverage
  signal; not a replacement for Law 18's existing declared-mutation
  mechanism**, which does different, legibility-focused work mutmut's
  aggregate score doesn't replicate.

---

## What this pass found nothing new on

Per the task brief's own instruction: stated plainly rather than padded.
Nothing in this pass's reading turned up a new, independently verifiable
finding about policy-decision algebras beyond confirming (not extending)
Cedar's and ATLAS's existing entries above — the deny>ask>allow convergence
question itself (five independently-built systems, per the hook-mechanisms
survey) was not revisited this pass since nothing new surfaced to add to it.
No Falcun-relayed report was encountered or relied on this pass; nothing
here traces through a secondary research report from another repo.

## Re-check when

- `open-plugins.com` — retry direct access whenever this session's (or a
  future session's) egress policy might differ; do not substitute the
  "Agent Plugins Specification" (`agent-plugins.org`) for it, confirmed
  this pass to be a different, hooks-free spec.
- Codex's hook protocol — re-attempt `developers.openai.com/codex/hooks` or
  `learn.chatgpt.com/docs/hooks` directly if ever reachable; the GitHub-
  issue-sourced account here is a real evidentiary upgrade but still not
  this doc's own primary-source bar.
- `lawkeeper update`/pinned-distribution gap (§3) — re-check after any
  session that touches `src/guardrail/cli.py`'s `cmd_init`, since this
  entry's claim ("no update/sync subcommand exists") is a snapshot of
  today's `main`, not a permanent property of the codebase.
