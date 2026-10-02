## AGENTS.md — Working Agreement

Governed by `docs/AI_CONSTITUTION.md` (16 Laws). Enforcement layers:
local git hooks + CI `governance-guard.yml` + `scripts/system_audit.py`. The guards
themselves are tested by `tests/test_guard_scripts.py`.

### Step 0 (session start): sync
- Install hooks: `python scripts/install_hooks.py`
- Verify: `python scripts/system_audit.py` (must PASS)
- Before any cross-machine merge: `python scripts/merge_gate.py <base> <head>`
- On any Law violation: log it in `docs/AI_FAILURE_PATTERNS.md`

### Environment
- Repo: `kooshikooo-lab/lawkeeper` (remote: `origin`)
- Branch naming: Law 15 in `docs/AI_CONSTITUTION.md`. `main` (trunk), `opencode/main/<machine>` (canonical, permanent), `agent/<topic>/<machine>` (feature, ephemeral — changed 2026-09-04 from `opencode/<topic>/<machine>`, which named a specific tool; legacy `opencode/<topic>/<machine>` branches remain valid), `merge/<topic>` (merge staging, ephemeral).
- `origin/HEAD` must point at `main`.

### Coordination
GitHub Discussion #23 is the durable team channel. Real-time messages go to it;
machines read before acting (Law 12). Unacknowledged requests are re-sent.

### Working with the user (standing rule, user 2026-09-28)
Same rule as falcun's AGENTS.md, set by the user for every repo.
1. Collect every decision that is genuinely the user's (permissions, sends,
   commits/merges, spending, direction) into **one clickable multi-select menu**
   (AskUserQuestion, `multiSelect`) at the end of a turn, so the user can tick
   several items, or all, at once.
2. Each option gets a short label and plain-language context: what it is, why it
   matters, what happens if chosen. Mark recommendations **"(Recommended)"** and
   list them first. Always state a recommendation the user can deny; never just
   ask "what do you want?".
3. No loose questions buried in prose.
4. **Agents are the doers.** Recommend; once approved, the owning session does it
   and reports. Never hand the user a merge or a step. Only what the permission
   system truly blocks goes back to the user, with the reason and one exact action.
5. Technical choices are researched and decided by the agent, not offered to the
   user as a question.

This changes how decisions are *asked for*, not who may make them: the
constitution and every approval gate still apply.

### If things go wrong
- `system_audit.py` FAIL: fix the guard or the violation before any further commit.
- Merge conflict: rehearse on a `merge/<topic>` branch via `merge_gate.py`, resolve, verify, promote.
