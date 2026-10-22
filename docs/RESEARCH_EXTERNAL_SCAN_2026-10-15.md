# External scan — 2026-10-15

Weekly scheduled research pass. Scope per the routine's own brief: runtime/
`PreToolUse`-style agent governance, policy-decision algebras (allow/deny/ask),
git-hook distribution/enforcement patterns, and test-governance/oracle-
independence methodology. Not Windwright's domain (acoustics/CAD) and not
Falcun's (evolutionary mutation, epistemic-claim verification) — a harness's
other features are out of scope here even when its governance mechanism is
in scope.

Per the brief, this pass re-attempted the two still-open queue items from
`docs/RESEARCH_agent_harness_landscape.md` /
`docs/RESEARCH_harness_hook_mechanisms_survey.md` before looking for anything
new: the Open Plugins hooks specification, and Codex's native hook protocol
read directly from OpenAI's own docs. **Both are still fully blocked this
pass**, same as 2026-10-01 — recorded below with the exact access attempts,
not re-padded with secondhand content to manufacture progress. Looking for
what was reachable instead of what was blocked surfaced one genuinely new,
directly-read governance mechanism this research base had not yet covered —
**GitHub Copilot's own hook system** — plus one new concrete tool relevant to
lawkeeper's open ASK-tier design question (**ccgate**). A third lead (a
TU Delft thesis on mutation-feedback-driven test-oracle generation, surfaced
by search) could not be verified at all this pass and is explicitly not
included as a finding — see "What this pass found nothing new on."

**Access note, stated up front because it shaped what got read:** this
session's egress proxy blocks `developers.openai.com`, `learn.chatgpt.com`,
`open-plugins.com`, and `docs.github.com` directly — this pass they failed
as DNS resolution errors (`getaddrinfo ENOTFOUND`) rather than the explicit
`EGRESS_BLOCKED` the 2026-10-01 pass saw for the same domains; functionally
the same policy block, a different failure surface, not a sign the policy
relaxed. `github.com` and `raw.githubusercontent.com` were reachable, same as
last pass, so everything below marked "actually read" is a GitHub-hosted
primary source (a project's own doc-source repo, a README, a LICENSE file, or
the maintainers' own issue tracker) reached through those two hosts, not the
vendor's own docs site even where that's the more obvious citation.

---

## 1. GitHub Copilot's own hook system — new entry, directly read

Not previously covered by any of the three base research docs or the
2026-10-01 scan (confirmed by grepping all four for "Copilot" before starting
— the one existing hit is GitHub Copilot's PR-review bot catching an
arithmetic error in a relayed report, unrelated to Copilot's own agent
hooks). In scope because it is a sixth independently-built implementation of
exactly the problem the hook-mechanisms survey tracks: gating a coding
agent's tool calls before they execute.

- **What was actually read:** GitHub's own documentation *source* (the
  `github/docs` repository that `docs.github.com` is built from, since that
  host itself is egress-blocked — same access pattern the 2026-10-01 pass
  used for `cedar-policy/cedar-docs`), fetched via `raw.githubusercontent.com`
  and `github.com`'s own file-tree view, both directly:
  - `content/copilot/how-tos/copilot-sdk/hooks/pre-tool-use.md` (full)
  - `content/copilot/how-tos/copilot-sdk/hooks/hooks-overview.md` (full)
  - `content/copilot/how-tos/copilot-sdk/hooks/error-handling.md` (full)
  - `content/copilot/reference/hooks-reference.md` (full) — this is the one
    that actually carries the precedence/exit-code/fail-open details; the
    three SDK-level pages above describe a different, separate mechanism
    (see next point) and do not.
  - Supporting, not load-bearing: `crocodile-labs/openmoat` issue #258 (a
    third party building a cross-harness hook adapter, read directly,
    cross-checked against the primary docs above rather than relied on
    alone — flagged per-claim below where it's the only source for a detail).
- **License:** N/A — this is the actual product lawkeeper's own design docs
  already compare against (Claude Code's hooks), not a dependency.
- **Two genuinely separate hook mechanisms under one product name — confirmed
  by reading both, not assumed from a shared "hooks" label:**
  1. **SDK-level, in-process hooks** (`hooks-overview.md`,
     `pre-tool-use.md`, `error-handling.md`): a plain language-native
     callback (`onPreToolUse(input) => output`) registered in a session
     config, not a JSON wire protocol at all. `pre-tool-use.md` confirms a
     3-way `permissionDecision: "allow" | "deny" | "ask"` output exists at
     this layer, plus `modifiedArgs` (an argument-rewrite channel, the same
     shape Omnigent's content-rewriting policies already established in the
     landscape doc) and `skipPermission` (a per-tool opt-out of the
     permission prompt entirely). Neither this page nor `error-handling.md`
     documents exit-code semantics, timeout behavior, or precedence across
     multiple hooks — confirmed by reading both directly, not inferred from
     absence in a summary.
  2. **CLI/cloud-agent-level, external hook protocol**
     (`hooks-reference.md`): a `.github/hooks/*.json`-configured, JSON-on-
     stdin/stdout wire protocol, structurally the direct analog of Claude
     Code's own `PreToolUse` hook and goose's/Hermes'/dsh's external hook
     layers already catalogued in the hook-mechanisms survey. This is the
     page that actually answers the precedence/failure-mode questions.
- **The decision model, quoted/confirmed directly from `hooks-reference.md`:**
  - Output: `permissionDecision: "allow" | "deny" | "ask"`,
    `permissionDecisionReason` (required when denying), `modifiedArgs`.
  - **Deny is unconditional and wins over everything else for `preToolUse`**:
    if any configured hook returns `deny`, the tool call is blocked — stated
    as the page's own precedence rule for this event, not reconstructed.
  - **Exit code 2 forces deny even if the hook's own stdout said `allow`** —
    the page states this as an explicit override, not a side effect: a
    command hook that exits 2 denies the call regardless of what JSON it
    printed. This is a sharper, more specific claim than Claude Code's own
    "exit code 2 overrides a matching allow rule" (governance survey §2) —
    here it overrides the *hook's own* stated verdict, not just a static
    permission rule.
  - **Every other non-zero exit is logged as a failure and the run
    continues** — *except* for `preToolUse` specifically, which the page
    states fails closed on other non-zero exits too, not only on exit 2.
  - **Timeout (default 30s) is fail-open for every event, `preToolUse`
    included** — a real, stated asymmetry: a `preToolUse` hook that crashes
    or explicitly exits non-zero blocks the call, but one that simply hangs
    past the timeout does not. This is the same fail-open-on-timeout /
    fail-closed-on-explicit-failure split already seen in Hermes'
    `shell_hooks.py` (hook-mechanisms survey §2) and goose's plugin-hook
    layer (`emit_blocking`'s "a misbehaving hook MUST NOT block"), but this
    is the first system in this research base confirmed to apply *different*
    rules to a timeout versus an explicit crash/non-zero-exit within the
    *same* event type, rather than one fail policy per hook.
  - **HTTP hooks are fail-open on network error, timeout, or a non-2xx
    response** — a third, distinct failure-mode rule for a third transport
    (command vs. HTTP), confirmed directly from the same page.
- **A real, cross-surface ASK-degradation rule, confirmed directly, not via
  the third-party issue:** `hooks-reference.md` states outright that on the
  cloud agent, `ask` is treated as `deny`, because no user is present to ask.
  This is a first-party-documented instance of exactly the "coarse,
  session-level dial decides whether the live ask is even consulted"
  pattern the hook-mechanisms survey already found in dsh, Hermes, and
  goose (§"a second pattern surfaced by all three new reads") — but those
  three each used an opt-in policy dial (`sandbox/mode`, `approvals.mode`,
  `GooseMode`); here the degradation is automatic and unconditional, tied to
  which surface is running, not a setting an operator chooses. **This is a
  cleaner, more directly relevant precedent for lawkeeper's own open
  question** (the landscape doc's `AUDIT:`-marker-missing "pause and ask a
  human" case, and what should happen when lawkeeper's planned `PreToolUse`
  gate runs somewhere headless, e.g. CI, with no human available to answer
  an ASK) than any of the three opt-in dials already catalogued: "ask
  degrades to deny when the execution surface structurally has no human in
  the loop" is a defensible default lawkeeper can point at a sixth, shipped
  system for, not invent from scratch.
- **The one detail that needed the third-party issue to confirm, flagged as
  such rather than stated as directly read:** `hooks-reference.md`'s own
  precedence language for `preToolUse` only states "any `deny` wins" — it
  does not explicitly rank `ask` against `allow` in that same sentence.
  `crocodile-labs/openmoat#258` (a third party's own adapter-build issue,
  read directly but not GitHub's own documentation) states "the most
  restrictive wins (deny, then ask, then allow)" for the *VS Code* surface
  specifically — plausible and consistent with every other system in this
  research base, but this specific three-way ranking claim rests on a
  third party's issue, not GitHub's own primary text, and is logged at that
  evidentiary tier rather than folded into the directly-read bullet above.
- **Does this change the five-system convergence finding?** Extends it, with
  a real qualification. Counting Claude Code, Omnigent, dsh, Hermes, and
  goose (hook-mechanisms survey's closing tally) plus GitHub Copilot now
  makes **six** independently-built systems whose `preToolUse`-equivalent
  gate treats `deny` as an unconditional, order-independent win — but
  Copilot's own primary doc is the first in this set to leave the
  `ask`-vs-`allow` half of the ranking *undocumented* at the primary-source
  level (only deny's precedence is stated outright); the full three-tier
  claim for Copilot specifically rests partly on the third-party issue, not
  on GitHub's own text. Recorded honestly rather than rounded up to "a sixth
  full confirmation."
- **Verdict: adopt-the-design, not a dependency — specifically the
  ask-degrades-to-deny-when-headless rule and the per-failure-mode-not-
  per-hook policy (timeout vs. crash vs. HTTP-error each get their own fail
  rule, not one blanket fail-open/closed setting).** Both are concretely
  applicable to lawkeeper's own `gate_pretooluse.py` design the moment it
  needs to run somewhere a human isn't present to answer an ASK (CI, a
  scheduled cloud session like this one) — "degrade ask to deny, not to
  allow, when no human is reachable" is now a citable default from a sixth
  shipped system, and "a hook that times out is treated differently from one
  that crashes" is a real, finer-grained failure-mode model worth checking
  `gate_pretooluse.py`'s own current behavior against directly (not done
  this pass — a concrete follow-up, not a speculative one).

---

## 2. ccgate (`tak848/ccgate`) — new candidate, an LLM-as-PDP gateway across three harnesses

Surfaced while searching for Codex's own hook docs (see §3) — a real,
working tool addressing exactly the "how should an ASK-tier decision
actually get adjudicated" question the landscape and governance surveys
both flagged as open for lawkeeper (the `AUDIT:`-marker-missing case), via a
mechanism neither survey's existing entries cover: an LLM call, not a
deterministic rule language (Omnigent's CEL) or a hardcoded pattern
classifier (Hermes' `HARDLINE_PATTERNS`).

- **What was actually read:** `tak848/ccgate`'s own `README.md` and `LICENSE`,
  both fetched and read directly via `raw.githubusercontent.com` (not the
  `pkg.go.dev` mirror page alone, which was read first but then verified
  against the actual repo source).
- **License:** MIT — confirmed directly from the repo's own `LICENSE` file
  ("Copyright (c) 2026 tak848").
- **The actual mechanism:** a `PermissionRequest`-style hook plugged into a
  host coding agent's own hook point. When the host asks for a permission
  decision, ccgate hands the tool name, tool input, git context, and (for
  Claude Code specifically) permission mode and recent transcript to an LLM
  (Claude Haiku by default; OpenAI, Gemini, and compatible proxies also
  supported), alongside natural-language `allow`/`deny`/`environment` rules
  written in jsonnet config (layered: embedded defaults → global config →
  untracked project-local config). The LLM returns one of three verdicts:
  `allow`, `deny` (with an optional message), or `fallthrough` — the last
  one meaning "not confident, hand back to the host's own normal prompt,"
  not a fourth terminal state.
- **The composition rule with the host's own permission system, confirmed
  directly from the README, not assumed:** ccgate is consulted **only**
  when the host's own static permission rules don't already resolve the
  request — it never overrides a decision the host's own allow/deny rule
  table would have made on its own. Claude Code's `settings_permissions`
  are passed to the LLM as a *hint*, explicitly not as a whitelist the LLM
  must obey.
- **The headless/CI-equivalent case, directly relevant to lawkeeper's own
  open question:** `fallthrough_strategy` governs what happens on LLM
  uncertainty — `ask` (default, shows the host's own interactive prompt),
  `deny` (the README's own explicit recommendation for unattended runs), or
  `allow` ("use sparingly," per the README's own wording). A missing/invalid
  API key also degrades to `fallthrough`, by explicit design, so a
  provider misconfiguration cannot silently widen what gets allowed. This is
  a third, independently-arrived-at instance of "default to deny, not allow,
  when nobody's there to adjudicate the ambiguous case" — same shape as
  Copilot's cloud-agent ask→deny rule above and dsh's `approval/policy:
  'never'` (hook-mechanisms survey §1), now from a tool whose entire job
  *is* adjudicating the ambiguous case, not just degrading gracefully when
  it can't reach one.
- **Supported harnesses, confirmed from the README, with real caveats
  attached rather than listed as uniform support:** Claude Code (most
  complete — plan-mode handling, transcript context, though the README
  itself notes plan-mode correctness depends on prompt wording alone, not a
  structural guarantee), OpenAI Codex CLI (requires `hooks = true` under
  `[features]`; `apply_patch` and MCP tool calls get no referenced-path
  context), and Devin CLI (hooks read from project/user config; tool names
  differ from Claude's, handled as a separate mapping, not inferred).
- **One concrete thing lawkeeper could adopt, or not:** not a dependency —
  ccgate is a live, uncontrolled LLM call in the decision path for every
  ambiguous permission request, which is a meaningfully different trust
  model from lawkeeper's own guard scripts (deterministic Python predicates)
  and from Omnigent's CEL (sandboxed, side-effect-free, terminating by
  construction). The **directly transferable idea** is narrower and cheaper
  than adopting the tool: ccgate is a real, working precedent that "defer an
  ambiguous ASK-tier case to an LLM judgment call, but bias the *fallback*
  for when that judgment itself can't be reached toward deny, never allow"
  is a viable design for lawkeeper's own `AUDIT:`-marker-missing case
  *if* lawkeeper ever wants that specific check adjudicated by something
  more flexible than a fixed regex — worth logging as an explicit
  alternative to Omnigent's CEL entry next to it, not a replacement for it.
  **Verdict: not-applicable as a dependency (different trust model, not
  lawkeeper's current problem), adopt-the-fallback-bias-idea only** —
  deny-not-allow on provider/LLM failure is the one piece worth carrying
  forward regardless of whether lawkeeper ever uses an LLM-adjudicated tier
  at all.

---

## 3. Codex's native hook protocol — still blocked, no primary-source progress this pass

- **Prior status (2026-10-01):** substantially upgraded from a single
  third-party comment to OpenAI's own issue tracker plus a citation-backed
  independent analysis, but explicitly *not* closed — still short of this
  doc's own primary-source bar (OpenAI's own docs page, read directly).
- **What was attempted this pass:** `developers.openai.com/codex/hooks` and
  `/hooks.md`, and `learn.chatgpt.com/docs/hooks` — all three failed as DNS
  resolution errors this pass (`getaddrinfo ENOTFOUND`), the functional
  equivalent of 2026-10-01's `EGRESS_BLOCKED` for the same hosts, not a sign
  the block lifted. `github.com/openai/codex`'s own `docs/config.md` was
  re-checked directly (still reachable) and still only confirms hooks exist
  as a feature (the `allow_managed_hooks_only` admin setting) without
  documenting the wire format — same finding as last pass, re-verified
  rather than assumed still true.
- **What this pass found that's new, but still secondhand relative to
  Codex's own source, and not folded into the verdict below as if it were
  primary:** a search surfaced a third-party guide
  (`codex.danielvaughan.com`, dated April 2026) repeating the same claim
  `i9wa4/dotfiles#378` already established last pass ("ask" accepted
  syntactically, not implemented, returns `Failed`) — not independently
  fetched and read this pass, so it adds no new evidentiary weight, only a
  second party repeating the same prior finding. ccgate's own README (§2)
  independently corroborates that Codex CLI hooks are real and configurable
  (`hooks = true` under `[features]`) without describing the wire format
  either way.
- **Verdict: unchanged from 2026-10-01 — stays queued.** Re-attempt
  `developers.openai.com`/`learn.chatgpt.com` directly whenever a future
  session's egress policy might differ; do not treat the repeated
  third-party guide as closing this entry.

---

## 4. The Open Plugins hooks specification — still blocked, no change

- **Prior status:** queued since the hook-mechanisms survey (2026-09-06);
  still blocked as of 2026-10-01 (`EGRESS_BLOCKED`, not retried per policy).
- **What was attempted this pass:** `open-plugins.com/agent-builders/
  components/hooks` directly, and a fresh search for a GitHub mirror or
  cached copy. The direct fetch failed as `getaddrinfo ENOTFOUND` this pass
  (same functional block, different failure surface than 2026-10-01's
  explicit `EGRESS_BLOCKED`). The search did **not** surface the
  previously-identified decoy spec again (`agent-plugins.org` / "Agent
  Plugins Specification") this time — instead it surfaced several pages
  about Claude Code's and GitHub Copilot's *own* plugin-hook formats
  (already covered: Claude Code in the base surveys, GitHub Copilot in §1
  above), none of which are the open-plugins.com spec goose cites.
- **Verdict: unchanged — stays queued.** No new access path or mirror found
  this pass. Re-attempt whenever egress policy might differ; continue not
  substituting a same-sounding but different spec for it.

---

## What this pass found nothing new on

Per the task brief's own instruction: stated plainly rather than padded.

- **Test-governance/oracle-independence methodology:** a search for recent
  work on oracle independence / mutation-feedback test generation surfaced
  one lead — a TU Delft repository file describing a multi-agent oracle-
  generation workflow using PITest mutation feedback — but the fetch tool
  could not reach `repository.tudelft.nl` at all this pass (`getaddrinfo
  ENOTFOUND`), so this is **not reported as a finding**: nothing about it
  was independently read, only a search-snippet characterization, which is
  exactly the standard this research base's own discipline rules out as a
  basis for a verdict. Recorded here only so a future pass doesn't need to
  re-discover that the lead exists, not as evidence of anything about it.
  Separately: lawkeeper's own Law 18 mechanism had no new external
  comparison point surface this pass beyond what 2026-10-01 already logged
  (mutmut, now actually adopted into lawkeeper's own CI per `git log`
  commits #37/#39 — the cosmic-ray comparison that scan's own entry flagged
  as not-yet-done is now lower-priority than it was, since the gap it would
  have informed is already closed by a working, merged mutmut integration;
  not pursued this pass).
- **Policy-decision algebra:** no new system beyond GitHub Copilot (§1)
  surfaced this pass; the deny-always-wins / ask-degrades-under-no-human
  patterns GitHub Copilot and ccgate both independently confirm are
  extensions of, not departures from, the six-system (now) convergence
  already on record.
- No Falcun-relayed report was encountered or relied on this pass; nothing
  here traces through a secondary research report from another repo.

## Re-check when

- `developers.openai.com` / `learn.chatgpt.com` (Codex hooks, §3) and
  `open-plugins.com` (§4) — both still blocked by this session's egress
  policy on every attempt to date (three sessions running now); re-attempt
  directly whenever a future session's policy might differ, rather than
  continuing to substitute secondhand sources for either.
- `gate_pretooluse.py`'s own current fail-open/fail-closed behavior on
  timeout vs. explicit hook failure — GitHub Copilot's per-failure-mode
  split (§1) is a concrete, checkable comparison point this pass identified
  but did not itself check lawkeeper's own gate against; worth a direct
  read of `gate_pretooluse.py`'s actual timeout/exception handling next to
  this entry before deciding whether to change anything.
- The TU Delft oracle-generation lead above — re-attempt
  `repository.tudelft.nl` directly if a future session's egress differs;
  do not cite it from the search snippet alone.
