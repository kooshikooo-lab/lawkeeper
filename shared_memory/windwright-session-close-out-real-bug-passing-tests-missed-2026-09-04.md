---
name: windwright-session-close-out-real-bug-passing-tests-missed-2026-09-04
description: Session close-out from Windwright tonight -- a real bug (a bore's last node permanently disconnected from wave propagation) that a currently-passing test suite didn't catch, because the tests only checked aggregate output, not internal state. Relevant to Lawkeeper's own governance mission.
metadata:
  type: project
---

Written by a Claude session working in Windwright (same machine), closing
out for the night per direct user instruction to keep other sessions
in the loop, especially for governance/testing findings -- this is the
last one.

## The finding

Building an A/B test in Windwright (comparing a real vs. a placeholder
physics boundary condition), the two configurations produced
byte-identical output -- an anomaly, not the expected outcome. Root-
caused rather than assumed: a real, pre-existing bug where one line in a
numerical scheme silently overwrote a correctly-computed formula the
previous line had already set, permanently disconnecting part of the
simulation's state from the rest. The project's own existing, currently-
green test suite for this code never caught it, because those tests only
check the aggregate output spectrum, not whether the specific internal
state in question ever actually changes.

**Why:** directly relevant to Lawkeeper's own mission ("mechanical policy
that blocks bad commits... even when the agent misunderstands"). A test
suite that's green can still have a real, structural blind spot if it
only checks aggregate/output-level behavior rather than also asserting
specific internal invariants ("does this state variable ever actually
change in response to forcing" is a cheap, real check that would have
caught this immediately). Full account: Windwright's `docs/research/
RESULT_horn_phs_last_node_bug_2026-09-04.md`.

**How to apply:** when reviewing or writing tests for a stateful
simulation/numerical scheme (relevant if Lawkeeper's own template/
guardrail work ever touches this kind of code, or if this pattern is
worth a general governance check), consider whether the test would catch
"this internal state variable never actually updates" as well as "the
final output looks roughly right" -- these are genuinely different
failure modes, and the second doesn't imply the first.

## Also from tonight, briefly

Full night's close-out is in Windwright's `docs/session-logs/
BOOT_STATE.md` on `merge/audio-synthesis-consolidated-2026-09-04-work` --
the theory-card hook, `import-linter` findings, the real radiation-model
implementation and its 3-oracle verification, and the branch-prefix
phase-out status. Not duplicated here in full; check that file if picking
up related work.
