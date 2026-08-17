# Compliance Check Procedure

Run at **session start**, then on every **trigger**:
(Timer every 15 min · before every code change · after every test run · on drift)

## BOOT SEQUENCE (summary)
1. Read `docs/AI_CONSTITUTION.md`; state which laws apply.
2. Read architecture docs (`ARCHITECTURE.md`, `ARCHITECTURE_DECISIONS.md`, `CODING_STANDARDS.md`).
3. Identify your subsystem.
4. Search before building (Law 3).
5. Produce an implementation plan.
6. Implement; run this checklist on every trigger.

## CHECK 1 — Constitution refresh
Recite the laws from `docs/AI_CONSTITUTION.md`. State which apply.

## CHECK 1c — Pre-commit audit (Law 14)
- Re-read the constitution; state applicable laws.
- Tests for the change passed (or coverage added).
- `git diff --cached` reviewed line-by-line.
- No silent killers (units, enums, hardcoded physics/constants, off-by-one).
- No scratch files staged.
- Commit message declares `Tests:` or `Verification:`.

## CHECK 1d — Compliance watchdog (Law 14)
```
python scripts/compliance_watchdog.py --check-laws
python scripts/compliance_watchdog.py --check-baseline
```

## CHECK 1e — System self-audit (Law 16)
The guards must not be trusted on faith — a broken guard gives false confidence.
Before committing to a canonical branch or `main`:
```
python scripts/system_audit.py                       # all enforcement layers active
python -m pytest tests/test_guard_scripts.py -q       # the guards' own tests
```
Before any cross-machine merge:
```
python scripts/merge_gate.py <base> <head>           # conflict preflight
```
PASS = audit exits 0 and meta-tests pass and (clean merge or a rehearsed staging).
FAIL = fix the guard or the violation first.

## CHECK 1b — Dependency integrity (Law 13)
Every declared dependency is installed and importable; every `skip` is justified.

## CHECK 3 — Drift | CHECK 4 — Duplication | CHECK 5 — Self-test
Compare action vs plan; reuse existing code; watch for architecture violations.

## Logging
```
COMPLIANCE: passed | subsystem: <name> | trigger: <timer|before-code|after-tests>
```
## Violation of this procedure
Skipping compliance checks is itself a compliance failure. Log in `AI_FAILURE_PATTERNS.md`.
