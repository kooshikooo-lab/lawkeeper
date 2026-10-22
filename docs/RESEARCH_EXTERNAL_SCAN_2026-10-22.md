# External scan — 2026-10-22

Weekly scheduled research pass. Scope per the routine's own brief: runtime/
`PreToolUse`-style agent governance, policy-decision algebras (allow/deny/ask),
git-hook distribution/enforcement patterns, and test-governance/oracle-
independence methodology. Not Windwright's domain (acoustics/CAD) and not
Falcun's (evolutionary mutation, epistemic-claim verification) — a harness's
other features are out of scope here even when its governance mechanism is
in scope.

**Correction note, written after this pass's own first draft, before
merging — recorded here rather than silently rewritten, per this doc's own
"check against the repo's current state" discipline:** this pass's first
draft independently rediscovered the "Claude Code's `permissionDecision` now
has a fourth value, `defer`" finding and presented it as new. While drafting,
`git fetch` surfaced that **two more weekly passes had already landed on
`main`** during this session's own work —
`docs/RESEARCH_EXTERNAL_SCAN_2026-10-08.md` and
`docs/RESEARCH_EXTERNAL_SCAN_2026-10-15.md` — from other concurrent sessions
of this same scheduled routine (confirmed from
`docs/inter-agent/noticeboard/`: this lawkeeper repo runs the routine from
more than one machine/session). The 2026-10-08 pass had already found the
same `defer` drift, in more depth and more precisely sourced (it traces the
change to `anthropics/claude-code#41791` and the `v2.1.89` changelog entry
directly, rather than this pass's own weaker, secondhand version-number
claim) — and the 2026-10-08 pass had **also already fully resolved** the
Codex native-hook-protocol queue item, via a direct clone and read of
`openai/codex`'s own Rust source, which this pass's own first draft had
(wrongly, since it didn't know about the newer doc when drafting) reported
as "still blocked." Both sections below are rewritten to not duplicate
already-published findings and to correct the Codex claim, rather than left
as drafted. What survives from this pass's own independent work is the
genuinely new material below (§§1–2) plus corrected, cross-referenced
treatment of the two queue items (§§3–4).

**Step 0 sync note:** `python scripts/system_audit.py` initially FAILed
("`lint-imports` command is not installed") — fixed by `pip install
import-linter` in this session's environment (not a lawkeeper code or config
change); re-run passed clean.

---

## 1. Two Claude Code hook events not covered by any prior pass — `PermissionDenied` and `PermissionRequest`

Found while re-reading `code.claude.com/docs/en/hooks` (the same page the
2026-10-08 pass's `defer` finding came from) for an unrelated reason —
checked this isn't a duplicate by grepping all five existing `RESEARCH_*.md`
docs for "PermissionDenied" and "PermissionRequest" before writing this up:
zero hits for either term anywhere in the research base, including the
2026-10-08 and 2026-10-15 passes (the latter's GitHub-Copilot entry covers
Copilot's own analogous events, not Claude Code's).

- **What was actually read this pass:** the `code.claude.com/docs/en/hooks`
  event-lifecycle table (all 33 named events) and the `PermissionDenied`/
  `PermissionRequest` rows of the decision-control, exit-code, and
  input-rewriting tables, fetched and read directly. **Not read:** the
  dedicated prose section for either event, or either event's full
  input-JSON schema — both pages' content for these events fell past this
  pass's read window; flagged rather than guessed at.
- **License:** N/A — Anthropic's own current documentation for the runtime
  `gate_pretooluse.py` already targets.
- **`PermissionDenied` — audit-shaped, cannot reverse the denial, quoted
  directly:** fires "when auto mode denies a tool call, including denials
  without a classifier verdict." Exit code and stderr are explicitly
  inert — "Exit code and stderr are ignored because the denial already
  occurred" — and the only output with any effect is
  `hookSpecificOutput.retry: true`, which tells the model it *may* retry the
  same call; it does not reverse the denial, and retry is itself ignored
  "when the classifier produced no verdict." By the docs' own description
  this is a strictly **after-the-fact observer**: it cannot allow, deny, or
  rewrite anything, only hint "you may try again" or not.
- **`PermissionRequest` — a decision point, but narrower than `PreToolUse`,
  and a different shape than Codex's own event of the same name:** fires
  "when a tool call needs a permission decision," with its own decision
  shape — `hookSpecificOutput.decision.behavior` (`"allow"/"deny"` only,
  confirmed from the decision-control table — **no `ask` or `defer` value
  exists for this event**), its own `updatedInput` location (nested inside
  `decision`, not top-level the way `PreToolUse`'s is), and its own failure
  default: `onFailure: "block"` for this event is explicitly stated as
  "denies the request" — a fail-closed default stated specifically for this
  event, not inherited generically. Exit code 2 is explicitly *not* honored
  for `PermissionRequest` ("Exit code 2 isn't honored for this event and the
  permission flow proceeds unchanged. Deny through the `decision` object
  instead") — a real, specific exception to the exit-code-2-blocks
  convention every other `PreToolUse`-shaped mechanism in this research base
  relies on. Note this is a **same-named but structurally distinct** event
  from Codex's own `PermissionRequest` (the 2026-10-08 pass's §2 — Codex's
  version has a `PermissionRequestDecisionWire.behavior` enum confirmed from
  source to also be strictly `Allow`/`Deny`, so the two products converge on
  the same binary shape for this specific event under the same name, which
  is itself worth recording as a seventh/eighth data point for this
  research base's deny-wins convergence tally rather than two unrelated
  facts).
- **How `PermissionRequest` relates to `PreToolUse` — genuinely not resolved
  this pass:** the fetched portion of the page places both in the same
  matcher table and the same lifecycle diagram (with `PermissionDenied`
  shown as "a side branch" off whichever flow produces a denial), but this
  pass's reads did not surface an explicit statement of execution order or
  precedence between a `PreToolUse` hook's `permissionDecision` and a
  `PermissionRequest` hook's `decision.behavior` when both are configured
  for the same tool call. Recorded as an open question, not answered from
  inference.
- **The concrete thing worth doing something with — instantiates an
  already-logged idea, not a new one:**
  `docs/RESEARCH_harness_governance_survey.md` §4 already recommended
  upgrading Law 14's `AUDIT:` text marker toward a SLSA/in-toto-shaped
  **structured, subject-bound attestation** instead of a self-asserted
  string. `PermissionDenied` is a concrete, already-shipped hook point that
  fires at exactly the moment such an attestation would need to be written
  for a *denied* call — "this tool call, this reason, this policy, this
  timestamp" — without lawkeeper having to infer a denial happened from
  `gate_pretooluse.py`'s own exit path. **Checked directly against
  lawkeeper's own repo: this hook is not wired anywhere** —
  `.claude/settings.json` (both the live repo-root one and the shipped
  `src/guardrail/template/.claude/settings.json`) registers only `Stop`,
  `PreToolUse`/`Bash`, `SessionStart`, `UserPromptSubmit`, and `PostToolUse`.
  No `PermissionDenied` handler exists today — a real, currently-open gap,
  not a hypothetical.
- **Verdict: adopt-the-design for a future Law 14 upgrade** (a
  `PermissionDenied` hook writing a structured deny-attestation, concretely
  instantiating the SLSA/in-toto-shaped idea the governance survey already
  logged) — **not urged for immediate implementation**, since this scan's
  job is research, not build. For `PermissionRequest`: **not yet
  actionable** — its relationship to `PreToolUse` needs resolving first (a
  future pass should read both events' dedicated prose sections directly,
  not just the summary tables) before recommending anything built against
  it.

---

## 2. Elicitation / ElicitationResult — now native Claude Code hook events, not read beyond their names this pass

- **What was actually read:** only the event-lifecycle table's two rows
  (`Elicitation`, `ElicitationResult`) listing their names and one-line
  triggers; **nothing else** — no input schema, no decision shape, no
  stated relationship to the MCP `elicitation/create` primitive
  `docs/RESEARCH_harness_governance_survey.md` §5 already read in full from
  the MCP spec itself.
- **Why this is worth flagging even half-read:** if these events expose the
  MCP elicitation accept/decline/cancel three-way split natively inside
  Claude Code's own hook system, that would be a direct, shippable answer to
  the governance survey's own "adopt-the-distinction (decline vs.
  cancel/timeout are different outcomes)" recommendation for any future
  lawkeeper ASK-tier mechanism — not a port of the idea, but the exact
  mechanism already present in the runtime lawkeeper targets. Stated as a
  hypothesis worth checking, not a finding.
- **Verdict: unresolved, queued** — do not cite this as confirming anything
  about decline/cancel support until the dedicated sections are actually
  read.

---

## 3. Codex's native hook protocol — already fully resolved by the 2026-10-08 pass; this pass adds post-resolution, carefully-caveated incremental evidence only

**This section's framing was wrong in this pass's own first draft**, which
attempted the same blocked documentation domain this session's egress policy
has refused since 2026-09, found the same block, and (not yet aware of
`docs/RESEARCH_EXTERNAL_SCAN_2026-10-08.md`) reported the item as "still
unresolved, stays queued." It is not. `docs/RESEARCH_EXTERNAL_SCAN_2026-10-08.md`
§2 closed this by cloning `openai/codex` directly (Apache-2.0, commit
`d2a6dac20b3b76d4b95d8a699ef7bc6ee3a852d6`) and reading
`codex-rs/hooks/src/engine/output_parser.rs`,
`codex-rs/hooks/src/events/pre_tool_use.rs`, and
`codex-rs/hooks/src/events/permission_request.rs` directly — confirming,
from the actual validation code rather than any secondhand account:
`permissionDecision: "ask"` on `PreToolUse` is parsed, explicitly recognized
as `unsupported_pre_tool_use_hook_specific_output`, and fails open (hook run
marked `Failed`, tool call proceeds); an **async**-configured handler cannot
block or deny *anything*, by a type-level dispatcher guarantee
(`can_apply_control_effects()`), a second, independent fail-open path;
Codex's own `PermissionRequest` event is strictly binary `Allow`/`Deny`,
with no `ask` enum value to even reject. That is a direct, primary-source
read — this pass's own attempt at the vendor's documentation site was not
needed and should not have been reported as the open state of this item.

What this pass can still add, found via direct `WebFetch` reads of the
vendor's own issue tracker (not search-snippet aggregation), as **evidence
layered on top of an already-closed finding**, not evidence needed to close
it:

- **`openai/codex#27833`** (the `apply_patch` deny-not-enforced report,
  already covered as a live, mixed-evidence thread by the 2026-10-01 pass)
  has a new comment since then, dated 2026-10-14, from a user
  (`wattwong103`): "Exiting [with exit code 2] with the JSON deny on stdout
  blocks correctly on 0.162.1," and separately: "Windows PowerShell 5.1
  reports the hook's exit 2 as 1" — a concrete, checkable, user-proposed
  explanation for some of the thread's earlier Windows non-enforcement
  reports being a PowerShell-version exit-code-translation artifact, not a
  Codex dispatch bug. Stated as what the comment says, not as this session's
  own confirmed finding — it does not resolve the thread (which remains
  open, version/platform-mixed), but it is a real, specific, checkable claim
  worth a future pass's attention, and a sharper version of the
  `EXECUTOR_CONTRACT.md` warning already on record: a future Codex adapter's
  characterization tests need to control for host shell (PowerShell vs.
  Bash exit-code semantics), not just Codex version.
- **`openai/codex#49736`** (the `spawn_agent` hook-never-fires report) is
  still open with **no replies**, unchanged substantively, except the issue
  now carries triage labels (`bug`, `CLI`, `windows-os`, `hooks`,
  `subagent`) applied via an automated event, not a maintainer comment.
  Flagged explicitly: a label is not a maintainer confirmation — recorded as
  "still unconfirmed by anyone but the original reporter," not upgraded.
- **`i9wa4/dotfiles#378`** was closed by its own author on 2026-09-23 —
  because the author fixed *their own dotfiles hook script*, not because
  Codex shipped `ask` support. The closing comment doesn't mention `ask` or
  retract the original "parsed but not yet supported" claim. This is
  consistent with, and now additionally confirmed by, the 2026-10-08 pass's
  direct source read.
- **A `WebSearch` summary this pass ran turned up a conflicting, unverified
  third-party claim** that Codex's official docs describe `PreToolUse` JSON
  support for `permissionDecision: "ask"` actually prompting the user — the
  search tool's own synthesis filed this under "third-party references,"
  not "official docs," and it directly conflicts with the 2026-10-08 pass's
  own source-level finding (`ask` fails open, confirmed from
  `output_parser.rs`). **Resolved in favor of the source read, not the
  secondhand search claim** — recorded only so a future pass doesn't
  rediscover the same conflicting snippet and wonder whether it changes
  anything. It doesn't.
- This pass's own attempt to reach `developers.openai.com` directly failed
  identically to every prior pass's attempt (`curl -v` through this
  session's proxy: explicit `HTTP/1.1 403 Forbidden`; `WebFetch`:
  `getaddrinfo ENOTFOUND`) — consistent with, not a new data point beyond,
  the four prior passes' identical finding that this specific domain is
  blocked for this routine's sessions. Not re-queued; the item is already
  closed via the source-code read, which doesn't need this domain at all.
- **Verdict: closed (per 2026-10-08), not queued.** The `adopt-the-warning`
  guidance for `EXECUTOR_CONTRACT.md` stands and gains one more specific
  caveat from this pass (host-shell exit-code semantics as a confound for
  future characterization tests), not a new mechanism or a reopened
  question.

---

## 4. The Open Plugins hooks specification — still blocked, fourth consecutive pass, one small new fragment

- **Prior status:** queued since 2026-09-06; blocked on every attempt across
  2026-10-01, 2026-10-08, and 2026-10-15 (four distinct access strategies
  tried across those three passes: direct fetch, a cached-mirror fetch, a
  reader-proxy fetch via `r.jina.ai`, and a GitHub-org-mirror check — all
  blocked at the network layer, not by the content not existing).
- **What was attempted this pass, same outcome as before:** a direct `curl
  -v` `CONNECT` through this session's proxy to `open-plugins.com:443`
  (explicit `HTTP/1.1 403 Forbidden`) and a `WebFetch` call to the same URL
  (`getaddrinfo ENOTFOUND`) — the same two failure signatures the 2026-10-01
  and 2026-10-15 passes already recorded for this domain. Not retried a
  second time, per the proxy's own no-retry-on-policy-denial guidance.
  **Still blocked, now a fourth consecutive weekly pass.**
- **One small, genuine fragment, via search-result snippet aggregation only
  (not a direct fetch, flagged as such) — not surfaced by any prior pass:**
  a search snippet of `open-plugins.com/plugin-builders/specification` (a
  *different* page than goose's own cited `/agent-builders/components/hooks`
  URL — the spec appears to have separate documentation trees for someone
  *authoring* a plugin versus someone *consuming* plugins in a harness)
  describes a plugin as "a directory bundling skills, agents, rules, hooks,
  MCP servers, and LSP servers" — confirming hooks are a real, named
  component type in this spec, consistent with goose's own citation, but
  contributing no schema detail beyond that one sentence. Not enough to
  change the verdict.
- **Verdict: unresolved, re-queue again, unchanged.** Four consecutive
  passes and five distinct access strategies have now failed identically —
  reasonably confirmed as a standing policy restriction on this domain for
  this routine's sessions specifically, not a transient failure worth
  retrying with an already-tried method a fifth time. Needs either an
  allowlist change or a GitHub mirror no pass's search has yet surfaced.
  Continue not substituting the "Agent Plugins Specification"
  (`agent-plugins.org`) for it (re-confirmed by the 2026-10-01 pass to be a
  different, hooks-free document; not independently re-checked this pass).

---

## 5. New candidates spotted, not resolved — queued rather than cited from secondhand snippets

Per the task brief's own standard ("do not conclude relevance from a name or
README alone — read real source"): two arXiv papers surfaced by a search for
oracle-independence/mutation-testing methodology (explicitly in-scope per
the brief) looked genuinely on-topic for Law 18's own discrimination-check
mechanism — distinct from the TU Delft oracle-generation lead the
2026-10-15 pass already flagged as unverifiable (different papers, same
general topic area, same outcome) — **but `arxiv.org` (and its
`export.arxiv.org` mirror) returned an explicit `403` from this session's
egress proxy on every attempt**, confirmed via both `WebFetch`
(`ENOTFOUND`) and a direct `curl -v` (`CONNECT tunnel failed, response
403`), not retried further.

- **arXiv 2607.23002, "Adversarial Test-Hardening for AI-Written Code"** — a
  search-snippet summary describes a "pass-on-pristine validation step"
  that prunes generated tests failing on correct/unmutated code before
  trusting them as mutation discriminators, which — **if the snippet's
  characterization is accurate, not independently verified here** — sounds
  structurally close to the exact bug `scripts/governed_test.py`'s own
  `run_mutation` was patched for on 2026-09-06 (confirming the baseline/
  unmutated run passes before trusting a "discriminates" result). Recorded
  as a candidate worth a direct read, explicitly **not** as a confirmed
  parallel — the only source for this claim is a search engine's own
  aggregated summary, not the paper's text.
- **arXiv 2608.17214, "Oracles That Cannot Fail"** — a search-snippet
  summary attributes to it a discussion of Terragni et al. using
  *different* mutation tools for test-improvement versus test-validation
  specifically to avoid circularity — a direct hit on the word
  "independence" in Law 18's own name, if accurate. Same caveat: secondhand,
  not independently read.
- **Verdict for both: queued, not adopted, not even provisionally cited as
  fact anywhere else in lawkeeper's docs.** Re-attempt with direct
  `arxiv.org` access in a future pass (or via a GitHub mirror of either
  paper's LaTeX source, not searched for this pass) before treating either
  claim as checkable.

---

## What this pass found nothing new on

Per the task brief's own instruction: stated plainly. Nothing this pass
surfaced changes the deny>ask>allow convergence verdict from
`docs/RESEARCH_harness_hook_mechanisms_survey.md` or the two `defer`/Codex
findings the 2026-10-08 pass already established in more depth than this
pass's own first attempt at them — §§3 above is corrected to say so rather
than re-present either as open or as this pass's own discovery. No
Falcun-relayed report was encountered or relied on this pass; nothing here
traces through a secondary research report from another repo.

## Re-check when

- `open-plugins.com` and `developers.openai.com` — `open-plugins.com`
  remains genuinely queued (§4); `developers.openai.com` does not need
  re-checking for the Codex-hook-protocol question specifically, since that
  question is closed via source (§3) — but re-attempt the domain directly
  for anything else Codex-doc-specific whenever a future session's egress
  policy might differ.
- `PermissionRequest`'s precedence relative to `PreToolUse` (§1) and the
  `Elicitation`/`ElicitationResult` event pair's actual decision shape (§2)
  — both need a direct read of their dedicated sections on
  `code.claude.com/docs/en/hooks` (this pass only read the summary tables
  that mention them) before anything is built or claimed about either.
- arXiv 2607.23002 and 2608.17214 (§5) — re-attempt direct access; do not
  cite either paper's specific claims anywhere else in lawkeeper's docs
  until read directly.
- **Process note for future passes, not a research finding:** this pass
  discovered mid-draft that this routine runs from more than one
  session/machine concurrently (per `docs/inter-agent/noticeboard/`), which
  is how two newer scans landed on `main` during this session's own work
  without this session knowing at start time. A future pass should `git
  fetch origin main` again immediately before finalizing its own doc (not
  just at Step 0) to catch a same-week concurrent pass before drafting
  overlapping content, rather than discovering it only when pushing.
