# Architecture Review — `src/guardrail/` and its shipped surface (2026-09-04)

Phase D of `docs/QUALITY_AND_GOVERNANCE_IMPROVEMENT_PLAN_2026-09-04.md`,
requested directly by the user. Every finding below is verified by
reading the real code and grepping the real import graph on this branch
— not impression, not a rubric applied without checking.

## Method

Mapped `src/guardrail/`'s real file sizes, then the actual internal
import graph (every `from guardrail...`/`from .` line, including
function-local/deferred imports in `cli.py`), then cross-checked every
module against Law 21 ("a capability with no consumer is a bug, not
neutral") by grepping for real callers outside its own test file, then
checked what `test_template.py` actually enforces vs. what it merely
lists, then compared the shipped template's contents against the
package's own stated purpose.

## What's genuinely good — stated plainly, not as a courtesy

- **Clean, one-directional layering.** `core/`, `laws/`, and `memory/`
  never import `cli.py` or `config.py` — verified by grep, zero hits.
  `cli.py` is the outer composition layer that reaches into the inner
  ones (mostly via deferred imports, a reasonable CLI-startup-cost
  choice, not a smell). No circular imports found anywhere in
  `src/guardrail/`.
- **`scan_config.py` is real, working dependency inversion** — one
  shared resolver used by 4+ scripts instead of N separately-hardcoded
  copies. It exists specifically because that duplication already
  caused a bug once; it's the "right" pattern already present in this
  codebase, not a suggestion from outside.
- **The shipped package itself is small and focused**: 1,948 lines
  across `src/guardrail/`, cleanly separated into `core/` (primitives +
  runner + registry), `laws/` (one file per law), `memory/` (provider
  abstraction + 2 implementations), plus `cli.py`/`config.py`/`choices.py`
  as flat top-level modules where a subpackage would be overkill.

## Real problems found

### 1. Two fully-built, fully-tested modules have zero real consumers

`src/guardrail/executor.py` (Task/ExecutorResult/Executor protocol +
SubprocessExecutor, ratified via ADR-007) and `src/guardrail/agent.py`
(Agent SDK Stage-1 Stop-hook integration) are each exercised only by
their own test file (`test_executor.py`, `test_agent.py` — 11 and 10
tests respectively, all passing). Grepped the entire tree for any other
import of either module: **none exist.** `cli.py` never references
`executor` or `agent`; nothing in `core/` wires them in.

This was honest at the time each was built — the executor's own commit
says "the OpenAIExecutor backend and the ExecutorResult→CheckResult
adapter remain genuinely PLANNED, not built," and `agent.py`'s own
docstring calls it Stage 1 of a 4-stage plan. But weeks have passed and
neither has a consumer today. This is this project's **own Law 21**,
unapplied to its own code: a real, tested capability sitting unused is
a bug to track, not neutral background. Concretely, every
`pip install lawkeeper` ships both modules (they're top-level package
files, not template-only) — real shipped surface area, and in
`agent.py`'s case a real optional dependency (`claude-agent-sdk`)
declared for a feature nothing calls yet.

**Not fixed here** — removing or wiring in code is a real judgment call
(is Stage 2 actually planned soon, or should this be pulled until it
is?), not something to decide unilaterally mid-review.

### 2. A mechanical sync check that's declared but not fully enforced

`tests/test_template.py`'s `ROOT_SCRIPT_FILES` list names 9 files that
are supposed to stay byte-identical between the dev repo and the shipped
template. Only 6 have an actual test method calling `_check()` on them.
**`install_hooks.py`, `guard_governance.py`, and `validate_commit_msg.py`
are listed but never actually checked.**

Checked all three directly: `guard_governance.py` and
`validate_commit_msg.py` happen to still be in sync (verified by real
`diff`, byte-identical) — lucky, not verified by anything mechanical.
**`install_hooks.py` has already drifted for real**: the dev copy has an
entire `install_claude_stop_hook()` function (registers
`scripts/claude_stop_hook.py` into `.claude/settings.json`) that the
shipped template copy does not have. In this specific case the omission
is actually *correct* — `claude_stop_hook.py` itself isn't shipped
either, so a consuming project doesn't get a Stop hook pointing at a
missing file — but that correctness is accidental, not something any
test currently verifies, and the next edit to either copy has nothing
stopping it from breaking that by accident.

**Cheap, safe, mechanical fix available:** add the 3 missing
`_check()`-based test methods (matching the existing pattern exactly).
Low risk, high value — this is the kind of gap the project's own
tooling is built to prevent, just not yet applied to its own meta-test.
Not applied in this pass since it's a distinct, reviewable change from
the architecture read-through itself; flagging as a ready-to-approve
follow-up.

### 3. The shipped template's scope doesn't match the package's stated purpose

`pyproject.toml` describes this project as "Constitution-as-code
governance for agentic + vibe-coded projects." What `lawkeeper init`
actually installs into a *consuming* project
(`src/guardrail/template/scripts/`) includes `ai_review.py` and
`consensus_review.py` (multi-model LLM review orchestration — calls
OpenRouter/Claude CLI, not governance enforcement) and `team_chat.py`
(cross-agent chat coordination). None of these check or enforce
anything; they're general-purpose tools that happen to live in this
repo.

Meanwhile, tools that *are* squarely about governance/compliance
(`mine_failure_patterns.py`, `code_compliance_checker.py`,
`adversarial_review_checker.py`) are deliberately kept dev-only, not
shipped.

This split doesn't read as a deliberate product-boundary decision — it
reads like whatever ended up in `template/` during past syncs. It's the
concrete, code-level version of the "module vs. tool-builder"
architecture question already raised earlier this session (and
researched by Falcun separately): right now the shipped product *is*
both a governance framework and a bundle of personal LLM-orchestration
tools, without that having been a stated choice. A consuming project
running `lawkeeper init` today gets tools whose only real dependency is
"this happened to be useful to the original author," alongside the
actual governance mechanism.

**Not fixed here** — this is exactly the kind of directional decision
that needs your call, not mine: keep the bundle as-is (and say so
explicitly in the README), or split `ai_review.py`/`consensus_review.py`/
`team_chat.py` into a separate, optional package/template so
"governance" and "agent-coordination utilities" are two honestly-named
things instead of one blurred one.

## Summary table

| Finding | Severity | Fix available now? |
|---|---|---|
| `executor.py`/`agent.py` unconsumed (Law 21) | Real, shipped dead weight | No — needs a decision: wire in, or pull |
| `install_hooks.py` template drift, unenforced | Real, currently harmless by luck | Yes — add the missing test, low risk |
| `guard_governance.py`/`validate_commit_msg.py` unenforced | Latent risk, no drift yet | Yes — same fix, same pattern |
| Template scope vs. stated purpose | Real, no drift risk, but a real product-identity gap | No — needs your directional call |

## Recommendation

Approve the one safe, mechanical fix (item 2's missing test methods) and
I'll make it immediately. The other two are real findings but genuinely
your call, not mine to decide inside a review.
