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
Windwright are relevant here. `cosmic-ray`/mutation testing generally is
one strong candidate: Falcun's own stated mission ("Red-Team/Blue-Team
loop, running LLM-generated tests and patches") is about as natural a fit
for mutation testing as exists; checked Falcun's own source directly and
it doesn't currently use either `mutmut` or `cosmic-ray` (only hits were
inside its own `.venv`'s third-party test suites, not Falcun's code).
Given Falcun is Windows-based like this machine, `cosmic-ray` (not
`mutmut`) is the one that would actually work here without needing WSL.

**How to apply:** if picking this thread up, confirm Falcun's own
governance-test setup still has no mutation-testing coverage before
proposing `cosmic-ray` as an addition (a stale check, not an assumption —
Falcun's own test tooling may have changed since this was written).

A separate, unrelated candidate found in the same Windwright session (two
governance scripts worth porting into Lawkeeper's own `scripts/`) is its
own fact — see [[windwright-governance-scripts-port-candidates]], split
out from this file per the shared_memory one-fact-per-file convention
(caught by GitHub Copilot's review of PR #22, 2026-09-17: this file
originally bundled both, coupling two unrelated claims).
