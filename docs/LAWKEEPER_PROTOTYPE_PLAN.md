# Lawkeeper Downloadable Prototype — Plan

Real, concrete plan for a downloadable lawkeeper prototype: your own
Anthropic API key, real agentic coding capability, lawkeeper's existing
governance apparatus wrapped around it from the start -- and, as a real
first test, lawkeeper governing its own build.

## The key finding that makes this realistic, not aspirational

Anthropic's **Agent SDK** (`pip install claude-agent-sdk`, real, free,
open-source, confirmed 2026) provides the entire agentic engine lawkeeper
would otherwise need to build from scratch: the tool-use loop (read/
write/edit files, run commands, search the web), sessions, permissions,
subagents, MCP support -- and, critically, **the same hook system
already used tonight** (`scripts/claude_stop_hook.py`) and **the same
`.claude/`-directory skill/memory loading** already set up in this repo
(`.opencode/skills/governance-recall/`).

This changes the honest scope estimate a lot: building the agent loop
from scratch would have been a multi-month undertaking, comparable to
what Claude Code/Aider/similar tools already are. Building a
*governance layer wrapped around an existing, real agent loop* is a
real, bounded project -- most of the hard part (the agent loop itself)
is already solved and free to use.

**Real, confirmed permission for exactly this use case**: Anthropic's
own Agent SDK docs state third-party products must authenticate via API
key, not claude.ai login/rate limits -- this is the sanctioned,
intended pattern for what you're describing, not a workaround.
**Real branding constraint**: can't call the product "Claude Code" or
use Claude Code branding; "Lawkeeper, Powered by Claude" is explicitly
listed as permitted.

## Architecture

```
User's ANTHROPIC_API_KEY
        |
        v
Claude Agent SDK (real engine: tool loop, sessions, hooks, MCP)
        |
        v
Lawkeeper governance layer:
  - Stop hook (Law 22 hedge-phrase check) -- adapt claude_stop_hook.py
    to the SDK's own hook registration, likely near-direct port
  - Pre-action checks (Law 14/18-style: audit before commit, theory
    cards) -- wired via PreToolUse-equivalent hooks the SDK supports
  - Constitution loaded as real context, the same way `.claude/`
    memory already loads today -- AI_CONSTITUTION.md becomes part of
    every session's real system context, not a separate document
    nobody reads
  - Existing scripts (compliance_watchdog.py, orphan_scan.py,
    consensus_review.py, literature.py) available as real tools/skills
    the agent can invoke, same as any other project
        |
        v
`lawkeeper agent` (new CLI command, extends the existing `lawkeeper`
entry point already real and pip-installable)
```

## Real MVP scope, staged

### Stage 1 -- Prove the integration works at all
- New module: `src/guardrail/agent.py`, a thin wrapper that starts a
  real Agent SDK session pointed at the current directory, with:
  - `ANTHROPIC_API_KEY` read from the environment (standard, no new
    mechanism needed)
  - Lawkeeper's constitution + relevant docs loaded as real context
  - The Stop hook ported to the SDK's real hook registration format
- New CLI subcommand: `lawkeeper agent "<task>"` -- runs one real,
  governed agentic session.
- **Real success criterion**: run it on a small, real, bounded task in
  this very repo and confirm (a) it actually reads/edits real files,
  (b) the ported Stop hook actually fires and blocks a deliberately
  triggered hedge-phrase response, the same live test attempted earlier
  tonight but inside a context where it's confirmed to actually work
  (a bare Agent SDK session isn't the same managed-environment surface
  that blocked the hook from firing in this Claude Code session).

### Stage 2 -- Port the real, existing governance checks
- Pre-commit-style checks (theory cards, commit message validation,
  compliance baseline) wired as real PreToolUse-equivalent hooks, not
  reimplemented -- these already exist as real, tested Python functions
  in `scripts/`; the work here is wiring, not rewriting.
- Real verification: run the SAME test suite that already exists
  (`tests/`) against the wrapped agent's actual behavior, not just the
  standalone scripts.

### Stage 3 -- Real packaging for "downloadable"
- Extend the existing, already-real `pip install lawkeeper` +
  `lawkeeper init` (proven via `test_init_smoke.py`'s real wheel-build
  test) to also install the Agent SDK as a dependency and expose
  `lawkeeper agent`.
- Real, honest open question, not yet decided: does "downloadable"
  mean a `pip install` package (lowest effort, requires Python
  familiarity) or a real packaged application (a `.exe`/`.AppImage`/
  similar, no Python knowledge required, more distribution work)? The
  platform-cooperative vision (letting non-technical members join)
  points toward the latter eventually, but a `pip install`-based CLI
  is the honest, fast first real milestone.

### Stage 4 -- Dogfood: lawkeeper governs its own next commit
Once Stage 1-2 produce something real and working, use it to make a
real, small, genuine improvement to lawkeeper itself -- governed by its
own Stop hook, its own pre-commit checks, its own constitution as live
context. This is the real "lawkeeper builds itself" test the user
asked for, and a genuine, meaningful validation that isn't just a
synthetic demo task.

## What this plan deliberately does not claim

This is a real, achievable prototype path, not a claim that Stage 3's
"real packaged application" (the fuller platform-cooperative vision) is
close or simple -- that's real, separate, later work. The honest,
concrete near-term deliverable is Stages 1-2: a working, governed agent
CLI, provable in days, not months, given how much of the hard
infrastructure (the agent loop itself, via the SDK; lawkeeper's own
governance apparatus, already built) already exists.

## The fuller vision, restated accurately (2026-08-21)

Real expansion from the user, worth capturing precisely rather than
losing in chat scrollback:

**Two related but distinct products, not one:**
1. **Lawkeeper as a coding platform** — resembling Claude Code, with
   governance built in from the start. This is what Stages 1-4 above
   build toward.
2. **A separate, general-purpose product** — a project planner/
   organizer (not coding-specific), with an *optional* AI plugin --
   models/agents can be enabled or left off entirely, user's choice.
   Real, distinct scope from the coding platform; not yet designed,
   flagged here so it isn't lost, not attempted in this plan's Stages.

**The non-negotiable design principle for both:** privacy-first,
architecturally and legally, not as a marketing claim. Two real,
separate guarantees, kept distinct on purpose (conflating them would
promise something the architecture can't keep):

- **What lawkeeper itself can genuinely, architecturally guarantee**:
  it never mines, retains, or resells user data beyond what a given
  request needs. This applies regardless of which model backend is
  used, cloud or local. The contract terms need to be specific and
  unambiguous enough that a breach would be trivially, legally
  provable — "your data is your own," written so a violation is a
  clear, winnable breach-of-contract case, not hedged boilerplate.
  Real, already-established requirement from an earlier session (see
  the `voice-input-offline-privacy` memory) — this generalizes that
  same requirement from voice input specifically to the whole
  platform.
- **What "no cloud dependency" actually requires**: Claude, GPT,
  Gemini, and Kimi are all cloud-hosted — calling any of them means a
  real network request to their servers, unavoidably. This is a
  different, narrower claim than the one above, and the two must not
  be conflated in how this gets described to users. The honest design:
  cloud-API models are offered as an explicit, opt-in choice with the
  airtight data-handling contract above; a genuine local/offline model
  option (connecting to tonight's earlier local-fine-tuning
  discussion, and [[ai-independence-goal]]) is the real answer for
  anyone who wants zero cloud dependency specifically, not something
  the cloud-model path can honestly claim to already be.

**Adaptive, but only because it's genuinely safe:** the AI should
adapt to the user (matching the already-logged `adaptive-assistant-
skill-vision` memory), and the user should be able to trust that
adaptation specifically *because* the privacy guarantee is airtight —
adaptive personalization means remembering things about the user,
which is exactly the category of data that most needs the strongest,
most legally concrete guarantee to be trustworthy. The privacy
architecture isn't a separate feature from the adaptive one; it's the
precondition that makes the adaptive one safe to want.

## Real, open items before Stage 1 starts
- Read the Agent SDK's real hooks documentation in full
  (`code.claude.com/docs/en/agent-sdk/hooks`) to confirm the exact
  registration format before porting `claude_stop_hook.py` -- not yet
  done, real next step.
- Confirm the Agent SDK's real Python package name/install command
  works cleanly in this environment (`pip install claude-agent-sdk`,
  requires Python 3.10+) -- not yet tested here.
- Read Anthropic's Commercial Terms of Service in full before any
  plan to distribute this beyond personal/testing use -- real,
  necessary step for the platform-cooperative vision specifically, not
  optional legal boilerplate to skip.
