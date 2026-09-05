# Harness governance survey — prior art for the missing runtime layer

Started 2026-09-05. `docs/RESEARCH_agent_harness_landscape.md` established that
lawkeeper's enforcement stack (Law 16) only fires at git boundaries
(pre-commit/commit-msg/pre-push + CI), and that Omnigent is one working
implementation of the missing layer — a tool-call-level ALLOW/DENY/ASK gate
that runs *inside* the agent's own loop, between commits. That doc's own
"Candidate projects queued for future entries" section named three things to
read before designing anything from scratch: **OPA/Rego**, **pre-commit's own
extension model**, and **Anthropic's Claude Agent SDK permission/hook
system**. This survey resolves the first and third of those (OPA/Rego,
Claude Agent SDK) plus everything in the assignment below. pre-commit's
extension model stays queued, untouched, for a future pass — it wasn't in
scope here and nothing below substitutes for actually reading it.

Same discipline as the landscape doc: every entry states what was **actually
read** (spec text, official docs, primary source file) versus what's
secondhand (aggregated from search results or a blog post) — and says so
explicitly, not implicitly. No vague enthusiasm; every entry ends with a
concrete adopt-the-design / worth-a-dependency / not-applicable verdict.

---

## 1. Access-control formalisms — the real prior art under all of this

### PDP/PEP (XACML's decomposition)

- **What was actually read:** Oracle's XACML PEP tutorial
  (docs.oracle.com/cd/E24191_01/common/tutorials/authz_xacml_pep.html) —
  covers PEP and PDP in concrete workflow terms. NOT read: an actual XACML
  spec text for PAP/PIP (the tutorial doesn't cover them; this entry is
  honest about that gap rather than inventing detail).
- **License:** N/A — a standard/pattern, not software to depend on.
- **The actual decomposition, in its own terms:** PEP intercepts the real
  request (a filter, a gateway, an application boundary) and translates it
  into a structured authorization query (subject/resource/action/environment
  attributes) sent to the PDP. The PDP is stateless with respect to the
  calling application — it knows nothing about HTTP, files, or git; it only
  evaluates policy against attributes and returns one of `Permit` / `Deny` /
  `NotApplicable` / `Indeterminate`. The PEP then enforces that decision
  (allow-through or block) and applies any `Obligations` the PDP attached.
  The problem this decomposition solves, in its own terms, is **letting
  policy evolve independently of every place that needs to enforce it** —
  many PEPs (a web gateway, a file server, a database proxy) can all defer to
  one PDP instead of each embedding its own copy of the rules.
- **Confirm/correct the framing:** an AI-agent tool-call gate is a PEP/PDP
  instance almost exactly as described — the agent harness (Claude Code, or
  whatever runs the tool call) is the PEP; a policy engine deciding
  ALLOW/DENY/ASK is the PDP. Omnigent's own architecture (already documented
  in the landscape doc) literally is this: harness adapters are PEPs, the
  runtime policy engine is the PDP. Worth naming explicitly, because it means
  lawkeeper isn't choosing between "invent a new pattern" and "copy Omnigent"
  — it's choosing an instantiation of a 20-year-old decomposition either way.
- **One concrete adoption:** none directly — XACML itself (the four-point
  PAP/PDP/PEP/PIP architecture, the specific request/response XML schema) is
  not something lawkeeper should adopt; it predates and is heavier than what
  a single-repo git-hook tool needs. **Verdict: not-applicable as a
  dependency, but adopt-the-vocabulary** — when lawkeeper's own design docs
  describe a future in-loop gate, calling the git-hook layer "PEP-shaped" and
  a future policy-decision module "PDP-shaped" gives precise, already-
  load-bearing terminology instead of reinventing loose language for the
  same split Law 16 already gestures at (local hooks + CI backstop already
  are two independent PEPs enforcing one shared, external decision — the
  constitution's laws are already acting as the PDP's policy source; that's
  worth stating as a real finding, not a coincidence).

### RBAC vs ABAC vs ReBAC

- **What was actually read:** NIST's own ABAC definition is cited across
  multiple secondary sources as SP 800-162 ("Guide to Attribute Based Access
  Control (ABAC) Definition and Considerations") — this entry did **not**
  fetch and read SP 800-162's PDF text directly (repeated tool failures on
  that URL this pass); the definition below is reconstructed consistently
  across several secondary sources (guptadeepak.com, pangea.cloud,
  plainid.com), which agree closely enough on wording to trust the
  paraphrase, but this is secondhand, not a primary read, and is logged as
  such.
- **License:** N/A — access-control models, not software.
- **The actual distinction:** RBAC assigns permissions to named roles, then
  users to roles — cheap to reason about, breaks down when the permission
  actually needed is a function of context ("this user, this specific file,
  right now") rather than a fixed job function. ABAC evaluates a policy
  (a boolean expression) against attributes of the subject, the resource,
  the action, and the environment — no fixed role vocabulary, but harder to
  audit ("what can Alice do" requires evaluating the policy against every
  resource, not reading a role list). ReBAC grants access based on graph
  relationships between subjects and objects (Alice can edit this doc
  because she owns the folder it's in).
- **Confirm or correct the task's own framing:** confirmed — a tool-call gate
  (should this specific Bash command, with this specific argument, from this
  specific agent session, right now, be allowed) is unambiguously an ABAC
  decision, not RBAC. There is no fixed small set of "roles" a tool call
  falls into; the decision is a function of live attributes (which tool,
  which argument pattern, which file path, which branch, time of day,
  whether a human is present to ask). Omnigent's CEL-based policy conditions
  (documented in the landscape doc) are exactly ABAC-shaped rule expressions
  over a `PolicyEvent`'s attributes. Claude Code's own permission rules
  (§2 below) are also ABAC — `Bash(rm *)`, `Read(./.env)`, `Agent(model:opus)`
  are all attribute predicates over the tool call, not roles.
- **One concrete adoption:** confirms, rather than changes, lawkeeper's
  existing design instinct — any future in-loop gate should be specified as
  an ABAC policy language (attributes of the tool call + repo state) from the
  start, not as a role table that will need bolting-on later. **Verdict:
  adopt-the-framing** — no new mechanism, but a correct name for what any
  future Law-16-extension mechanism already has to be.

### Open Policy Agent (OPA) / Rego

- **What was actually read:** OPA's own philosophy page
  (openpolicyagent.org/docs/latest/philosophy/) and its policy-language page
  (openpolicyagent.org/docs/latest/policy-language/) — both official docs,
  fetched and read directly, covering the base/virtual document model,
  incremental rule definition, `default`, and rule-conflict errors. Also
  corroborated (secondhand, from search-result aggregation of OPA's FAQ and
  community blog posts, not independently fetched and read in full) the
  "aggregate `deny` set across packages" composition pattern used in
  real-world Rego policies for Kubernetes/Terraform gating.
- **License:** Apache 2.0 — genuinely usable as a dependency if lawkeeper
  ever wants an embeddable policy evaluator rather than hand-rolled Python
  guard scripts.
- **The actual decision/composition model, in Rego's own terms:** OPA has no
  built-in notion of "policy" as a named, orderable unit the way Omnigent
  does. Everything is a **document** — `data` (external/base facts) and rules
  that compute **virtual documents**. Multiple rules sharing a name compose
  by **union** for partial rules (sets/objects — genuinely additive, no
  conflict possible) but by **error** for complete rules (`allow := true` in
  one file and `allow := false` in another is not "the second one wins" — it
  is an undefined-document evaluation error, full stop). `default` supplies a
  fallback only when *no* rule fires, not a fallback when rules disagree.
  Composition of multiple *modules/packages* into one decision is left
  entirely to policy authors — Rego provides the primitives (`default`,
  negation, incremental union) but, per its own docs and the community's own
  accumulated convention, **there is no standard allow/deny precedence
  algebra baked into the language**. The de facto community pattern (each
  package contributes to a shared `deny` set of violation messages; the
  top-level decision is `count(deny) == 0`) is a convention, not a language
  guarantee — every non-trivial Rego deployment (Kubernetes admission,
  Terraform gating) re-derives this pattern rather than importing it from a
  library.
- **Comparison to Omnigent's DENY>ASK>ALLOW (already documented in the
  landscape doc):** genuinely different, not the same thing wearing OPA's
  syntax. Omnigent's engine has a first-class three-way verdict with a fixed
  precedence rule *built into the runtime* (`engine.py`'s loop, not policy
  author's choice). OPA has no such runtime-enforced precedence for anything
  beyond simple document union/error; a Rego-based ALLOW/DENY/ASK system
  would have to be **built on top of** OPA by policy-author convention (a
  `verdict` document that a wrapping caller interprets), exactly the way the
  Kubernetes/Terraform `deny`-set convention already is. So the honest
  answer to the task's question ("is there a standard conflict-resolution
  algebra in policy-as-code, or does everyone invent their own") is: **no
  standard algebra exists even in the most mature policy-as-code ecosystem —
  OPA deliberately punts this to convention**, and that absence is itself the
  finding.
- **One concrete adoption:** if lawkeeper's guards ever grow past
  hand-written Python scripts into something a non-maintainer should be able
  to configure without writing Python (Omnigent's own CEL-for-untrusted-
  authors argument, already logged in the landscape doc, applies equally
  here) — Rego is a mature, sandboxed, Apache-licensed choice for that DSL,
  with a real ecosystem (`opa eval`, unit-test framework, VS Code tooling)
  lawkeeper doesn't have to build. It would change how new Laws get authored:
  a Law becomes a `.rego` file with a `deny` rule and a unit test, evaluated
  by an embedded `opa` binary or the `github.com/open-policy-agent/opa/rego`
  Go package, rather than a new Python module wired into `guardrail/laws/`.
  **Verdict: worth-a-dependency, but only if/when lawkeeper needs
  non-maintainer-authored rules** — for the current maintainer-authored,
  Python-native `guardrail/laws/` registry, rewriting into Rego today would
  be a large migration for no functional gain; the honest verdict is
  **not-yet-applicable**, revisit if that non-maintainer-authoring need
  becomes real.

### AWS Cedar

- **What was actually read:** the AWS Security Blog post "Why Policy in
  Amazon Bedrock AgentCore chose Cedar for securing agentic workflows"
  (aws.amazon.com/blogs/security/...) — an official first-party AWS source,
  fetched and read directly, and specifically about securing *agentic AI
  tool calls*, not authorization in general. NOT read: Cedar's own policy
  reference docs at docs.cedarpolicy.com (repeated TLS failures fetching
  that host this pass) or the Cedar POPL paper's full text (only its abstract
  and a secondhand summary were available via search). This entry is
  explicitly a partial read — real, first-party, but narrower than ideal.
- **License:** Apache 2.0 (`cedar-policy/cedar` on GitHub, per public
  knowledge — not independently verified by reading the repo's LICENSE file
  this pass; flagged as secondhand).
- **The actual decision model, per the AWS post:** `permit` and `forbid`
  statements; **default deny** (nothing is allowed unless some `permit`
  matches); **forbid always wins** over any matching `permit`, unconditionally
  and regardless of authoring order — "no ordering dependency," in the post's
  own words. This is a real, meaningfully different algebra from both Rego
  (no built-in precedence at all) and Omnigent (DENY > ASK > ALLOW, a
  three-way verdict) — Cedar is a clean two-way `forbid`-beats-`permit` with
  no ASK concept in the language itself. The distinguishing feature over
  every other system in this survey is **formal verifiability**: Cedar
  policies compile to SMT and can be proven, not just tested, to have
  properties like "refactoring this policy set doesn't change who's
  authorized" or "no policy is unsatisfiable/dead." The AWS post frames this
  as directly relevant to agentic security because a human reviewer cannot
  reliably eyeball a real policy set for logical gaps ("impossible
  conditions," "overly permissive rules") at scale, especially once an LLM
  is generating or modifying policies.
- **Is formal verification relevant to a constitution's laws needing formal
  verification?** Genuinely, partially. Lawkeeper's laws are prose
  (`AI_CONSTITUTION.md`) checked by ad hoc Python predicates — there is no
  way today to ask "do laws 4 and 6 ever contradict for some diff" the way
  Cedar Analysis can ask "do these two policies ever disagree." That's a real
  capability gap, but a much bigger investment than anything else in this
  survey — it would mean either encoding the *laws themselves* (not just tool
  calls) in an analyzable policy language, a project on the order of
  rewriting the constitution, not extending a guard script.
- **One concrete adoption:** the specific, cheap thing worth taking is
  **forbid-always-wins as an explicit, stated precedence rule**, distinct
  from Omnigent's three-way DENY>ASK>ALLOW — if a future lawkeeper in-loop
  gate ever needs a *simpler* two-way (not three-way) precedence for a subset
  of checks (e.g. Law 15's branch-deletion guard: nothing overrides a
  canonical-branch-deletion forbid, full stop, no ASK escape hatch), Cedar's
  model is the citable precedent for "some decisions shouldn't have an ASK
  tier at all." **Verdict: adopt-the-precedence-idea for a specific carve-out
  (unconditional forbids that skip ASK entirely), not-applicable as a
  dependency** — Cedar's SMT-backed analysis tooling is a heavier investment
  than lawkeeper's current problem justifies.

### Kubernetes admission controllers

- **What was actually read:** the official Kubernetes docs page on admission
  controllers (kubernetes.io/docs/reference/access-authn-authz/
  admission-controllers/), fetched and read directly.
- **License:** N/A — a mechanism inside Kubernetes' own architecture, not a
  standalone dependency candidate.
- **The actual model:** two phases — **mutating** admission controllers run
  first (can rewrite the request; a mutation re-triggers re-validation of
  already-run webhooks), then **validating** controllers run (accept or
  reject only, no rewriting). Composition across controllers in either phase
  is **pure AND**: every controller must accept, or the whole request is
  rejected — there is no ALLOW/DENY/ASK three-way and no precedence puzzle,
  because there's no "allow" verdict to compete with a "deny" — every
  controller either raises an objection or stays silent, and any objection
  is fatal. `failurePolicy` (`Fail` vs `Ignore`) governs only what happens
  when a webhook itself is unreachable/errors, a different axis from the
  request's actual accept/reject content.
- **Real structural analog, or false friend?** Genuinely a real structural
  analog for the **mutate-then-gate** shape (a policy can rewrite the
  request before the final accept/reject, exactly like Omnigent's
  content-rewriting policies documented in the landscape doc's deeper pass),
  but a **false friend** for the precedence question — admission control's
  "any objection is fatal, no override" is structurally closer to Cedar's
  forbid-wins than to Omnigent's three-tier ALLOW/DENY/ASK, and it has no ASK
  concept at all (an admission webhook cannot pause and wait for a human;
  Kubernetes' API server has no synchronous human-approval primitive). Citing
  it as evidence for a three-way gate would be overreaching what the source
  actually supports.
- **One concrete adoption:** the **mutate-then-validate ordering** (rewrite
  first, check the rewritten result, not the original) is directly
  transferable to a hypothetical lawkeeper "auto-fix-then-check" flow (e.g.
  strip a stray secret from a diff, then run the audit-marker check against
  the cleaned diff) — cheaper to adopt than Omnigent's general
  content-transformation pipeline because it's just "run fixers before
  checkers," already close to how `pre-commit`'s own fixer hooks work today.
  **Verdict: adopt-the-ordering-idea (mutate-then-validate) for a future
  auto-fix guard, not-applicable for the precedence/ASK question** — that
  part of the analogy doesn't hold.

---

## 2. AI-agent-specific governance/guardrail systems

### Claude Agent SDK / Claude Code's own permission + hooks system

This is the single most important finding in this survey — see the closing
recommendation.

- **What was actually read:** the official Claude Code docs, both fetched
  and read in full directly: `code.claude.com/docs/en/hooks` (hook events,
  decision JSON shape, exit-code semantics, multi-hook composition) and
  `code.claude.com/docs/en/permissions` (permission rule syntax, evaluation
  order, permission modes, how hooks and rules interact) — these are current,
  first-party Anthropic documentation for the exact product lawkeeper already
  targets (Claude Code sessions).
- **License:** N/A — this is the actual runtime lawkeeper's target agent
  already runs inside, not a dependency to add; the question isn't "can we
  depend on it" but "does it already do the thing lawkeeper would otherwise
  build."
- **The actual decision model — and it already IS a three-way ALLOW/DENY/ASK
  gate:** Claude Code's permission system evaluates **deny, then ask, then
  allow, in that fixed order — first match wins, and rule specificity never
  overrides the order** (quoting the docs directly: "a broad deny rule...
  blocks every matching call, including calls that also match a narrower
  allow rule... a matching ask rule prompts even when a more specific allow
  rule also matches the same call"). This is, functionally, the *exact same
  precedence Omnigent implements* (DENY beats ASK beats ALLOW, documented in
  the landscape doc's deeper pass) — not a coincidence worth glossing over: two
  independently-designed systems converged on the identical three-tier
  algebra for the identical problem (gating an agent's actions). That
  convergence is itself evidence there *is* a natural algebra for this
  specific problem, even though §1 found none in general policy-as-code.
  On top of the static allow/deny/ask rule table, **`PreToolUse` hooks are a
  live, arbitrary-code PDP**: a hook receives the tool call as JSON on stdin
  and can return `permissionDecision: "allow"|"deny"|"ask"`, or force a hard
  block via exit code 2 (which overrides even a JSON "allow", and overrides
  a matching allow *rule*, though it can never override a matching **deny**
  rule or a matching **ask** rule set in a *managed* settings file — the docs
  are explicit that "hook decisions don't bypass permission rules" for those
  two cases). Multiple hooks run in parallel per event; any single
  `deny`/exit-2 wins, `ask` beats `allow`, matching Omnigent's DENY>ASK>ALLOW
  precedence again at the hook layer.
- **Does it already offer what lawkeeper would otherwise invent?** Yes, to a
  degree that changes the shape of the recommendation below. A `PreToolUse`
  hook that shells out to a script, receives the exact tool name and full
  argument JSON, and returns a deny/ask/allow decision **is** a tool-call-
  level policy gate, wired into the actual product lawkeeper already targets,
  with no new harness-adapter code needed at all. It is not a general
  cross-harness abstraction (it's Claude-Code-specific, whereas Omnigent's
  adapter pattern is explicitly harness-agnostic across Claude Code, Codex,
  Cursor, etc.) — but for the concrete, immediate problem statement in the
  landscape doc ("a bad `rm -rf` or an unreviewed shell command run
  mid-session is invisible until something gets staged"), a `PreToolUse` hook
  running one of lawkeeper's own guard scripts (the same Python already
  living in `scripts/`, called from a hook instead of only from
  pre-commit) closes that exact gap **today**, with no new engine to build.
- **One concrete, specific thing to adopt:** write a `PreToolUse` hook
  (`.claude/hooks/lawkeeper-pretooluse.py` or similar) that runs against
  `Bash` tool calls specifically, re-using lawkeeper's existing branch-guard
  and destructive-command detection logic (the same checks `guard_branch.py`
  already has for git-layer enforcement) as a live gate instead of only a
  git-hook-time gate — this changes **Law 16 specifically**: it would add a
  fourth enforcement layer ("live tool-call gate, in addition to local
  hooks + CI + self-audit") using a mechanism Claude Code already ships,
  rather than inventing Omnigent's runtime engine. This is narrower than
  Omnigent (Claude-Code-only, not harness-agnostic) but is buildable now, in
  lawkeeper's own repo, with zero new dependencies.
- **Verdict: adopt directly — this is a dependency in the sense that
  lawkeeper's target runtime already ships the exact hook point needed; the
  work is writing the hook script, not building a policy engine.**

### NeMo Guardrails vs Guardrails AI vs Llama Guard — the content-vs-action distinction the task warned about

- **What was actually read:** NVIDIA's own NeMo Guardrails introduction docs
  (docs.nvidia.com/nemo/guardrails/latest/introduction.html), fetched and
  read directly. For Guardrails AI: the GitHub README at
  `github.com/guardrails-ai/guardrails` (fetched and read directly) — the
  guardrailsai.com docs site itself returned repeated TLS errors this pass,
  so the primary claim here rests on the README, not the full docs site. For
  Llama Guard: secondhand only — Meta's model card
  (`github.com/meta-llama/PurpleLlama/.../MODEL_CARD.md`) was found via
  search but not independently fetched and read this pass; the summary below
  is reconstructed from consistent secondary coverage (the arXiv paper
  abstract, HuggingFace model page, and a technical blog), which is weaker
  than the other two entries and is flagged as such.
- **License:** NeMo Guardrails: Apache 2.0. Guardrails AI: Apache 2.0.
  Llama Guard: Meta's Llama community license (not a standard OSI license —
  usage restrictions apply above a user-count threshold), per its model
  card's well-known terms (secondhand, not independently re-verified here).
- **Resolving the task's explicit warning — these are not one thing wearing
  the same word:**
  - **Guardrails AI is fundamentally an output-content validator, confirmed
    directly from its own README.** A `Guard` wraps validators that check
    LLM input/output against a schema (frequently a Pydantic model);
    validators run before an LLM call (input) or after one (output), with
    `OnFailAction` (exception/reask/fix/filter) governing what happens on a
    failed check. Nothing in the README describes gating a tool/function
    call before it executes — it is squarely in the "checking what the model
    *says*" category, not "checking what it *does*."
  - **Llama Guard is also a content classifier, not an action gate** — it
    takes a prompt or a response as input and outputs a safety label plus
    violated-category names from a fixed taxonomy (14 MLCommons hazard
    categories, secondhand-confirmed). It does have one category
    specifically for tool-use context ("Code Interpreter Abuse," per the
    secondhand model-card summary), meaning it can be pointed *at* the text
    of a tool call's arguments the same way it's pointed at chat text — but
    it is still a text classifier scoring content for safety, not a
    mechanism that receives a structured tool call and returns
    ALLOW/DENY/ASK against a policy.
  - **NeMo Guardrails is the one genuine exception in this trio — it is
    both, by explicit design, confirmed directly from NVIDIA's own docs.**
    Alongside input/dialog/retrieval/output rails (all content-shaped, same
    category as Guardrails AI and Llama Guard), NeMo Guardrails has a
    distinct **execution rail** type that "validates tool inputs and outputs
    before and after invocation" — i.e., an actual action-gate concept
    sitting in the same framework as the content filters, not bolted on
    separately.
- **One concrete thing lawkeeper could adopt, or not:** none of the three is
  a fit for lawkeeper's actual problem (mechanically gating shell
  commands/file writes in a coding agent's loop) as well as Claude Code's own
  hook system already is (§ above) — all three are LLM-application-framework
  concepts (LangChain-adjacent, chatbot/RAG-shaped), not coding-agent-harness
  concepts, and none of them know what a git repo, a branch, or a commit is.
  The one transferable *idea*, specifically from NeMo Guardrails' rail
  taxonomy: **naming the gate type explicitly by what it inspects (content
  before generation / content after generation / action before execution /
  action after execution)** is a clean four-way split lawkeeper's own guard
  scripts don't currently name explicitly — Law 14 (audit-before-commit) is
  content-after-generation-shaped; a future `PreToolUse` hook (previous
  entry) would be action-before-execution-shaped. **Verdict: not-applicable
  as a dependency for any of the three; adopt NeMo Guardrails' naming
  taxonomy (content vs. action, before vs. after) as vocabulary only**, and
  keep the content-vs-action distinction sharp in any future lawkeeper design
  doc so a content filter never gets proposed to solve an action-gating
  problem or vice versa.

---

## 3. Standards-level agentic-AI-security frameworks

These are read for threat-model comparison, not implementation ideas — per
the assignment, this section checks lawkeeper's 18 laws against a published
taxonomy rather than looking for mechanisms to copy.

### OWASP — LLM Top 10 (2026) and the separate Top 10 for Agentic Applications (2026)

- **What was actually read:** OWASP's own Cheat Sheet Series page,
  "AI Agent Security Cheat Sheet"
  (cheatsheetseries.owasp.org/cheatsheets/AI_Agent_Security_Cheat_Sheet.html)
  — official OWASP wiki content, fetched and read directly, covering risk
  categories and specific tool-call mitigation guidance. The dedicated
  "OWASP Top 10 for Agentic Applications for 2026" resource page
  (genai.owasp.org) was fetched but returned only a landing blurb, not the
  actual ASI01–ASI10 list text (the full list requires a PDF download this
  tool couldn't retrieve) — so the specific ASI01–ASI10 names and
  descriptions below are **secondhand**, reconstructed from search-result
  aggregation of multiple third-party writeups (goteleport.com, cycode.com,
  neuraltrust.ai, among others) that agree closely enough to trust the
  category list, but this is explicitly not a primary read of OWASP's own
  document text for that specific list.
- **License:** CC-BY-SA (OWASP's standard content license) — not a software
  dependency; a document to check lawkeeper's threat model against.
- **The risk categories, and what lawkeeper's 18 laws don't cover at all:**
  the ten ASI categories (ASI01 Agent Goal Hijack, ASI02 Tool Misuse &
  Exploitation, ASI03 Identity & Privilege Abuse, plus — per secondhand
  aggregation — categories covering agentic supply-chain vulnerabilities,
  unexpected code execution, memory/context poisoning, insecure inter-agent
  communication, cascading failures, human-agent trust exploitation, and
  rogue agents) name several failure classes lawkeeper's constitution is
  silent on:
  - **Memory/context poisoning** (malicious content persisted somewhere the
    agent will read back later, e.g. a poisoned `CLAUDE.md`, a doctored
    `AGENTS.md`, a compromised memory-provider entry) — lawkeeper's laws
    protect the constitution file itself (Law 16's guard against
    unauthorized edits) but say nothing about `guardrail/memory/`'s provider
    abstraction being a poisoning target, and no law currently treats "an
    agent's own prior session output, read back uncritically" as an attack
    surface.
  - **Identity & privilege abuse across delegation** — Law 19 (delegation
    authority) governs *legitimate* delegation protocol between trusted
    agents on trusted machines; it has no adversarial framing at all (what if
    a delegation message itself is spoofed or the "coordinating agent" claim
    is forged) because lawkeeper's threat model to date has been "agent
    malfunctions," not "agent or channel is compromised by an outside actor."
  - **Insecure inter-agent communication** — Law 11's team channel (GitHub
    Discussion) has no authentication/integrity requirement stated anywhere
    in the constitution beyond "post there"; OWASP's framing would ask
    whether a forged or tampered channel message could be acted on as if
    genuine.
  - **Cascading failures across a multi-agent system** — lawkeeper's laws are
    entirely single-repo/single-decision-at-a-time; nothing addresses one
    guard's false-negative propagating into another agent's action on a
    different machine.
- **One concrete thing to do with this, or explicit non-fit:** this is a
  threat-model gap list, not a mechanism to build — the actionable finding is
  narrow and specific: **Law 11/19's team-channel protocol currently assumes
  benign-but-fallible actors, never an adversarial one**, which is a real,
  nameable gap this survey surfaced that the existing laws don't claim to
  cover. **Verdict: not a dependency or design pattern to adopt — a
  documented gap to log**, and it's logged here rather than glossed as
  "covered" by an existing law that doesn't actually address it.

### MITRE ATLAS

- **What was actually read:** nothing directly — every attempt to fetch
  atlas.mitre.org and its subpages (the front page, `/matrices/ATLAS`,
  `/matrices`, `/tactics`, and the official PDF fact sheet) returned either a
  bare page shell with no substantive content or an HTTP 404 this pass. This
  entry is **entirely secondhand**, reconstructed from search-result
  aggregation (which itself cites MITRE's own case-study/fact-sheet language
  second-hand) and should be weighted accordingly — this is the weakest-
  sourced entry in the whole survey and is flagged as such rather than
  presented with false confidence.
- **License:** N/A — a knowledge base/taxonomy, not software.
- **What it appears to be, per secondhand sources:** an ATT&CK-style
  matrix of adversary tactics against ML/AI systems specifically — tactics
  named (per aggregated search results) Reconnaissance, Resource Development,
  Initial Access, ML Model Access, Execution, Persistence, Defense Evasion,
  Discovery, Collection, ML Attack Staging, Exfiltration, and Impact, each
  with specific techniques underneath, built from real red-team/incident
  observations rather than theory.
- **Does it cover agentic tool-use attacks specifically?** Cannot be
  confirmed from what was actually read this pass. Secondhand sources
  describe ATLAS as originally scoped to classical ML attacks (evasion, model
  extraction, data poisoning against a trained model) with agentic-specific
  technique additions reportedly ongoing as the field moves, but this survey
  did not verify that claim against the actual matrix content and should not
  be relied on for that specific question.
- **One concrete thing to adopt, or not:** none — with no confirmed read of
  the actual technique list, there is nothing to responsibly recommend
  adopting from this entry. **Verdict: unresolved, re-queue for a dedicated
  future pass** with a different fetch strategy (the site appears to be a
  JS-rendered SPA that this pass's fetch tool couldn't render) — added to
  the landscape doc's candidate queue below rather than closed out here.

### NIST AI RMF's Generative AI Profile (AI 600-1)

- **What was actually read:** nothing of NIST's own document text directly —
  every finding here is secondhand, reconstructed from search-result
  aggregation of third-party summaries of AI 600-1 (published July 2024).
  This entry additionally surfaced a claim (from one secondary source,
  aisecurityandsafety.org) that "NIST AI 100-5" is a dedicated agentic-AI
  risk profile — **this claim is flagged as unverified and likely
  unreliable**: a separate, independent search turned up NIST's own
  publication record describing AI 100-5 as "A Plan for Global Engagement on
  AI Standards," a different document with no agentic-AI-specific content
  described anywhere else. The two claims about the same document number
  contradict each other, which is exactly the kind of thing Law 20 (never
  claim verified without a fresh check) exists to catch — so this survey
  explicitly does **not** assert that a NIST agentic-AI RMF profile exists
  under that or any other identifier; if lawkeeper needs to know whether one
  exists, that requires a dedicated check against nist.gov's own publication
  list, not this survey.
- **License:** N/A — a federal framework document.
- **What AI 600-1 covers, per consistent secondhand summary:** twelve GenAI-
  specific risk categories (CBRN information, confabulation, harmful/violent
  content, data privacy, environmental impact, harmful bias, human-AI
  configuration, information integrity, information security, intellectual
  property, obscene content, value-chain/component integration) — all
  **content-generation-shaped risks** (what the model produces), consistent
  with the task's own prediction. Multiple secondary sources independently
  make the same specific claim: AI 600-1 predates and does not address
  "delegation chains, multi-agent coordination, or runtime permission
  boundaries" — i.e., it was written for a standalone generative model, not
  a tool-calling agent, and does not speak to lawkeeper's actual problem
  space at all.
- **One concrete thing to adopt, or explicit non-fit:** **explicit
  non-fit, confirmed rather than assumed** — the task's own hedge ("it may
  mostly predate that agentic reality; say so if true rather than stretching
  a fit") is exactly the honest conclusion here. **Verdict: not applicable —
  AI 600-1 is a content-risk taxonomy for generative models, not an
  agentic-tool-use framework, and nothing in it should be cited as covering
  lawkeeper's actual problem.**

---

## 4. Supply-chain provenance — SLSA and in-toto

Relevant specifically to lawkeeper's Law 14 (`AUDIT:` markers) and Law 16's
"audit result declared in the commit" convention — both are today a
**self-asserted text marker** with no cryptographic or structural backing:
an agent writes `AUDIT: reviewed, tests pass` in a commit message, and
nothing checks that the audit actually happened the way the text claims.

### SLSA

- **What was actually read:** SLSA's own spec pages, fetched and read
  directly: `slsa.dev/spec/v1.0/about` (levels/tracks model) and
  `slsa.dev/provenance/v1` (the concrete provenance predicate schema).
- **License:** SLSA itself is a specification (CC-BY-4.0 per its own site,
  not independently re-verified this pass); reference implementations
  (`slsa-framework/slsa-github-generator` etc.) are Apache 2.0.
- **The concrete mechanism:** a SLSA provenance attestation is a specific
  in-toto `Statement` (see next entry) with `predicateType:
  "https://slsa.dev/provenance/v1"`. Its `predicate.buildDefinition` records
  exactly what went into the build (`buildType`, `externalParameters` —
  user-controlled inputs that MUST be checked, `resolvedDependencies` — every
  fetched artifact's URI and content digest); `predicate.runDetails` records
  who/what ran it (`builder.id`, a URI identifying "the transitive closure of
  the trusted build platform," plus timestamps). Verification is a concrete,
  four-step check a verifier actually performs: confirm the attestation's
  cryptographic signer matches the claimed `builder.id`; confirm
  `externalParameters` match what's expected (nothing snuck in); confirm
  `resolvedDependencies`' digests match current reality; confirm the
  artifact's own digest matches the attestation's `subject`. This is a
  genuinely different kind of claim than lawkeeper's `AUDIT:` marker — it's
  not "a human/agent asserts X happened," it's "a specific builder identity,
  cryptographically bound to specific inputs and a specific output digest,
  produced this."
- **One concrete thing lawkeeper could check its convention against:**
  lawkeeper's `AUDIT:` marker is currently unfalsifiable — the same failure
  class Law 20 exists to catch generally ("claiming verified without a fresh
  check") applies structurally to the marker itself: nothing stops an agent
  from writing `AUDIT: reviewed, tests pass` without having done either. A
  SLSA-style upgrade would mean the audit claim becomes a **subject-bound
  attestation** (a small JSON document, `subject` = the commit's tree hash,
  `predicate` = which laws were checked, what test run produced what
  pass/fail counts, and a timestamp) rather than free text inside a commit
  message — checkable mechanically (does a claimed test-run digest actually
  match a real, reproducible test invocation) instead of only textually
  (does the string `AUDIT:` appear). This is a real, scoped mechanism
  upgrade, not a vague "be more like SLSA" gesture.
- **Verdict: adopt-the-design of subject-bound, structured attestation for
  Law 14's audit marker** — not a dependency (lawkeeper doesn't need SLSA's
  build-platform-identity model, which solves a build-farm-trust problem
  lawkeeper doesn't have), but the *shape* of "a structured, artifact-bound
  claim a machine can check" directly upgrades what is currently a bare text
  string.

### in-toto

- **What was actually read:** in-toto's own "what is in-toto" overview page
  (in-toto.io/docs/what-is-in-toto/, fetched directly, high-level only) and
  the in-toto Attestation Framework's spec README on GitHub
  (`github.com/in-toto/attestation/blob/main/spec/README.md`, fetched and
  read directly, covering the concrete Statement/Predicate/Envelope layering
  SLSA's own provenance format is built on).
- **License:** Apache 2.0.
- **The concrete mechanism, more general than SLSA's specific use of it:**
  in-toto's Attestation Framework is the general format SLSA provenance is
  one instance of — an **Envelope** (handles signing/serialization,
  typically DSSE), wrapping a **Statement** (binds a `predicateType` and a
  `subject` — the artifact digest(s) being described — together), wrapping
  an arbitrary **Predicate** (the actual claim, schema depends on
  `predicateType` — SLSA provenance is one predicate type; a test-report
  predicate, a code-review predicate, or a vulnerability-scan predicate are
  other real, already-defined predicate types in the wider ecosystem). The
  separation matters: **the attestation format is generic; the claim inside
  it is pluggable**. A policy engine (in-toto's own docs name
  `in-toto-verify` and Google's `Binary Authorization` as examples) checks
  whether the *set* of attestations attached to an artifact satisfies a
  **layout** (a supply-chain definition of which steps, by which authorized
  actors, in what order, must have produced attestations before the final
  artifact is trusted) — this layout-plus-attestation-set model is
  functionally a policy language over a chain of provenance claims, not just
  a single audit marker.
- **One concrete thing lawkeeper could adopt-toward:** the **predicate-type
  pluggability** is the most directly transferable idea — lawkeeper's own
  Law 14 audit and Law 18 test-governance ("theory cards," trust levels T0–T5)
  are *already*, structurally, two different kinds of claims about the same
  commit that currently live in unrelated places (a commit-message string vs.
  a theory-card file). Modeling both as **in-toto-shaped predicates keyed to
  the same commit-tree-digest subject** (an `AuditPredicate` and a
  `TestGovernancePredicate`, say) would give lawkeeper one consistent,
  inspectable attestation format for every "this was checked" claim it
  already makes in different ad hoc ways, and a natural place to add new
  predicate types later (a `MergeGatePredicate` for `merge_gate.py`'s output,
  for instance) without inventing a new bespoke marker convention each time.
- **Verdict: adopt-the-design of the Statement/Predicate separation as the
  target shape for a future structured-attestation upgrade to Laws 14/18** —
  not a dependency to install (`in-toto`'s own Python reference
  implementation is heavier tooling — key management, layout signing —
  than a single-repo tool needs today), but the concrete data-shape
  (subject digest + typed predicate + who/when) is the right target to design
  toward before inventing a bespoke JSON shape from nothing.

---

## 5. MCP's elicitation primitive, in full

- **What was actually read:** the actual MCP specification source files,
  fetched via a CDN mirror of the spec repository after `modelcontextprotocol.io`
  and GitHub's raw-content host both returned repeated TLS/certificate errors
  in this environment this pass (`cdn.jsdelivr.net/gh/modelcontextprotocol/
  modelcontextprotocol@main/docs/specification/2025-06-18/client/
  elicitation.mdx` and the sibling `sampling.mdx` in the same path) — this is
  the actual spec source text, not a paraphrase site, just fetched through a
  mirror rather than the canonical domain; flagged here so the access method
  is transparent.
- **License:** the MCP spec itself is open (MIT, per the
  `modelcontextprotocol/modelcontextprotocol` repo's well-known licensing —
  not independently re-verified by reading its LICENSE file this pass).
- **The elicitation primitive, confirmed from spec text:** a server sends
  `elicitation/create` with a `message` and a `requestedSchema` — deliberately
  restricted to a **flat object of primitives only** (string, number/integer,
  boolean, enum), explicitly **no nested objects or arrays**, a constraint
  the spec states is deliberate (so any client can build one generic form
  renderer once, rather than needing to support arbitrary JSON Schema). The
  client's response carries an `action` field with exactly three values —
  **`accept`** (content provided, validated against the schema),
  **`decline`** (the user considered the request and refused — a real,
  meaningful signal distinct from...), **`cancel`** (the user dismissed
  without forming an opinion — closed the dialog, pressed Escape, was
  interrupted). The spec states outright, as a MUST: **"Servers MUST NOT use
  elicitation to request sensitive information"** — it is explicitly scoped
  to operational parameters and configuration choices, not
  credentials/secrets, and clients are told to make clear which server is
  asking and to rate-limit requests.
- **Confirms Omnigent's own borrowing, already logged in the landscape
  doc:** Omnigent's `approval.py` three-way outcome split (approve / explicit
  decline that aborts the turn / everything-else-fails-closed-to-deny) maps
  extremely closely onto elicitation's own accept/decline/cancel — this
  survey's direct read of the spec text confirms the landscape doc's claim
  that this was modeled "verbatim" on elicitation, down to treating an
  explicit decline as meaningfully different from a timeout/cancel/failure,
  not collapsing all three into one "not approved" bucket.
  ​
- **Other MCP-native human-approval/consent machinery beyond elicitation, per
  spec text actually read this pass:** **sampling** (`sampling/createMessage`)
  has its own, separate human-in-the-loop requirement, mechanically different
  from elicitation rather than a variant of it. Where elicitation is "server
  asks the human a small structured question," sampling is "server asks the
  client to run an LLM completion on its behalf," and the spec places
  **two** distinct human checkpoints around that: the client SHOULD let a
  human review/edit/approve the *outgoing prompt* before it reaches the model,
  and SHOULD let a human review/edit/approve the *model's response* before it
  goes back to the requesting server. The spec's own language here is
  softer than elicitation's — "SHOULD" throughout, not the hard "MUST NOT"
  found in elicitation's sensitive-data prohibition — meaning sampling's
  human-in-the-loop behavior is a strong recommendation an implementation can
  legitimately skip, whereas elicitation's data-sensitivity constraint is not
  optional.
- **One concrete thing lawkeeper could adopt, or not:** if lawkeeper's
  `AUDIT:`-marker-missing "pause and ask a human" case (already flagged in
  the landscape doc as a natural ASK-tier case) is ever surfaced through an
  MCP-aware surface (an MCP client, a bot, anything other than a raw blocking
  CLI prompt), the **decline vs. cancel distinction** is the concrete,
  reusable piece: a human explicitly saying "no, don't commit this" should
  behave differently (abort the operation outright, matching Omnigent's
  `ElicitationDeclinedError` behavior) than a prompt that simply timed out or
  got dismissed unanswered (which should fail closed to DENY-for-this-attempt
  but not necessarily abort the whole session). Lawkeeper's guard scripts
  today have no such distinction — a missing/unanswered `AUDIT:` marker and
  an operator explicitly saying "I decline to add one" are currently handled
  identically (both just block the commit). **Verdict: adopt-the-distinction
  (decline vs. cancel/timeout are different outcomes, not one) into any
  future ASK-tier mechanism** — cheap to add to a design doc now, before a
  concrete ASK-tier mechanism exists to retrofit later.

---

## If lawkeeper does ONE thing next

Everything above supports one recommendation, not a menu:

**Write a `PreToolUse` hook in lawkeeper's own `.claude/` config that runs
lawkeeper's existing destructive-command/branch-guard checks (the logic
already in `scripts/guard_branch.py` and friends) as a live ALLOW/DENY/ASK
gate on `Bash` tool calls, before they execute — not a new policy engine, not
a port to Rego, not an Omnigent-style harness-agnostic adapter layer.**

This is the one finding in this survey that is simultaneously (a) the
biggest capability gap the landscape doc identified (no in-loop enforcement
at all today), (b) already fully supported by the exact product lawkeeper's
own README says it targets (Claude Code — confirmed by direct reading of its
current hooks and permissions docs, not inferred), (c) buildable with zero
new dependencies and no new DSL, by re-using logic lawkeeper already has, and
(d) uses a precedence model (deny > ask > allow) that this survey found
independently confirmed by Omnigent's own runtime engine, meaning lawkeeper
doesn't have to invent or justify a new algebra — it can point at Claude
Code's own documented behavior as the reference. Every other finding in this
survey (Rego's lack of a standard algebra, Cedar's formal-verification
story, SLSA/in-toto's structured-attestation shape, MCP's decline/cancel
split) is a real, worth-logging idea for later — but none of them closes the
actual gap the way a `PreToolUse` hook does, today, in an afternoon, with
tools lawkeeper's target already ships.
