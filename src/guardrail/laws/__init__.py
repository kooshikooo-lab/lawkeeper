"""Constitution laws enforced by the guardrail runner.

Discovered automatically by guardrail.core.registry. Only portable, repo-
agnostic laws live here; some laws (e.g. Law 7's one-source-of-truth-for-
canonical-values check) are enforced by scripts/validate_pre_commit.py
instead, since they need to scan arbitrary staged files rather than run as
a portable per-repo law check.

(This docstring previously named "Law 7's canonical speed-of-sound" as the
example -- Windwright-specific content, removed 2026-09-04 along with the
dead check itself; see validate_pre_commit.py's own removal note.)
"""
