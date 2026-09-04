---
name: windwright-cosmic-ray-works-native-windows-not-wsl
description: cosmic-ray (Python mutation testing) runs natively on this Windows machine, no WSL needed -- verified directly tonight, not assumed. mutmut is the one that needs WSL. Relevant to Falcun's mission specifically.
metadata:
  type: project
---

Written by a Claude session working in Windwright (same machine), per the
user's direct instruction to coordinate this finding with the active
LawKeeper session — see `docs/session-logs/BOOT_STATE.md` in Windwright for
the fuller context this was found inside (an audio-synthesis consolidation
session, not otherwise relevant to Lawkeeper).

## The fact

`cosmic-ray` (Python mutation testing) **runs natively on Windows, no WSL
required.** Verified directly tonight, twice, not assumed from a research
doc: (1) a real init+exec mutation session against a toy function — 11
mutants generated, all correctly KILLED; (2) a real run against an actual
Windwright module (`backend/dwg_stk_blowhole.py`) using the exact same
config Windwright's own CI pilot uses — in progress/completed by the time
you read this, check `docs/research/RESULT_mutation_testing_pilot_2026-09-03.md`
and `.github/workflows/mutation-testing.yml` in Windwright (branch
`opencode/dwg-stk-synthesis-eval/desktop`) for the full account.

**`mutmut` is the one that needs WSL** — it has no native Windows support
and errors immediately pointing to WSL when run directly on Windows
(confirmed in the same Windwright research). If a WSL requirement was
recalled for "the mutation testing tool" without specifying which one,
it's almost certainly mutmut being misremembered as cosmic-ray, or vice
versa — worth double-checking which one was actually meant, next time this
comes up, rather than assuming either direction.

## Why this matters for Lawkeeper specifically

**Why:** the user asked directly whether external tools/scripts found in
Windwright are relevant here. Two candidates surfaced, both worth a real
look, not a blind port:

1. **`cosmic-ray`/mutation testing generally** — Falcun's own stated
   mission ("Red-Team/Blue-Team loop, running LLM-generated tests and
   patches") is about as natural a fit for mutation testing as exists;
   checked Falcun's own source directly and it doesn't currently use
   either `mutmut` or `cosmic-ray` (only hits were inside its own
   `.venv`'s third-party test suites, not Falcun's code). Given Falcun is
   Windows-based like this machine, `cosmic-ray` (not `mutmut`) is the one
   that would actually work here without needing WSL.
2. **Two new governance scripts Windwright built tonight** — a LOCKED-
   constant guard (blocks silently changing a cited/verified constant
   without an explicit override) and a tool-registry drift checker
   (catches "verified installed" claims going stale, e.g. it caught
   Windwright's own `psgnn` claim being wrong on first use). Both are
   dependency-free, no Windwright-specific coupling, adversarially
   reviewed and fixed after real bugs were found in them (see Windwright's
   `docs/AI_REVIEW_locked_constants_and_tool_registry_2026-09-04.md` and
   `docs/AI_REVIEW_tool_registry_only_2026-09-04.md`). **This is squarely
   Lawkeeper's own category** ("constitution-as-code governance... blocks
   bad commits") — `ai_review.py`, `merge_gate.py`, `compliance_watchdog.py`,
   `guard_branch.py`, `guard_governance.py` already show a real, working
   precedent of exactly this kind of script moving between Windwright and
   Lawkeeper. These two are real candidates to pull into Lawkeeper's own
   `scripts/`, the same way those did — not yet done, flagging for
   whoever's actively driving this session to evaluate and decide, not
   done unilaterally from the Windwright side.

**How to apply:** if picking up either thread, read the two Windwright
review docs named above first (they document real bugs found and fixed,
plus two claims the reviewer got wrong that were caught by direct
verification — useful context for judging the scripts' current maturity
honestly rather than assuming "reviewed" means "flawless"). Windwright's
`scripts/validate_locked_constants.py` and `scripts/check_tool_registry.py`
are the two files, on branch `merge/audio-synthesis-consolidated-2026-09-04-work`
(a worktree at `C:\Users\Admin\Desktop\windwright-audio-consolidation`, same
machine, same "read the files directly" access this note itself follows —
see [[same-machine-direct-file-access-not-chat-relay]]).
