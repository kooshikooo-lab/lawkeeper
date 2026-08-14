# AI Failure & Debt Log

Log every compliance failure and guard bypass. Review before each session (Law 12).

## Template
- [YYYY-MM-DD HH:MM] LAW: <N> — <what broke> / <root cause> / <fix>. Severity: <blocker|policy|debt>.

## Failures
- [session] LAW 16 — watchdog law-loader lacked `re.MULTILINE`; silently fell back to a hardcoded 14-law list so Laws 15–16 were never verified. Fixed; regression test added. Severity: policy.
- [session] LAW 15 — pre-commit guard flagged speed-of-sound/IP literals inside `tests/test_guard_scripts.py` while testing that detection; resolved by assembling the literals at runtime. Severity: debt.
- [2026-08-07T16:40] LAW 10 — agent acted before confirming scope: committed a framework MVP to a feature branch and probed `git merge-tree` semantics WITHOUT first getting user sign-off on the test plan / default choices (Law 10: "when uncertain, stop and ask"; Law 12 coordination). Root cause: treated "make a plan to test lawkeeper" as an instruction to build, and replied to ambiguity with multi-part technical questions instead of a single confirmation with recommended defaults. Fix: surface defaults as simple checkboxes and wait for explicit approval before editing code; keep git probes validated before trusting results. Severity: policy.
- [2026-08-14] LAW 18 — reported a 402.8-cent intonation result as "worked" / "best" when the target is <3 cents (barely-acceptable <20, >200 = BROKEN). Root cause: confused "process ran to completion (rc=0)" with "result is correct". Fix: never report a number without its threshold; "ran" is never "passed"; three statuses CRASH / RAN-BUT-FAILED / PASS. Severity: blocker.
- [2026-08-14] LAW 17 — ran tests, found bad results, and STOPPED at reporting instead of debugging, despite standing authorization to debug ("you are also clear to debug and audit based on test results"). Root cause: collapsed work into a report; treated "found the bug" as the deliverable when the deliverable was "fix it or get as far as possible" (Law 17: work in order of safety, not approval — safe local debugging is never blocked). Fix: completion criterion for "test + debug" is a fixed or narrowed bug, not a bug list. Severity: policy.
- [2026-08-14] LAW 18 — skipped the baked-in adversarial review and narrowed "test your tests" to "prove my new tests discriminate" instead of auditing existing tests for quality. Root cause: treated adversarial review as a one-off exercise instead of a standing gate; reinvented a weaker version of what already existed (scripts/ai_review.py). Fix: adversarial review is a state transition — a result is UNTRUSTED until reviewed; a skipped review is an incomplete task. Severity: policy.
- [2026-08-14] LAW 18 — estimated a test run at "3.5-4 hours" (later "6-9 hours") that actually finished in 13 minutes; also reported an overnight run as "launched" without verifying the detached process survived. Root cause: estimated from the plan, not from measured data; "issued the launch command" != "verified it runs". Fix: no duration claim without a measured data point; after any detached launch, verify PID + growing log before reporting success. Severity: policy.

## Debt (non-blocking)
- Pre-existing orphan branches outside Law 15 namespaces: clean up via #23; canonical branches are NOT deleted without human approval.
- [2026-08-07T16:40] Initial `git merge-tree` probe falsely reported "no conflict" because the repo's default branch was `master`, so `checkout main` created a non-divergent branch. `merge_gate.py` itself is NOT broken — a corrected probe (sibling branches from a single base) returns rc 1 with `CONFLICT (content)` as expected. Debt: re-verify `merge_gate` e2e against real git conflicts on Linux CI before relying on it. Severity: debt.
