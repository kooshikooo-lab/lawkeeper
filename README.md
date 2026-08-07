# lawkeeper

**Constitution-as-code governance for agentic + vibe-coded projects.**

`lawkeeper` gives any project — especially ones built by non-coders vibing with AI —
a small, enforceable constitution that lives in git and is guarded by the git layer
itself. It is not docs you read and forget; it is **mechanical policy that blocks
bad commits and bad branches even when the agent misunderstands, is rash, or is
just a large language model that confidently hallucinated a merge.**

## Why this exists
Today's AI coding agents and vibe coders ship fast but have **no guardrails beyond
secret scanners and commit-format checks.** Nothing prevents a vague instruction
("clean up branches") from deleting the trunk, or a blind merge from importing
20 conflicts, or an agent from committing unverified work. `lawkeeper` adds the
missing layer: **a project constitution enforced mechanically at commit, push,
and CI time, that also audits itself.**

## What it provides (one command)
```
pip install lawkeeper        # or: pip install -e .
lawkeeper init               # into an existing git project
```
This scaffolds:
- `docs/AI_CONSTITUTION.md` — 16 enforceable laws (architecture, duplication,
  physics one-source-of-truth, audit-before-commit, branch governance,
  system self-audit...).
- `scripts/git-hooks/{pre-commit,commit-msg,pre-push}` + `scripts/*guard*`
  — the enforcement layer.
- `.github/workflows/governance-guard.yml` — the CI backstop.
- `scripts/system_audit.py` — the system audits its own guards.
- `tests/test_guard_scripts.py` — tests for the guards.
- `AGENTS.md`, `COMPLIANCE_CHECK.md`, `docs/REMINDERS.md`... starter docs.

Run it once; the project is governed. Non-coders keep coding; the system keeps
everyone compliant.

## The enforcement stack (Law 16 — defense in depth)
1. **Local git hooks** (`pre-commit`, `commit-msg`, `pre-push`): block ungoverned
   commits, unauthorized edits to the constitution, provisional work without an
   `AUDIT:` marker, and — crucially — any **deletion or force-push of a canonical
   branch** (the "stale = safe to delete" failure mode that breaks repos).
2. **CI backstop** (`governance-guard.yml`): re-runs the same checks on every push/PR
   so a machine that disabled local hooks is still stopped.
3. **Self-audit** (`system_audit.py`): verifies the other two layers are actually
   active (hooks wired, laws parse, baseline current, guards importable), so a
   dead guard is caught — not trusted on faith.

## Commands
| Command | What it does |
|---|---|
| `lawkeeper init [DIR]` | scaffold full governance into a project |
| `lawkeeper run` | run the constitution laws against the current repo (exit non-zero on FAIL; `--json`, `--law N`, `--quiet`) |
| `lawkeeper status` | show which enforcement layers are active (read-only) |
| `python scripts/merge_gate.py <base> <head>` | predict merge conflicts without touching the worktree |
| `python scripts/guard_branch.py --audit` | report Law 15 branch-topology violations |
| `python scripts/system_audit.py` | verify the whole enforcement stack is alive |

## Running the laws
`lawkeeper run` loads every portable Law from `guardrail/laws/` (auto-discovered by
`guardrail.core.registry`) and checks the repo. On `lawkeeper` itself it is green:

```
[PASS] Law 1  - README.md declares project purpose and structure.
[PASS] Law 9  - docs/ARCHITECTURE_DECISIONS.md records architectural decisions.
[PASS] Law 12 - AGENTS.md present.
[PASS] Law 14 - Commit-audit validators present and wired.
[PASS] Law 15 - Branch 'opencode/<topic>/<machine>' is feature (compliant).
[PASS] Law 16 - Enforcement system present: guards, tests, and config.

6 checks: 6 pass, 0 warn, 0 fail
```

`--json` emits a machine-readable report; `--law N` runs a single law; `--quiet`
returns only the exit code (non-zero if any Law FAILS).

## Non-coder quickstart
```bash
pip install lawkeeper
lawkeeper init .                       # one command — your project is now governed
python scripts/install_hooks.py        # installs the git hooks
git add -A
git commit -m "chore: lawkeeper bootstrap" -m "GOVERNANCE-UPDATE"
python scripts/system_audit.py         # must say ALL CHECKS PASS
git push && open a PR                  # branch protection + CI backstop guard main
```
Now any agent you send at the repo is mechanically constrained: it cannot delete
the trunk, cannot merge blind, and cannot ship without its own guards passing.

## Design note: assemble, don't reinvent
This project deliberately reuses the governance infra already battle-tested in
[`kooshikooo-lab/instrument-designer`](https://github.com/kooshikooo-lab/instrument-designer)
(the 16-law constitution, the git-layer branch guard, the merge gate, the self-audit)
rather than building another runtime policy engine. Existing open-source agent
governance (Microsoft Agent Governance Toolkit, OpenPolicyAgent/Rego,
Guardrails AI, OpenGuardrails) focuses on *runtime/agent behavior*. Few provide
*git-layer, self-auditing* governance that works for distributed two-machine (or
human+agent) vibe teams. That's the gap `lawkeeper` fills.

## License
MIT.
