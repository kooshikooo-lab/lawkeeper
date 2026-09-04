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

### If things go wrong
- `system_audit.py` FAIL: fix the guard or the violation before any further commit.
- Merge conflict: rehearse on a `merge/<topic>` branch via `merge_gate.py`, resolve, verify, promote.
