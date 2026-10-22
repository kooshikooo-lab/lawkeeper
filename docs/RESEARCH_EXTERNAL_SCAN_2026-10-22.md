# External scan — 2026-10-22

Weekly scheduled research pass. Scope per the routine's own brief: runtime/
`PreToolUse`-style agent governance, policy-decision algebras (allow/deny/ask),
git-hook distribution/enforcement patterns, and test-governance/oracle-
independence methodology. Not Windwright's domain (acoustics/CAD) and not
Falcun's (evolutionary mutation, epistemic-claim verification) — a harness's
other features are out of scope here even when its governance mechanism is
in scope.

**Three weeks since the last pass** (`docs/RESEARCH_EXTERNAL_SCAN_2026-10-01.md`,
2026-10-01) — confirmed via `git log -- 'docs/RESEARCH_EXTERNAL_SCAN_*.md'`,
only one prior entry exists. In the gap, several of that pass's recommendations
were actually implemented on `main` (confirmed by `git log --oneline`, not
assumed): `lawkeeper update` with diff-first sync (#36, closing the
pre-commit-distribution gap §3 identified), an advisory mutmut CI job plus
survivor-diff reporting (#37–#39, the supplementary-mutation-pass idea §6
recommended), and `gate_pretooluse.py` is now live and wired on `main`
(`.claude/settings.json`'s `PreToolUse`/`Bash` matcher) — the survey's "if
lawkeeper does ONE thing next" recommendation from `RESEARCH_harness_governance_survey.md`
is done, not still a proposal.

**Step 0 sync note:** `python scripts/system_audit.py` initially FAILed
("`lint-imports` command is not installed") — fixed by `pip install
import-linter` in this session's environment (not a lawkeeper code or config
change); re-run passed clean. Recorded here per AGENTS.md's "on any Law
violation" discipline, even though this was an environment gap, not a policy
violation.

**Queue status going in:** two items from the base surveys' queue remain open
— the Open Plugins hooks specification (`open-plugins.com`) and Codex's
native hook protocol read directly. Both were attempted again this pass, per
the brief's instruction to prioritize the queue; both are **still blocked** at
this session's egress layer, unchanged from 2026-10-01 (see §§2–3). Neither
is closed on secondhand confidence. The pass's substantive new finding came
instead from re-reading Claude Code's own hooks docs directly (lawkeeper's
actual target runtime, not a queued third party) and finding real drift since
every prior pass read that same page — see §1, the headline finding below.

---

## 1. Claude Code's own `permissionDecision` has drifted to four values, not three — a correction to two load-bearing citations

This is the pass's headline finding: not a new tool, a **correction to
primary-source claims already cited as settled** in
`docs/RESEARCH_harness_governance_survey.md` §2 and
`docs/RESEARCH_harness_hook_mechanisms_survey.md`'s convergence verdict.

- **What was actually read this pass:** `code.claude.com/docs/en/hooks`,
  fetched and read directly across its full length (the page is ~273,000
  characters; read in three passes at different offsets to cover the
  `PreToolUse` decision-control section, the multi-hook precedence section,
  and the `PermissionDenied`/`PermissionRequest` event descriptions — not a
  single truncated fetch). This is the identical URL both base surveys cite
  as read in full on 2026-09-05 — re-read now, not a new source.
- **License:** N/A — Anthropic's own current documentation for the exact
  runtime lawkeeper's `gate_pretooluse.py` already targets.
- **The actual drift, quoted directly from the live page:**
  - The decision-control table: `permissionDecision` (`"allow"/"deny"/"ask"/
    "defer"`) — a fourth value, `defer`, that did not appear in either base
    survey's account of this page.
  - `defer`'s definition, quoted verbatim: `"defer" ends the turn so the tool
    can be resumed later, and requires non-interactive mode with the -p
    flag`. It is explicitly for "integrations that run `claude -p` as a
    subprocess" — the page states Claude Code "honors this value only in
    non-interactive mode... In interactive sessions it logs a warning and
    ignores the hook result," and it only applies "when Claude makes a single
    tool call in the turn" (multiple simultaneous tool calls make Claude Code
    ignore `defer` with a warning and fall through to the normal permission
    flow). `updatedInput` and `additionalContext` are both ignored for
    `defer`.
  - **The precedence rule, quoted verbatim, now four-tier, not three:**
    "When multiple PreToolUse hooks return different decisions, precedence is
    `deny` > `defer` > `ask` > `allow`."
  - `permissionDecisionReason` visibility now varies by value too: shown to
    the user for `ask`, shown to Claude for `deny`, written only to the debug
    log for `allow` and `defer`.
- **Does this contradict the five-system convergence finding
  (`RESEARCH_harness_hook_mechanisms_survey.md`'s closing verdict)?** No —
  refines it, doesn't break it. `defer` is additive and Claude-Code-specific
  (a resume-later primitive for headless/subprocess orchestration, with no
  analog read in Omnigent, dsh, Hermes, or goose); the relative ordering
  `deny > ask > allow` the five-system convergence rests on is still true as
  a sub-ordering of the current four-tier rule (`deny > defer > ask > allow`
  implies `deny > ask > allow` once `defer`-eligible cases are set aside).
  What's actually wrong is narrower and more specific: the governance
  survey's own sentence, "Claude Code's permission system evaluates deny,
  then ask, then allow, in that fixed order" (§2, stated as directly quoted
  from this exact page on 2026-09-05), is **no longer a complete quote of
  what the page says today** — whether that's because the docs changed
  since September or because that pass's read of this specific section was
  incomplete is not resolvable from here (see below), but either way the
  claim as currently stated in that doc should not be treated as a complete
  account of the page without this update.
- **When did this ship, and was it already true in September?** `defer`
  itself is not new as of this pass — a secondhand-but-consistent pair of
  third-party release trackers (a changelog-aggregator site and a dated
  monthly release-roundup page, not Anthropic's own changelog, which this
  pass's fetch of `raw.githubusercontent.com/anthropics/claude-code/main/
  CHANGELOG.md` could not locate a matching entry for within the portion
  read) place `defer`'s introduction at **v2.1.89, dated 2026-03-31/04-01** —
  almost five months before either base survey's 2026-09-05/06 reads of this
  same page. This is flagged explicitly as **secondhand** (not Anthropic's
  own changelog text, which this pass attempted and could not confirm within
  budget) — but if accurate, it means `defer` already existed when both base
  surveys read this page and asserted a three-way precedence; the gap is in
  what got read/quoted then, not just subsequent product drift. Recorded
  plainly as an open question rather than resolved either way.
- **Checked directly against lawkeeper's own repo, not assumed:**
  `scripts/gate_pretooluse.py` only ever emits `"allow"|"deny"|"ask"` (its own
  docstring at line 13 states exactly these three; `_decide`'s return-type
  comment at line 427 says the same) and is wired only to the `PreToolUse`/
  `Bash` matcher in `.claude/settings.json` (and the shipped
  `src/guardrail/template/.claude/settings.json`). This is not a bug —
  `defer`'s own precondition (`-p`, non-interactive, single-tool-call turns)
  doesn't match lawkeeper's own interactive-session gate use case — but it
  means lawkeeper's gate has never emitted or needed to reason about `defer`,
  and the merge-precedence lawkeeper's own `GateDecision` design should cite
  going forward is the four-tier one, not the three-tier one, should
  lawkeeper ever run multiple competing `PreToolUse` hooks on the same
  matcher.
- **One concrete thing to do with this:** update the governance survey's §2
  claim (or at minimum this doc, cross-referenced from there) to state the
  current four-tier precedence rather than let the three-tier quote stand
  unqualified — a future design decision citing "Claude Code's own documented
  behavior" for a `GateDecision` type should cite `deny > defer > ask >
  allow`, not `deny > ask > allow`, even though `defer` itself is not
  something lawkeeper's current gate needs to emit.
- **Verdict: adopt-the-correction (not a new mechanism to build) —
  lawkeeper's own `GateDecision` precedence citation should be updated to the
  four-tier rule; `defer` itself is not-applicable to build toward today**
  (lawkeeper's gate is interactive-session-only; `defer`'s own precondition
  doesn't fit), **but the fact it exists is worth lawkeeper's `
  EXECUTOR_CONTRACT.md` knowing about**, since a future non-interactive
  invocation mode (e.g. a CI-triggered headless Claude Code run) could
  plausibly want to defer rather than ask when no human is present — a
  real, sourced alternative to Hermes'/dsh's/goose's own "session-level
  policy dial decides whether ask is even consulted" pattern already logged
  in the hook-mechanisms survey, native to Claude Code itself rather than
  something lawkeeper would have to build.

---

## 2. Two new-since-September hook events — `PermissionDenied` and `PermissionRequest` — one is a real candidate for Law 14's attestation idea

Found while reading §1's source for the precedence section; logged separately
because the governance implication is distinct from the precedence question.

- **What was actually read this pass:** the same `code.claude.com/docs/en/hooks`
  page — the event-lifecycle table (all 33 named events), the `PermissionDenied`
  and `PermissionRequest` rows of the decision-control, exit-code, and
  input-rewriting tables. **Not read:** the dedicated prose sections for
  either event (both fell past this pass's read window — see "not resolved"
  below) or either event's full input-JSON schema.
- **`PermissionDenied` — audit-shaped, cannot reverse the denial, quoted
  directly:** fires "when auto mode denies a tool call, including denials
  without a classifier verdict." Exit code and stderr are explicitly inert —
  "Exit code and stderr are ignored because the denial already occurred" —
  and the only output that has any effect is `hookSpecificOutput.retry: true`,
  which tells the model it *may* retry the same call; it does not reverse the
  denial, and the page states retry is itself ignored "when the classifier
  produced no verdict." This is, by the docs' own description, a strictly
  **after-the-fact observer**: it cannot allow, deny, or rewrite anything —
  only hint "you may try again" or not.
- **`PermissionRequest` — a decision point, but narrower than `PreToolUse`:**
  fires "when a tool call needs a permission decision," with its own,
  separate decision shape — `hookSpecificOutput.decision.behavior`
  (`"allow"/"deny"` only, confirmed from the decision-control table — **no
  `ask` or `defer` value exists for this event**), its own `updatedInput`
  location (nested inside `decision`, not top-level the way `PreToolUse`'s
  is), and its own failure default: the `onFailure: "block"` behavior for
  this event is explicitly "denies the request" on failure — a fail-closed
  default stated specifically for this event, not inherited generically.
  Exit code 2 is explicitly *not* honored for `PermissionRequest` ("Exit code
  2 isn't honored for this event and the permission flow proceeds unchanged.
  Deny through the `decision` object instead") — a real, specific exception
  to the exit-code-2-blocks convention every other PreToolUse-shaped
  mechanism in this research base (Claude Code's own `PreToolUse`, goose,
  Hermes, dsh) relies on.
- **How `PermissionRequest` relates to `PreToolUse` — genuinely not resolved
  this pass, flagged rather than guessed:** the fetched portion of the page
  states PreToolUse and PermissionRequest are both listed in the same
  matcher table and the same lifecycle diagram (with `PermissionDenied`
  shown as "a side branch" off whichever flow produces a denial), but this
  pass's reads did not surface an explicit statement of execution order or
  precedence between a `PreToolUse` hook's `permissionDecision` and a
  `PermissionRequest` hook's `decision.behavior` when both are configured for
  the same tool call. Recorded as an open question for a future pass, not
  answered here from inference.
- **The concrete thing worth doing something with — ties directly to an
  already-logged idea, not a new one:** `RESEARCH_harness_governance_survey.md`
  §4 already recommended upgrading Law 14's `AUDIT:` text marker toward a
  SLSA/in-toto-shaped **structured, subject-bound attestation** instead of a
  self-asserted string. `PermissionDenied` is a concrete, already-shipped
  hook point that fires at exactly the moment such an attestation would need
  to be written for a *denied* call — "this tool call, this reason, this
  policy, this timestamp" — without lawkeeper having to infer a denial
  happened from `gate_pretooluse.py`'s own exit path. **Checked directly
  against lawkeeper's own repo: this hook is not wired anywhere** —
  `.claude/settings.json` (both the live repo-root one and the shipped
  template) registers only `Stop`, `PreToolUse`/`Bash`, `SessionStart`,
  `UserPromptSubmit`, and `PostToolUse`. No `PermissionDenied` handler exists
  today, so this is a real, currently-open gap, not a hypothetical.
- **Verdict: adopt-the-design for a future Law 14 upgrade (a `PermissionDenied`
  hook writing a structured deny-attestation, concretely instantiating the
  SLSA/in-toto-shaped idea the governance survey already logged) — not
  urged for immediate implementation, since this scan's job is research, not
  build.** For `PermissionRequest`: **not yet actionable** — its relationship
  to `PreToolUse` needs resolving first (a future pass should read the two
  events' dedicated prose sections directly, not just the summary tables)
  before recommending anything built against it; recorded as a queued
  follow-up (§5) rather than acted on from a partial read.

---

## 3. Elicitation / ElicitationResult — now native Claude Code hook events, not read beyond their names this pass

- **What was actually read:** only the event-lifecycle table's two rows
  (`Elicitation`, `ElicitationResult`) listing their names and one-line
  triggers; **nothing else** — no input schema, no decision shape, no
  relationship to the MCP `elicitation/create` primitive
  `RESEARCH_harness_governance_survey.md` §5 already read in full from the
  MCP spec itself.
- **Why this is worth flagging even half-read:** if these events expose the
  MCP elicitation accept/decline/cancel three-way split natively inside
  Claude Code's own hook system, that would be a direct, shippable answer to
  the governance survey's own "adopt-the-distinction (decline vs.
  cancel/timeout are different outcomes)" recommendation for any future
  lawkeeper ASK-tier mechanism — not a port of the idea, but the exact
  mechanism already present in the runtime lawkeeper targets. This is stated
  as a hypothesis worth checking, not a finding — confirming it needs the
  dedicated section read, not just the event names.
- **Verdict: unresolved, queued (§5)** — do not cite this as confirming
  anything about decline/cancel support until the dedicated sections are
  actually read.

---

## 4. Open Plugins hooks specification — still blocked, one small secondhand fragment, no schema

- **Prior status:** blocked every attempt since 2026-09-06; the 2026-10-01
  pass's three attempts all returned `EGRESS_BLOCKED` and were not retried
  per the proxy's own no-retry-on-policy-denial guidance.
- **What was attempted this pass:** a direct `curl` `CONNECT` through this
  session's own egress proxy to `open-plugins.com:443` (not a DNS/TLS
  failure this time — an explicit `HTTP/1.1 403 Forbidden` from the proxy
  itself, confirmed via `-v` output, i.e. a policy block, same class as
  before) and a `WebFetch` call to the same URL (`getaddrinfo ENOTFOUND` —
  a different failure signature than the proxy's 403, but the same
  practical outcome: unreachable from this session). Per the proxy's own
  guidance, neither was retried a second time. **Still blocked, unchanged
  from 2026-10-01** — not re-queued on new grounds, just re-confirmed.
- **One small, genuine fragment, via search-result snippet aggregation only
  (not a direct fetch, flagged as such):** a search snippet of
  `open-plugins.com/plugin-builders/specification` (a *different* page than
  goose's own cited `/agent-builders/components/hooks` URL — note the path
  difference: "plugin-builders" vs. "agent-builders", i.e. the spec appears
  to have separate documentation trees for someone *authoring* a plugin
  versus someone *consuming* plugins in a harness) describes a plugin as "a
  directory bundling skills, agents, rules, hooks, MCP servers, and LSP
  servers" — confirming hooks are a real, named component type in this spec,
  consistent with goose's own citation, but contributing no schema detail
  beyond that one sentence. Not enough to change the verdict.
- **Verdict: unresolved, re-queue again, unchanged.** Needs either a
  different access path (an allowlist change, or a future session whose
  proxy policy differs) or a GitHub mirror this and the prior pass's
  searches have not surfaced. Continue not substituting the "Agent Plugins
  Specification" (`agent-plugins.org`) for it — re-confirmed this pass to be
  a different spec with no hooks content (unchanged finding from 2026-10-01,
  not independently re-checked this pass since nothing suggested revisiting
  it).

---

## 5. Codex's native hook protocol, read directly — still blocked for primary source, but real incremental evidence from the vendor's own issue tracker

- **Prior status:** `developers.openai.com/codex/hooks` and its redirect
  target were egress-blocked in the 2026-10-01 pass; the account of Codex's
  behavior rested on three GitHub issues (maintainer's own tracker) plus one
  citation-backed third-party analysis, not the vendor's own doc page.
- **What was attempted and the outcome, this pass:** `curl -v` through this
  session's proxy to `developers.openai.com:443` — explicit `HTTP/1.1 403
  Forbidden` from the proxy (policy block, not TLS/DNS); `WebFetch` to the
  same URL — `getaddrinfo ENOTFOUND`. Same outcome as §4: **still blocked,
  not retried further.** `open-plugins.com` and `developers.openai.com` are
  evidently both policy-denied for this session specifically (both failed
  the same two ways); whether that's a stable, session-independent block or
  specific to this session's egress policy is not something this pass can
  determine.
- **New evidence located this pass, via direct `WebFetch` reads of the
  GitHub issues themselves (the vendor's own tracker, not search-snippet
  aggregation) — `github.com` continues to be reachable, unchanged from
  2026-10-01:**
  - **`openai/codex#27833`** (the `apply_patch` deny-not-enforced report) is
    still open. A new comment since the 2026-10-01 pass's own follow-up read
    (from a user, `wattwong103`, dated 2026-10-14) reports: "Exiting [with
    exit code 2] with the JSON deny on stdout blocks correctly on 0.162.1,"
    and separately proposes a concrete, checkable alternate explanation for
    some of the prior "non-enforcement" reports on Windows: "Windows
    PowerShell 5.1 reports the hook's exit 2 as 1" — i.e. some of the
    Windows non-enforcement reports in this same thread may be a
    PowerShell-version exit-code-translation artifact, not a Codex
    dispatch bug. **This is a real, user-reported, unverified-by-this-session
    claim** (one more comment in an already-mixed, version/platform-dependent
    thread the 2026-10-01 pass already flagged as "not a confirmed
    product-wide fact") — stated here as what the comment says, not as
    confirmed current behavior. It does not resolve the thread; if anything
    it adds a plausible confound (PowerShell version) that a future pass
    should check for before citing any single report as representative.
  - **`openai/codex#49736`** (the `spawn_agent` hook-never-fires report) is
    still open with **no replies** — unchanged substantively from
    2026-10-01, except the issue now carries triage labels (`bug`, `CLI`,
    `windows-os`, `hooks`, `subagent`) applied via an automated event, not a
    maintainer comment. **Flagged explicitly: a label is not a maintainer
    confirmation** — this could be the reporter's own issue-template label
    selection or an auto-labeler bot, not evidence OpenAI has reproduced or
    accepted the report. Recorded as "still unconfirmed by anyone but the
    original reporter," not upgraded.
  - **`i9wa4/dotfiles#378`** (the citation-backed analysis stating
    `permissionDecision: "ask"` is "parsed but not yet supported," quoting
    Codex's own docs) is now **closed**, by its own author, on 2026-09-23 —
    but closed because the author fixed *their own dotfiles hook script* to
    match "the current shared hook behavior on main" (their words), not
    because Codex itself shipped `ask` support. The closing comment does not
    mention `ask` or retract the original claim. **This does not change the
    "ask is parsed but not implemented" finding** — recorded explicitly so a
    future pass doesn't mistake "issue closed" for "Codex fixed it."
  - A `WebSearch` summary (not independently verified against the vendor's
    own page, since that page remains blocked) separately surfaced a
    third-party claim that Codex's *official* docs describe `PreToolUse`
    JSON support for `permissionDecision: "allow"/"deny"/"ask"` with `"ask"
    prompt[ing] the user for manual confirmation" — but the search tool's
    own synthesis explicitly filed this under "third-party references," not
    under its "official docs" bullet, and it directly conflicts with
    `i9wa4/dotfiles#378`'s citation-backed claim that `ask` is unimplemented.
    **Not trusted as a finding** — recorded only to flag the conflict
    explicitly rather than silently picking one secondhand claim over the
    other; resolving it needs the actual docs page, still blocked.
- **Does this change the prior verdict?** No — refines the evidentiary
  picture without closing the queue entry. The practical lesson for
  `EXECUTOR_CONTRACT.md` is unchanged from 2026-10-01: don't assume a Codex
  adapter's `ask` is handled, and now additionally: **a Codex characterization
  test suite for a future adapter needs to control for the host shell/OS
  (PowerShell-vs-Bash exit-code semantics), not just Codex version** — a
  slightly sharper version of the same "per-tool-call-type characterization
  test" recommendation already logged.
- **Verdict: still unresolved as a primary-source read; the `adopt-the-warning`
  verdict for `EXECUTOR_CONTRACT.md` stands and gains one more specific
  caveat (host-shell exit-code semantics as a confound), not a new
  mechanism.** Re-attempt `developers.openai.com` directly whenever this
  session's (or a future session's) egress policy allows it.

---

## 6. New candidates spotted, not resolved — queued rather than cited from secondhand snippets

Per the task brief's own standard ("do not conclude relevance from a name or
README alone — read real source"): two arXiv papers surfaced by a search for
oracle-independence/mutation-testing methodology (explicitly in-scope per the
brief, and the only area this pass had budget left to look at after §§1–5)
looked genuinely on-topic for Law 18's own discrimination-check mechanism —
**but `arxiv.org` (and its `export.arxiv.org` mirror) returned an explicit
`403` from this session's egress proxy on every attempt**, confirmed via both
`WebFetch` (`ENOTFOUND`) and a direct `curl -v` (`CONNECT tunnel failed,
response 403`) — the same policy-block signature as §§4–5, not retried
further.

- **arXiv 2607.23002, "Adversarial Test-Hardening for AI-Written Code"** — a
  search-snippet summary describes a "pass-on-pristine validation step"
  that prunes generated tests failing on correct/unmutated code before
  trusting them as mutation discriminators, which — **if the snippet's
  characterization is accurate, not independently verified here** — sounds
  structurally close to the exact bug `scripts/governed_test.py`'s own
  `run_mutation` was patched for on 2026-09-06 (confirming the baseline/
  unmutated run passes before trusting a "discriminates" result). This is
  recorded as a candidate worth a direct read, explicitly **not** as a
  confirmed parallel — the only source for this claim is a search-engine's
  own aggregated summary of the paper, not the paper's text.
- **arXiv 2608.17214, "Oracles That Cannot Fail"** — a search-snippet summary
  attributes to it a discussion of Terragni et al. using *different*
  mutation tools for test-improvement versus test-validation specifically to
  avoid circularity — a direct hit on the word "independence" in Law 18's
  own name, if accurate. Same caveat: secondhand, not independently read.
- **Verdict for both: queued, not adopted, not even provisionally cited as
  fact anywhere else in lawkeeper's docs.** Re-attempt with direct `arxiv.org`
  access in a future pass (or via a GitHub mirror of either paper's LaTeX
  source, not searched for this pass) before treating either claim as
  checkable, per the same discipline already applied to MITRE ATLAS and
  Cedar in earlier passes before they were actually read.

---

## What this pass found nothing new on

Per the task brief's own instruction: stated plainly. Nothing this pass
surfaced changes the deny>ask>allow five-system convergence verdict from
`RESEARCH_harness_hook_mechanisms_survey.md` (§1's four-tier Claude-Code-
specific refinement is additive to it, not a contradiction, as stated
above) or the RBAC/ABAC/PEP-PDP framing from
`RESEARCH_harness_governance_survey.md` §1 — nothing this pass read bears on
either. No Falcun-relayed report was encountered or relied on this pass;
nothing here traces through a secondary research report from another repo.

## Re-check when

- `open-plugins.com` and `developers.openai.com` — both still hard-blocked
  by this session's egress proxy (confirmed by two independent failure
  signatures each, this pass and 2026-10-01); retry directly whenever a
  session's egress policy might differ, and do not substitute a
  secondhand/search-snippet account for either primary source in the
  interim.
- The exact ship date of Claude Code's `defer` value (§1) — this pass's
  "~v2.1.89, 2026-03-31/04-01" claim is secondhand (two third-party release
  trackers, not Anthropic's own changelog, which this pass's partial read
  could not locate a matching entry in). Re-attempt a full read of
  `raw.githubusercontent.com/anthropics/claude-code/main/CHANGELOG.md`
  (it is ~1.08M characters; this pass read only the first 100,000) or
  `code.claude.com/docs/en/changelog` before citing a specific version
  number as confirmed anywhere load-bearing.
- `PermissionRequest`'s precedence relative to `PreToolUse` (§2) and the
  `Elicitation`/`ElicitationResult` event pair's actual decision shape (§3)
  — both need a direct read of their dedicated sections on
  `code.claude.com/docs/en/hooks` (this pass only read the summary tables
  that mention them), before anything is built or claimed about either.
- arXiv 2607.23002 and 2608.17214 (§6) — re-attempt direct access; do not
  cite either paper's specific claims anywhere else in lawkeeper's docs
  until read directly.
