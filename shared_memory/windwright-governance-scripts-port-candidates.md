---
name: windwright-governance-scripts-port-candidates
description: Two new Windwright governance scripts (a LOCKED-constant guard, a tool-registry drift checker) are dependency-free, adversarially reviewed, and squarely Lawkeeper's own category -- real candidates to port into Lawkeeper's scripts/, not yet done.
metadata:
  type: project
---

Split out from `windwright-cosmic-ray-works-native-windows-not-wsl.md`
(caught by GitHub Copilot's review of PR #22, 2026-09-17: that file
originally bundled this unrelated claim alongside the cosmic-ray fact,
coupling two separate things under one entry). Written by a Claude session
working in Windwright (same machine), per the user's direct instruction to
coordinate this finding with the active LawKeeper session.

## The fact

Windwright built two new governance scripts the same night this was
written:

1. A **LOCKED-constant guard** — blocks silently changing a cited/verified
   constant without an explicit override.
2. A **tool-registry drift checker** — catches "verified installed" claims
   going stale (e.g. it caught Windwright's own `psgnn` claim being wrong
   on first use).

Both are dependency-free, no Windwright-specific coupling, and adversarially
reviewed and fixed after real bugs were found in them (see Windwright's
`docs/AI_REVIEW_locked_constants_and_tool_registry_2026-09-04.md` and
`docs/AI_REVIEW_tool_registry_only_2026-09-04.md`).

## Why this matters for Lawkeeper specifically

**Why:** this is squarely Lawkeeper's own category ("constitution-as-code
governance... blocks bad commits") — `ai_review.py`, `merge_gate.py`,
`compliance_watchdog.py`, `guard_branch.py`, `guard_governance.py` already
show a real, working precedent of exactly this kind of script moving
between Windwright and Lawkeeper. These two are real candidates to pull
into Lawkeeper's own `scripts/`, the same way those did — not yet done,
flagging for whoever's actively driving Lawkeeper to evaluate and decide,
not done unilaterally from the Windwright side.

**How to apply:** if picking this thread up, read the two Windwright
review docs named above first (they document real bugs found and fixed,
plus two claims the reviewer got wrong that were caught by direct
verification — useful context for judging the scripts' current maturity
honestly rather than assuming "reviewed" means "flawless"). Windwright's
`scripts/validate_locked_constants.py` and `scripts/check_tool_registry.py`
are the two files, on branch `merge/audio-synthesis-consolidated-2026-09-04-work`
(a worktree at `C:\Users\Admin\Desktop\windwright-audio-consolidation`, same
machine, same "read the files directly" access this note itself follows —
see [[same-machine-direct-file-access-not-chat-relay]]). Confirm this
branch/worktree still exists before relying on the path — it may have
moved or been cleaned up since this was written.
