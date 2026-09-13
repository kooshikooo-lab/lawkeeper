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

### Deeper pass, 2026-09-05 — the actual engine, the ASK flow, CEL

Read in full this pass: `omnigent/runtime/policies/engine.py`'s
`_evaluate_composed` (the real gate-dispatch-compose loop), `approval.py`
(the ASK round-trip), and `policies/builtins/cel.py`. All three follow-ups
from the first pass are now resolved:

1. **Precedence is DENY > ASK > ALLOW, and the loop does not stop on ASK.**
   The non-obvious detail: an ASK does **not** short-circuit the way a DENY
   does — the loop keeps evaluating every remaining policy after one ASKs.
   If a later policy in the list then DENYs, that DENY wins and the earlier
   ASK is discarded entirely (`engine.py:363-370` returns DENY immediately;
   `ask_reasons` only gets checked after the full loop, `engine.py:382`).
   So the actual precedence per evaluation is **DENY beats ASK beats
   ALLOW**, not "first verdict wins." Worth deliberately deciding on, not
   copying by accident — lawkeeper's own guards are currently independent
   scripts with no shared precedence rule at all.
2. **Policies can rewrite content, not just gate it.** A policy's `data`
   return value gets fed forward as the next policy's input
   (`ctx = replace(ctx, content=composed_data)`, `engine.py:371-375`) — so
   the pipeline supports sequential *transformation* (e.g. redact a secret
   out of a tool-call argument) in the same pass as allow/deny, not just a
   veto. Lawkeeper's guards today only ever block; auto-fixing-then-allowing
   (e.g. stripping a stray credential from a commit rather than just
   rejecting it) is a real capability gap this pattern would close.
3. **A `read_only` dry-run mode exists as a first-class parameter**, used by
   a "preview what would happen" API route for read-only collaborators
   (`engine.py:317-326`) — same evaluation, no persisted side effects.
   Directly transferable idea: a `lawkeeper check --dry-run` that runs the
   same guards as `pre-commit` without blocking anything, for a contributor
   or reviewer to sanity-check *before* staging.
4. **The ASK round-trip is modeled verbatim on MCP's `elicitation/create`
   primitive** (`approval.py:13-30`) — same wire shape for the request and
   the reply. That's not an incidental choice: it means any existing MCP
   client already knows how to render and answer the approval prompt, for
   free. Directly relevant if lawkeeper's `AUDIT:`-marker-missing "pause and
   ask a human" case is ever handled by something other than a blocking
   CLI prompt (e.g. a bot posting to the PR).
5. **Verdict parsing is fail-closed and distinguishes three outcomes, not
   two.** `_parse_verdict` returns `True` *only* for an exact
   `{"action": "accept"}` — malformed JSON, a missing field, a timeout, and
   an explicit `"cancel"` all collapse to `False`/DENY
   (`approval.py:322-347`). But an explicit `{"action": "decline"}` is
   handled separately: it raises `ElicitationDeclinedError` instead
   (`approval.py:148-152`), so the caller can abort the agent's turn
   outright rather than feed the agent a DENY it might just retry or route
   around. That three-way split — approve / explicit human refusal /
   everything-else-fails-closed — is a sharper model than lawkeeper's
   current binary, and the "explicit refusal aborts the turn, doesn't just
   deny the one action" behavior is worth deliberately deciding on.
6. **No side effects survive a non-approval, by construction.** Label
   writes and state updates from an ASKing policy are computed but withheld
   until `_await_elicitation` sees an actual accept
   (`approval.py:154-163`); every other path drops them. Same invariant
   lawkeeper wants for provisional/audit-pending work, stated here as a
   concrete mechanism (accumulate-but-don't-apply) rather than a principle.
7. **I/O is injected as three plain callback seams** (`register`, `emit`,
   `park` in `approval.py`), not a live task-store/SSE stack — so the whole
   approval flow is unit-testable with canned awaitables instead of
   requiring integration infrastructure. A directly reusable testing
   pattern for lawkeeper's own guard scripts wherever they need to simulate
   "wait for a human decision."
8. **CEL, not Python `eval`, is the dynamic/untrusted-condition DSL.**
   `builtins/cel.py` compiles a user-submitted expression string into a
   policy at runtime (e.g. via a session API call) — chosen specifically
   because CEL is "non-Turing-complete, side-effect-free, and guaranteed to
   terminate — no sandbox escapes, no infinite loops, no file I/O"
   (module docstring). That's the answer to "how do you let someone other
   than the codebase's own developer submit a rule without giving them
   arbitrary code execution" — relevant the moment lawkeeper considers any
   rule surface a non-maintainer (a contributor, an end user) could
   configure rather than a maintainer hand-writing a new guard script.

### Open follow-ups (not done yet)

- Haven't read `schema.py`'s `condition` / label-gate matching or
  `_should_fire`'s `PhaseSelector` logic — the mechanism that decides
  *whether* a policy runs at all before `evaluate` is even dispatched.
  That's the piece that would need the closest reading before designing
  an analogous "which laws apply to this diff" gate for lawkeeper.
- Haven't looked at the full `PolicyEvent` schema CEL expressions actually
  see, or the `risk_score.py` / `routing.py` builtins (unclear from the
  listing alone what problem those solve).
- Still haven't read the harness adapters, sandbox provisioning, or
  `orchestration.py` — out of scope for the governance-mechanism angle
  this doc is tracking, revisit only if lawkeeper's own harness-agnosticism
  work in `EXECUTOR_CONTRACT.md` actually resumes.

---

## Candidate projects queued for future entries

Not yet cloned or read — listed here so the queue survives across sessions
instead of living only in chat:

- ~~**Open Policy Agent (OPA) / Rego**~~ — **covered**, 2026-09-05, in
  `docs/RESEARCH_harness_governance_survey.md` §1. Finding: OPA/Rego has no
  built-in allow/deny/ask precedence algebra at all (`default`/incremental
  rules only govern single-document composition); the community's
  aggregate-`deny`-set pattern is convention, not a language guarantee.
  Apache 2.0; verdict was worth-a-dependency only if/when lawkeeper needs
  non-maintainer-authored rules, not-yet-applicable today.
- **pre-commit** (the framework, not just the hook lawkeeper already
  depends on) — lawkeeper already uses it as a mechanism; worth reading its
  own extension model for ideas on how lawkeeper's guard scripts are
  packaged/versioned/shared across repos (Windwright/orbital-study/falcun
  currently get copies, per `RESEARCH_governance_mechanism_audit.md` —
  that's exactly the "how do policies get distributed and stay in sync
  across repos" problem OPA/pre-commit both had to solve). Explicitly kept
  out of scope for the 2026-09-05 survey pass; still queued.
- ~~**Anthropic's own Claude Agent SDK permission/hook system**~~ —
  **covered**, 2026-09-05, in `docs/RESEARCH_harness_governance_survey.md`
  §2, and this is the survey's headline finding: Claude Code's own
  permission rules already evaluate **deny, then ask, then allow, in that
  fixed order** (confirmed by direct reading of `code.claude.com/docs/en/
  permissions`) — the identical three-tier precedence Omnigent's runtime
  independently converged on — and `PreToolUse` hooks are already a live,
  arbitrary-code ALLOW/DENY/ASK gate on every tool call, confirmed by direct
  reading of `code.claude.com/docs/en/hooks`. Lawkeeper does not need to
  build or port a policy engine to get in-loop enforcement; it needs to
  write one `PreToolUse` hook re-using guard logic it already has. This is
  the survey's "if lawkeeper does ONE thing next" recommendation.

New follow-ups this survey surfaced, not yet read, queued here:

- **MITRE ATLAS's actual technique matrix** — the survey's weakest-sourced
  entry: every fetch attempt against atlas.mitre.org this pass returned an
  empty shell or 404 (likely a JS-rendered SPA the fetch tool couldn't
  render), so whether it covers agentic tool-use techniques (vs. only
  classical ML evasion/poisoning attacks) is still unconfirmed. Needs a
  different fetch strategy (a headless-browser read, or MITRE's own STIX
  data export) before it can be cited for anything.
- **AWS Cedar's own policy reference + Cedar Analysis toolkit** — this
  survey read only AWS's blog post about Cedar's use in Bedrock AgentCore
  (a real first-party source, but secondary to the language spec itself);
  `docs.cedarpolicy.com` and the `cedar-policy/cedar` GitHub repo returned
  TLS errors every attempt. Worth a dedicated read if lawkeeper ever
  seriously considers an unconditional-forbid (no-ASK-escape-hatch) tier for
  a subset of Laws (Law 15's canonical-branch-deletion guard was the
  candidate named in the survey).
- **SLSA + in-toto's structured-attestation shape, applied concretely to
  Law 14/18** — the survey read both specs directly and recommends
  redesigning lawkeeper's `AUDIT:` text marker and Law 18's theory-card
  files as subject-bound, typed attestations (an in-toto `Statement` +
  `Predicate` keyed to the commit tree digest) instead of free text and a
  separate file convention. Not read yet: whether `in-toto`'s own Python
  reference implementation (layout signing, key management) is worth
  depending on directly versus just borrowing the JSON shape.
- **OWASP's Top 10 for Agentic Applications, full ASI01–ASI10 text** — this
  survey only got the category names and one-line descriptions secondhand
  (search-result aggregation); the actual document (a PDF download this
  pass's tools couldn't retrieve) likely has concrete per-category
  mitigations worth checking against lawkeeper's Law 11/19 team-channel
  protocol, which the survey found has no adversarial framing at all today.

---

## Entry (secondary, not independently verified): Falcun's neurosymbolic/harness-field research burst, relayed 2026-09-13

**Provenance discipline, stated up front per explicit user instruction
(2026-09-13):** the documents below are Falcun's own internal research
reports — a secondary synthesis of external papers, not the papers
themselves, and not independently re-read by lawkeeper. Several earlier
Devin-authored research reports in the same research trail were later
found to contain mistakes, subsequently fact-checked and corrected in
Falcun's own follow-up reports — internal reports, including this one,
are not canonical and are not a substitute for tracing to the actual
paper/repo before anything gets built on a specific claim. Everything
below is written as "Falcun's research claims X, citing primary source
Y" — not as "X is true" — except where explicitly marked as verified
directly against lawkeeper's own repo, which this session did check itself.

- **Source:** `E:\falcun\docs\research\MASTER_REPORT_HARNESS_NEUROSYMBOLIC_RELEVANCE_2026-09-09.md`
  (661 lines, read in full) plus `SEP_7_9_RESEARCH_BURST_MAP_2026-09-10.md`
  (an index of 10 related documents, cross-referencing and partially
  independently verifying the master report). Not read: the other 8
  mapped documents, judged by the burst-map's own account to be either
  near-duplicates of the master report or Falcun-specific (evolver
  wiring, governance.py re-grounding) with no lawkeeper relevance.

- **The one claim this session verified directly, not trusted secondhand:**
  the master report (dated 2026-09-09) states lawkeeper has "No PreToolUse
  hooks" and "the enforcement surface stops at the git boundary." Checked
  directly against lawkeeper's own repo just now (2026-09-13): **still
  accurate for `main`** — `gate_pretooluse.py` exists only on the still-open,
  unmerged PR #19, confirmed via `git log` against both `main` and the PR
  branch. Not stale, but worth re-checking again once #19 actually merges.

- **Falcun's claim, not independently re-verified by lawkeeper:** a survey
  (Mättas, Järv & Tammet, "A survey of neurosymbolic artificial
  intelligence," Neuro-Symbolic AI journal) is characterized as converging
  the field on "the LLM is an untrusted generator, and value is created
  only where a symbolic, deterministic, checkable component verifies,
  constrains, or gates what it produces." **Worth stating plainly since it
  corrects a hypothesis raised in this session**: per Falcun's account of
  this literature, neurosymbolic approaches do not reduce the need for
  harness/gating machinery — they're characterized as the opposite,
  strengthening the case for deterministic gates over LLM self-grading,
  which is the same direction lawkeeper's git hooks and the PreToolUse
  work already point. Stated here as what Falcun's synthesis claims the
  survey says, not as a verified fact about the survey itself — lawkeeper
  has not read paper 933 directly.

- **Falcun's claim, citing a real DOI, not independently re-verified:**
  ANSA (ICAART 2026, DOI 10.5220/0014442700004052) is characterized as
  describing "verifier agents enforce hard constraints as final
  gatekeepers, independent of upstream inference" — glossed by Falcun's
  report as matching lawkeeper's Law 16. Recorded here as a citation worth
  tracing directly (the DOI is real and checkable) before treating Law 16
  as externally validated by it.

- **An external assessment of lawkeeper's own execution reality** (Falcun's
  report, §7.2, dated 2026-09-09, described as based on a subagent's
  file:line evidence pass over lawkeeper's own repo): roughly ~30% of the
  23 laws mechanically enforced (3 full, ~7 partial/existence-check-only,
  11 prose-only), the theory-card/`governed_test.py` system's independent-
  oracle discipline treated as a real, comparatively strong asset, and the
  git-hook-only enforcement boundary as the clearest gap. The ~30%/3-fully-
  enforced figure is a real, independent corroboration of this session's
  own much earlier finding (this doc's own history: only 3 of 24 guard
  scripts wired to git hooks, found via direct `system_audit.py`/hook-file
  inspection, not from this report) — two separately-run checks landing on
  the same number is worth noting, but the corroboration is about the
  *conclusion*, not proof the report's own methodology was sound throughout.

- **AEF pieces still explicitly open, not decided against:** Falcun's
  report recommends porting AEF's "Tier-0 PreToolUse gate + single-use
  command approvals + Watchtower + idempotency sentinel + process-ancestry
  tracking" as one bundle. This session already ported the PreToolUse gate
  itself (`gate_pretooluse.py`, PR #19) and the scope-boundary
  characterization methodology, and investigated the idempotency sentinel
  specifically and found it not applicable (no stateful approval file to
  race on — see PR #19's own commits). **Not yet ported, still open:**
  the single-use command-hash approval flow, the Watchtower approval
  queue/CLI, and process-ancestry-based origin tracking. None decided
  against — recorded as queued, consistent with the user's explicit
  "keep things open, it's premature to decide on an integration strategy"
  stance from earlier this session.

## Re-check when

Before any new lawkeeper governance mechanism (a new Law, a new guard
script, anything in `GOVERNANCE_PROPOSALS.md` moving to implementation) is
designed from scratch — check this doc first, and add an entry here before
adding a proposal there if the design was informed by outside research.
Before treating anything in the "secondary, not independently verified"
entry above as settled: trace the specific claim to its actual primary
source (paper DOI/arXiv ID, or the AEF repo directly) rather than citing
Falcun's report a second time once removed.

## Known tension, deliberately not resolved yet (2026-09-13)

Lawkeeper has a weekly scheduled cloud research routine
(`trig_01UgJi3thYGyEYQaHFif3CY1`, via claude.ai's own RemoteTrigger
infrastructure) — the same mechanism Windwright already uses for its own
weekly routine. This is itself "an external platform for research
scheduling," which is in real tension with a stated user principle from
4 days earlier (`E:\falcun\docs\research\RESEARCH_SCHEDULING_INDEPENDENCE_2026-09-09.md`,
direct quote: "we should not rely on external platforms for research
scheduling... coding from scratch is surely not necessary"). That
document found a real, ready alternative already on this machine: Hermes
(`NousResearch/hermes-agent`, MIT, 243k★) ships a complete, tested,
self-contained cron/scheduling subsystem requiring no claude.ai
dependency at all.

**Explicit decision, asked directly:** keep the claude.ai routine for now,
revisit later — not urgent enough to unwind immediately. Recorded here so
this doesn't silently become "the architecture" by default, and so a
future session (or this one) doesn't need to re-discover the tension from
scratch. Re-check when a self-hosted/local scheduling migration becomes
an actual priority, not on a fixed cadence, per the Maximum Flexibility
standing philosophy in `docs/AI_CONSTITUTION.md`.
