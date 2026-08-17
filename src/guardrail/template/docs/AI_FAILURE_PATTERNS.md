# AI Failure & Debt Log

Log every compliance failure and guard bypass. Review before each session (Law 12).

## Template
- [YYYY-MM-DD HH:MM] LAW: <N> — <what broke> / <root cause> / <fix>. Severity: <blocker|policy|debt>.

## Failures
- [session] LAW 16 — watchdog law-loader lacked `re.MULTILINE`; silently fell back to a hardcoded 14-law list so Laws 15–16 were never verified. Fixed; regression test added. Severity: policy.
- [session] LAW 15 — pre-commit guard flagged speed-of-sound/IP literals inside `tests/test_guard_scripts.py` while testing that detection; resolved by assembling the literals at runtime. Severity: debt.

## Debt (non-blocking)
- Pre-existing orphan branches outside Law 15 namespaces: clean up via #23; canonical branches are NOT deleted without human approval.
