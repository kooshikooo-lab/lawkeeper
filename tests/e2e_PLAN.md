# e2e_PLAN — End-to-end test plan for lawkeeper

Status: **APPROVED** by user (build mode, "go"). Defaults applied unless user edits.

## Choices (checkboxes — single source of truth for the e2e phase)
- [x] A. keep the committed framework MVP on `opencode/framework-mvp/desktop`
- [x] B. scope = all five: own commits, bugs, commit-msg gate, pre-commit gate, conflicts
- [x] C. merge_gate is NOT broken (probe was a default-branch error); re-verified
      with divergent branches -> rc 1, `CONFLICT (content)`. Re-verify on Linux CI.
- [x] D. import order = instrument-designer first, then autonomi-code-assistant
- [x] E. green gate = pytest tests/ -q + `lawkeeper run` + system_audit + watchdog --check-laws + watchdog --check-baseline

## Acceptance (must all hold)
1. `tests/test_e2e.py` lives in `tests/` and is collected by `pytest tests/ -q`.
2. Each scenario passes on this machine (git 2.55, Windows) and on Linux CI.
3. `lawkeeper run` stays green on `lawkeeper` itself.
4. `system_audit.py` -> ALL CHECKS PASS.
5. `compliance_watchdog --check-laws` + `--check-baseline` -> OK.

## Failure reporting
New lawkeeper findings -> `docs/AI_FAILURE_PATTERNS.md` (GOVERNANCE-UPDATE commit).
Design decisions -> `docs/ARCHITECTURE_DECISIONS.md`.
