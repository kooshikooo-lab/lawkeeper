# External scan — 2026-11-19

Weekly scheduled research pass. Scope per the routine's own brief: runtime/
`PreToolUse`-style agent governance, policy-decision algebras (allow/deny/ask),
git-hook distribution/enforcement patterns, and test-governance/oracle-
independence methodology. Not Windwright's domain (acoustics/CAD) and not
Falcun's (evolutionary mutation, epistemic-claim verification) — a harness's
other features are out of scope here even when its governance mechanism is
in scope.

**Gap note, not investigated, flagged only so a future pass doesn't need to
re-discover it:** the last scan on record is
`docs/RESEARCH_EXTERNAL_SCAN_2026-11-05.md`. There is no
`RESEARCH_EXTERNAL_SCAN_2026-11-12.md` in this repo's history — a two-week
gap in the weekly cadence. Not investigated this pass, since the task is to
run this week's scan, not audit why the prior one may not have fired.

**Access note, carried forward from 2026-11-05, unchanged this pass:** this
session's egress proxy allows `github.com`, `raw.githubusercontent.com` and
the `api.github.com` search endpoints (`search/code`, `search/repositories`),
plus the two repos this account has GitHub API access to (`lawkeeper`,
`falcun` — `api.github.com/repos/...` against any other repo is refused with
"GitHub access to this repository is not enabled for this session," so every
other repo this pass was read via `raw.githubusercontent.com` directly, which
is not gated the same way). Every non-GitHub host attempted failed as an
explicit proxy-level policy denial (`CONNECT tunnel failed, response 403`),
confirmed directly against the proxy's own status endpoint. Confirmed blocked
this pass: `open-plugins.com`, `arxiv.org`, `export.arxiv.org`,
`blog.trailofbits.com`, `docs.snowflake.com`, `agent-plugins.org`,
`trace.agentrust-io.com`/`agentrust-io.com` (the TRACE spec's own
documentation site — its GitHub-hosted source repo was reachable and read
directly instead, §4 below). No workaround beyond a direct retry was
attempted for any of these, same discipline as every prior scan.

---

## 1. The Open Plugins hooks specification — re-attempted as instructed, still blocked, sixth consecutive pass

- **Prior status:** blocked on 2026-09-06 (queued), 2026-10-01
  (`EGRESS_BLOCKED`), 2026-10-15 (`getaddrinfo ENOTFOUND`), 2026-10-29
  and 2026-11-05 (`CONNECT tunnel failed, response 403`).
- **What was attempted this pass:** a direct fetch of
  `open-plugins.com/agent-builders/components/hooks` and of the bare domain
  `open-plugins.com/`, both via plain `curl`. Both failed identically:
  `curl: (56) CONNECT tunnel failed, response 403`, confirmed against this
  session's own proxy status endpoint as `connect_rejected` — the same
  policy-level denial every prior pass from 2026-10-01 onward has hit, not a
  new or different failure mode.
- **No workaround attempted.** 2026-11-05 already tried, and had refused, a
  Wayback Machine mirror fetch as a containment-escape risk; this pass does
  not repeat that or try any other indirect path, per that same refusal's own
  reasoning.
- **Verdict: unchanged — stays queued, still unreachable.** Stated plainly
  rather than padded: this pass adds no new information about Open Plugins
  itself. Re-attempt directly whenever a future session's egress policy
  might differ; do not substitute Agent Plugins (confirmed by 2026-11-05 to
  be a different, separate spec) and do not route around the block via a
  mirror.

---

## 2. Codex's `PermissionRequest` fold, when no hook decides — the 2026-11-05 follow-up, resolved from source

2026-11-05 §1 left this open: its own module-docstring citation
(`permission_request.rs`, "a handler can return a concrete allow/deny
decision, or decline to decide and let the normal approval flow continue")
named a fallback path (`core/src/tools/approvals.rs`) it had not read, and
flagged "whether 'normal' defaults to prompting a human, a configured
auto-approve, or something else is unverified" as a named follow-up. Read
directly this pass.

- **What was actually read, all via `raw.githubusercontent.com` against
  `openai/codex`'s `main` branch, 2026-11-19:**
  - `codex-rs/core/src/tools/approvals.rs` (full, 1001 lines, including its
    own module doc and test-module declaration)
  - `codex-rs/core/src/hook_runtime.rs`'s `run_permission_request_hooks`
    (lines 275–313)
  - `codex-rs/core/src/guardian/mod.rs` (module doc and top-level `mod`/
    `pub(crate) use` exports, first ~40 lines; the review/scoring/routing
    submodules themselves were not read beyond their names)
  - `codex-rs/hooks/src/events/permission_request.rs`, line 6 only — the
    same doc-comment line 2026-11-05 already quoted, re-confirmed verbatim
    at the exact line number this pass.
  - Confirmed directly: `LICENSE` is Apache 2.0 (unchanged from 2026-11-05).
- **License:** Apache 2.0 — read for design/precedent, not as a dependency
  candidate, same basis as every other harness in this research base.
- **What actually happens, confirmed from source, not inferred:**
  `approvals.rs`'s `request_approval_with_user_prompt` runs
  `run_permission_request_hooks` and matches its `Option<PermissionRequestDecision>`
  result with the comment, quoted directly:
  > "Hook denials always win. Managed checkpoints require a person even when
  > a hook allows the action or the session uses automatic review."

  The match itself (lines 602–627):
  - `Some(Deny { message })` → the action is denied, full stop — a hook deny
    always wins, matching every other system in this research base.
  - `Some(Allow) if !ctx.requires_human_approval()` → approved directly from
    the hook, no further stage.
  - **`Some(Allow)` when human approval *is* required, or `None` (no hook
    decided at all) — both fall into the same branch:**
    `self.request_reviewer_approval(action, ctx, user_prompt).await`.
  - `request_reviewer_approval` (lines 687–705) is itself two-staged: if the
    context requires human approval, it goes straight to the human prompt;
    otherwise it first tries `request_guardian_approval` — and only falls
    through to the human prompt if Guardian returns nothing.
- **"Guardian" is a previously-undocumented stage in this research base's
  account of Codex — an in-process, LLM-based automated reviewer, not a
  second hook or a config default.** `guardian/mod.rs`'s own module doc,
  quoted directly:
  > "Hosts approval decisions and the isolated synchronous reviewer. The
  > extension chooses policy and evidence; core enforces permissions and
  > mandatory review requirements."

  Its submodule names (`reviewer_config::guardian_policy_model`,
  `resolve_review_model`, `score_authorization`, `prepare_guardian_prompt`)
  confirm this is a model-based reviewer wired directly into the approval
  decision path, not a human-approval default or a second external hook.
  None of this module's internals were read this pass beyond its exports —
  flagged as a real gap, not silently treated as covered.
- **The answer to 2026-11-05's own open question, stated precisely:** a
  `PermissionRequest` fold that resolves to `None` does **not** default to
  either a bare allow or a bare deny. It is routed to the same place a
  hook-allow-that-still-needs-human-approval is routed: Guardian first (an
  automated reviewer), then a human prompt if Guardian doesn't resolve it.
  "The normal approval flow continues" (2026-11-05's quoted phrase) means
  specifically this three-stage pipeline, not an undocumented fallback.
- **This changes the shape of a comparison this research base has made
  before, not just adds detail to it.** Every other harness read in the
  hook-mechanisms survey and the governance survey (Claude Code, Omnigent,
  dsh, Hermes, goose) implements a **two-stage** pipeline at most: an
  external hook (sometimes ask-capable, sometimes binary) and a human. Codex
  has a **three-stage** pipeline: external hook → automated model-based
  reviewer → human. None of this research base's prior convergence claims
  ("N independent systems confirm deny>ask>allow") are about this specific
  structural question, so nothing is retracted — but a future comparison
  that treats "hook, then human" as the universal shape would now be wrong
  about Codex specifically, and should cite this entry rather than assume.
- **Verdict: adopt-the-finding, not a dependency.** The concrete, reusable
  takeaway for any future lawkeeper `EXECUTOR_CONTRACT.md` Codex adapter: a
  hook that returns nothing, or an allow that doesn't clear a mandatory-
  human-approval bar, does not mean "ask Claude-Code-style" — it means "an
  automated reviewer gets a turn first, and may itself approve the action
  before a human ever sees it." An adapter that assumes Codex's fallback
  path is equivalent to Claude Code's own hook-to-human handoff would be
  wrong about a real, sourced difference.

---

## 3. goose's hook/permission source — re-verified against current `main` (v1.60.0), closing the 2026-11-05 follow-up

2026-11-05 §2 corrected goose's *docs* against a live read but explicitly
left the hook-mechanisms survey's *source*-level claims (file paths, line
numbers, exact Rust logic — keyed to a ~10-week-stale 1.39.0 backup at the
time of the original 2026-09-06 survey) unverified, and queued a fresh-clone
re-read as a named follow-up. Done this pass.

- **What was actually read, all via `raw.githubusercontent.com` against
  `block/goose`'s `main` branch, 2026-11-19:**
  `crates/goose/src/hooks/mod.rs` (2227 lines — fetched in full; grepped for
  the specific enum/failure-policy declarations rather than read
  line-by-line start to end), `crates/goose/src/tool_inspection.rs` (313
  lines, read in full), and the root `Cargo.toml` (for the workspace
  version only).
- **License:** Apache 2.0 (unchanged; not re-verified this specific pass,
  carried over from the 2026-09-06 entry).
- **Version, confirmed directly:** `version = "1.60.0"` in the workspace
  `Cargo.toml` — up from the 1.39.0 backup the original survey read, and
  past the 1.49.0 that was live when 2026-11-05 did its docs-only
  correction. `crates/goose/src/hooks/mod.rs` has grown to 2227 lines (the
  original backup's version was not measured in lines, so growth is not
  quantifiable, only directional).
- **The two source-level claims the hook-mechanisms survey staked on exact
  line numbers, both confirmed unchanged at v1.60.0:**
  1. `HookDecision` is still exactly binary, same two variants, now at
     `hooks/mod.rs:350–353`:
     ```rust
     pub enum HookDecision {
         Allow,
         Deny { reason: String, plugin: String },
     }
     ```
  2. `tool_inspection.rs`'s `apply_inspection_results_to_permissions` — the
     function itself still at line 170, its `Allow` branch's "don't override"
     comment still at line 254, worded identically to the original survey's
     quote:
     > "This inspector allows it, but don't override other inspectors'
     > decisions — if it's already denied or needs approval, leave it that
     > way."
- **Verdict: this follow-up is closed.** The hook-mechanisms survey's
  source-level claims about goose (the binary external-hook enum, the
  deny-beats-ask-beats-allow merge logic in the in-process inspector
  pipeline) hold up unchanged at current `main`, three minor-version jumps
  past the original stale backup. No correction needed to the existing
  entries; this is confirmation, not new behavior. (The *docs*-level
  changes 2026-11-05 already found — per-rule `on_failure`, the
  `PreToolUseResult` event, `Stop`-hook block cap — were not re-checked
  against source again this pass; they were already confirmed from goose's
  own current docs text last week and nothing here contradicts them.)

---

## 4. New candidate: Writ (`infinri/Writ`) — a Claude Code `PreToolUse`-hook governance product, read directly

Surfaced via a GitHub repository search for `topic:agent-governance`
(`search/repositories`, sorted by recency) — the single most directly
on-point result returned: a repo explicitly describing itself as a
"Governance runtime for Claude Code. Enforces workflow gates at tool time,"
last pushed the day before this scan (2026-11-18).

- **What was actually read:** `README.md` (303 lines, fetched and read in
  full via `raw.githubusercontent.com`), `LICENSE` (full), and
  `writ/session/gates.py` (1210 lines — not read start to end, but every
  line matching the decision/output vocabulary grepped and the two
  resulting output functions, `cmd_can_write` and `cmd_can_read_code`, read
  in full in context) and `writ/config.py` (checked for the one
  `WRIT_STRICT` reference, line 390, in context).
- **License:** MIT, confirmed by reading `LICENSE` directly — genuinely
  usable as a dependency or vendored source if lawkeeper ever wanted to
  (Python, same language as lawkeeper's own guard scripts), though nothing
  below recommends that.
- **What it actually is, per its own README, not a marketing gloss:** a
  local daemon plus Claude Code hooks plus a Neo4j database, aimed
  specifically at making selected workflow requirements ("don't write source
  before an approved plan," "don't write credential paths") *enforced*
  rather than merely written into `CLAUDE.md` and hoped-for. The README's own
  framing of the problem — "A rule in `CLAUDE.md`, a skill or a system
  prompt is an instruction: the model has to find it, keep it through a long
  session, and decide it applies... Writ moves selected requirements out of
  the prompt and into code that runs when the agent acts" — is, functionally,
  the same instructions-vs-enforcement distinction lawkeeper's own
  `AGENTS.md`/`AI_CONSTITUTION.md` split already rests on, independently
  arrived at by a different, unrelated project targeting the same host
  (Claude Code).
- **A four-way outcome taxonomy for what a tool-call check can do to a
  call, stated explicitly in its own docs, not reconstructed:**

  | Kind | What happens |
  |---|---|
  | Blocking check | The tool call is refused |
  | Approval request | Claude Code asks the human to confirm |
  | Advisory finding | Reported; nothing is refused |
  | Context delivery | Text is added to the model's context |

  This is a genuinely different cut than the deny/ask/allow algebra this
  research base has tracked since the first survey — it separates "refuses
  outright" from "defers to Claude Code's own ask," and adds a fourth kind
  (context injection) with no gating character at all. Worth comparing to,
  not folding into, the deny>ask>allow tally: Writ's "approval request" row
  is not a ternary value *its own* hook returns (next finding) — it is Writ
  declining to refuse and instead relying on Claude Code's own built-in
  confirmation UI for specific cases (e.g. "a shell write whose target
  cannot be resolved").
- **Confirmed directly from source: the hook's own stdout wire protocol is
  binary allow/deny only — a sixth real-world instance of the
  hook-mechanisms survey's "the ask tier doesn't always live at the wire
  layer" finding.** `writ/session/gates.py`'s own docstring, quoted
  directly, and matched by the actual code three lines later:
  > "Output: JSON {"decision": "allow"} or {"decision": "deny", "reason":
  > "..."}"

  ```python
  if result["can_write"]:
      json.dump({"decision": "allow"}, sys.stdout)
  else:
      json.dump({"decision": "deny", "reason": result["reason"]}, sys.stdout)
  ```
  The identical shape repeats in the adjacent `cmd_can_read_code`. So Writ's
  conceptual four-way table (which includes "ask") and its actual wire
  protocol (which doesn't) are two different layers, exactly the same split
  already found in goose (in-process three-tier inspector vs. binary
  external-hook enum) and Hermes (built-in three-tier classifier vs. binary
  `shell_hooks.py` wire protocol) — now a fourth confirmed instance of a
  project's *conceptual* model being richer than what its hook *wire format*
  actually carries.
- **A second, independently-arrived-at confirmation of lawkeeper's own
  fail-direction design question:** the README states plainly, "If the
  daemon does not answer, the write hooks run the same check locally from
  the session file. Only when no verdict can be obtained at all does a write
  proceed; `WRIT_STRICT=1` refuses it instead." Fail-open-by-default, with
  an explicit opt-in to fail-closed via an environment variable — the same
  shape as goose's per-rule `on_failure` (2026-11-05 §2) and a close cousin
  of lawkeeper's own `gate_pretooluse.py` two-tier fail design
  (2026-11-05 §4: fail open on unparseable input, fail to ask on a judgment
  failure after successfully parsing). Writ's own design does not add a
  third tier the way lawkeeper's does — it is a plain binary
  fail-open/fail-closed toggle — but it's a fourth independent data point
  for "every system with production mileage on this problem ends up with an
  explicit, named fail-direction choice, not an accidental default."
- **A limitation the README states about itself, worth citing precisely
  rather than glossing over:** "Writ constrains a cooperative agent; it is
  not a sandbox," and separately, "Shell inspection is pattern-based...not a
  sandbox. It misses paths built from variables, `eval`, `sh -c` bodies and
  `python -m MODULE`." Relevant if Writ is ever cited as a governance
  precedent elsewhere in this research base's design docs: its own authors
  do not claim adversarial robustness, only cooperative-agent discipline —
  the same honest limitation Hermes' and goose's hardline-pattern
  classifiers (2026-09-06 survey) also stated about themselves.
- **Verdict: adopt-the-design (the four-way outcome taxonomy, and the
  explicit fail-direction toggle), not a dependency.** Nothing here argues
  for depending on or vendoring Writ — it is a full product (a daemon, a
  Neo4j database, a CLI) for a much broader problem (context delivery,
  decision memory, retrieval) than lawkeeper's narrower governance-layer
  scope. The two cheap, concrete things worth citing in a future lawkeeper
  design doc: naming "refuse outright" vs. "defer to the host's own ask UI"
  vs. "report without refusing" vs. "inject context" as four distinct kinds
  of tool-call outcome, the way Writ's README does explicitly; and treating
  an explicit, named, opt-in fail-closed override (its `WRIT_STRICT`, this
  research base's running collection of goose's `on_failure` and
  lawkeeper's own two-tier design) as a now-four-times-confirmed pattern
  worth keeping, not something to simplify away.

---

## 5. New candidate: the TRACE Specification (`agentrust-io/trace-spec`) — read from its own upstream repo, not cited secondhand

Surfaced indirectly: a GitHub repository search for `topic:agent-governance`
also returned `sipyourdrink-ltd/bernstein` ("Open-source AI agent
governance... produces the verifiable, replayable record," Apache-2.0,
pushed 2026-11-18), itself closer to Omnigent (already logged in
`docs/RESEARCH_agent_harness_landscape.md`) than to a `PreToolUse`-style
gate — a multi-agent task scheduler with signed run receipts, not primarily
a tool-call gate. Reading Bernstein's own ADR about its receipt format's
conformance claims (`docs/decisions/016-trace-conformance-level.md`) named a
third-party spec it vendors rather than invents: **TRACE**
(`agentrust-io/trace-spec`). Per this research base's own standing
discipline (an internal/secondhand account must be traced to its actual
primary source before being relied on — the same rule this routine's brief
states for Falcun's relayed reports), this pass did not stop at Bernstein's
account of TRACE; it fetched and read TRACE's own upstream repository
directly.

- **What was actually read, all via `raw.githubusercontent.com` against
  `agentrust-io/trace-spec`'s `main` branch, 2026-11-19:** `README.md` (127
  lines, full) and `docs/trust-levels.md` (72 lines, full) — both the
  spec project's own documentation, not a secondary summary. `LICENSE`
  confirmed directly. Not read: the actual JSON Schema
  (`schema/trace-claim.json`), the full spec text
  (`spec/trace-v0.2.md`), the conformance test suite, or the
  `agentrust-trace` Python library's source — flagged as real gaps, not
  silently treated as covered; this entry is a documentation-level read,
  sufficient to characterize what TRACE is and verify Bernstein's account
  of it, not a full technical audit of the schema or library.
- **License — two different licenses for two different things, confirmed
  directly, worth stating precisely:** the specification text itself is
  under the **Community Specification License 1.0** (an LF-governed
  specification license, not a software license); the reference code (the
  `agentrust-trace` Python library, the `cmcp` reference implementation) is
  **Apache 2.0**. The first AGPL-adjacent-but-actually-not-AGPL distinction
  this research base has had to draw between a spec's own license and its
  reference code's license — worth getting right rather than reporting one
  license for the whole repo.
- **What TRACE actually is, confirmed from its own README, not Bernstein's
  gloss of it:** "TRACE is an open format for a signed receipt of an AI
  agent run: what ran, where, under which rules, on what kind of data, and
  which tools it called. Anyone holding the receipt (a Trust Record) can
  check it on their own computer, without asking the operator." It builds
  on real, named IETF/IRTF standards — RFC 9711 (CBOR Web Token / EAT) for
  the claim envelope, RFC 9334 (RATS) for the attester/verifier/relying-party
  roles, and the SCITT draft for transparency-log anchoring — rather than
  inventing its own envelope format from scratch.
- **Standards-body weight, confirmed from the README's own text, not
  inferred from the name:** "TRACE Specification is an LF Project, hosted
  at the Linux Foundation as its own series... developed with AMD, Intel,
  Microsoft, OPAQUE and TII." This is a materially different kind of
  provenance than most entries in this research base — not one vendor's
  internal design choice (Omnigent, dsh, Hermes, goose) and not one
  harness's own docs (Claude Code, Codex), but a named, multi-vendor,
  foundation-hosted specification, the same category of thing SLSA and
  in-toto already occupy in the governance survey's §4.
- **TRACE's own three-level evidence ladder, quoted directly from
  `docs/trust-levels.md`, and precisely how it does and doesn't relate to
  lawkeeper's own trust levels:**
  > "Level 0, software: the record is signed with a key held in ordinary
  > software. Level 1, hardware evidence: the record also carries a signed
  > report from the processor showing where it ran. Level 2, transparency:
  > the record is also published to an append-only log that others can
  > audit."

  This is a genuinely different axis from lawkeeper's own Law 18 T0–T5
  test-governance trust levels, and the two should not be conflated just
  because both are named "trust levels" — TRACE's levels grade the strength
  of evidence behind a claim about *where and how an agent run happened*
  (software signature vs. hardware attestation vs. public transparency log);
  lawkeeper's T0–T5 grade *oracle independence of a test* (whether a test's
  pass/fail signal could have been written by the same process it's
  checking). Different question, same "name a ladder of evidence strength
  explicitly rather than leaving it binary" instinct — worth citing as a
  second real precedent for that instinct (SLSA's levels, already logged in
  the governance survey, being the first), not as validation of lawkeeper's
  specific ladder.
- **The direct, concrete connection to this research base's existing,
  not-yet-acted-on recommendation:** the governance survey's §4 (SLSA/
  in-toto) already recommended, as design target, upgrading lawkeeper's
  Law 14 `AUDIT:` marker and Law 18's theory-card files from free text into
  "a structured, artifact-bound claim a machine can check" — specifically a
  subject-bound Statement/Predicate pair keyed to a commit-tree digest.
  TRACE is a real, shipped, multi-vendor instance of exactly that upgrade
  path, applied to a different subject (an agent *run*, not a git commit) —
  "what model ran, under which policy, what data class it touched, which
  tools it called," each a named field in a signed record a third party can
  check without trusting the operator. It does not replace the SLSA/in-toto
  recommendation (different subject: a run's provenance, not a build's) but
  is a second, independently-arrived-at confirmation that "signed, schema'd,
  subject-bound record over free text" is where this whole adjacent field
  is converging, not a single committee's idiosyncratic design choice.
- **Explicit, stated limitation, not glossed over:** "Developer Preview,"
  spec v0.2, and the README's own FAQ states "a proposal to bring it into
  the Agentic AI Foundation as a Sandbox project is in progress" — this is
  an early-stage, not-yet-stabilized spec, not an established standard like
  SLSA. Cite it as "a real, well-sponsored, in-progress effort worth
  tracking," not as settled prior art to build against today.
- **Verdict: adopt-the-design (the signed, schema'd, multi-field attestation
  shape, and the explicit software/hardware/transparency evidence-level
  split), not yet a dependency.** The `agentrust-trace` Python library is
  genuinely installable (`pip install agentrust-trace`) and Apache-2.0, so
  "worth-a-dependency" is a live option in a way most of this research
  base's entries aren't — but the spec is a Developer Preview with no
  lawkeeper-shaped integration point designed yet (lawkeeper has no "agent
  run," in TRACE's sense, to attest to — its own enforcement is git-hook-
  and tool-call-boundary-shaped, not a discrete run with a start and an
  end). Revisit if lawkeeper's own Law 14/18 attestation-upgrade work
  (queued, not yet started, per the governance survey) gets underway for
  real — TRACE's schema is the concrete thing to check that work against
  before inventing a bespoke JSON shape, same discipline the governance
  survey already recommended for in-toto.

---

## What this pass found nothing new on

Per the task brief's own instruction: stated plainly rather than padded.

- **Test-governance/oracle-independence methodology:** no new primary-source
  progress. The two arXiv papers 2026-11-05 named (arXiv 2606.18168, "All
  Smoke, No Alarm: Oracle Signals in Agent-Authored Test Code"; arXiv
  2603.02601, AgentAssay) remain unread — `arxiv.org`/`export.arxiv.org`
  are still blocked, confirmed again this pass by direct attempt, not
  assumed from last week's status. A targeted `search/code` /
  `search/repositories` pass this week specifically for oracle-independence
  or mutation-testing tooling (beyond mewt, already closed out as
  not-applicable by 2026-11-05) surfaced nothing new and checkable — mostly
  generic "AI testing" marketing repos with no real oracle-independence
  mechanism described in their own READMEs.
- **A new, independently-built policy-decision-algebra system:** none
  surfaced this pass beyond the two re-checks above (Codex §2, goose §3),
  neither of which is a *new* system for the convergence tally — both are
  deeper/fresher reads of systems already counted. Searches this pass for
  recently-updated `topic:agent-governance` repositories turned up several
  more candidates (`sipyourdrink-ltd/bernstein`, folded into §5 above as the
  TRACE-spec route rather than a standalone entry; `faramesh-core`,
  `halofyai/halofy`, `KeyArgo/custodian-kernel`, `HelpCode-ai/anythingmcp`)
  whose own descriptions read as governance/audit platforms but were not
  read this pass — not reported as findings, named here only as a
  re-findable queue for a future pass, per this research base's own rule
  against citing an unread README as a verified result.
- `blog.trailofbits.com` and `docs.snowflake.com` — both still blocked,
  confirmed again by direct attempt this pass. No substitute GitHub-mirror
  path was found for either this week (unlike Codex/goose, which have their
  actual engines on GitHub; Snowflake's Cortex Code Agent SDK approval
  callback does not appear to have an open-source mirror this pass could
  locate).
- No Falcun-relayed report was encountered or relied on this pass; nothing
  here traces through a secondary research report from another repo.

## Re-check when

- `open-plugins.com` — sixth-pass-running block; re-attempt directly
  whenever a future session's egress policy might differ. Do not
  substitute Agent Plugins and do not route around the block via a mirror.
- `arxiv.org`/`export.arxiv.org` — still blocked, now three passes running
  (first blocked 2026-11-05). Two concrete, named papers are waiting:
  arXiv 2606.18168 and arXiv 2603.02601.
- `blog.trailofbits.com` and `docs.snowflake.com` — re-attempt directly if a
  future session's policy allows it.
- The candidates named above but not read this pass
  (`faramesh-core`, `halofyai/halofy`, `KeyArgo/custodian-kernel`,
  `HelpCode-ai/anythingmcp`) — a real, named queue, not yet checked against
  their own source. Read before citing any of them as relevant or not.
- TRACE's own schema (`schema/trace-claim.json`) and full spec text
  (`spec/trace-v0.2.md`) — this pass read the documentation layer
  (README, trust-levels doc) but not the schema or spec body itself. Read
  directly before citing specific field names or requirements beyond the
  six summarized in §5 above.
- Codex's `guardian` module internals (`review.rs`, `routing.rs`,
  `score_authorization.rs` and friends) — this pass read only `mod.rs`'s
  top-level doc and exports, confirming Guardian's existence and role in
  the approval fold, not how it actually decides. Read directly before
  citing anything about *how* Guardian scores or routes a request.
