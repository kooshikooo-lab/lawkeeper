---
name: windwright-verification-technique-cross-validate-against-worked-examples-2026-09-04
description: A real, reusable verification technique from tonight's Windwright work -- when implementing a paper's numerical/discretization scheme, cross-validate your general formula against any fully-worked example the paper itself provides (symbolically re-derived independently), not just against your own reasoning or a single "looks plausible" run.
metadata:
  type: project
---

Written by a Claude session working in Windwright (same machine),
continuing the earlier update in [[windwright-cosmic-ray-works-native-
windows-not-wsl]] and [[user-quality-standard-escalation-and-cross-repo-
sharing-2026-09-04]]. Noticed Lawkeeper's own most recent commit
("GOVERNANCE-UPDATE: fix Laws 4-7 (real Windwright boilerplate, not just
flagged debt)") looks like it's already acting on the earlier update --
good, this one continues that thread with something new and concrete.

## What happened

Implementing a real physics model from a cited paper (Darabundit &
Scavone 2025's unflanged-radiation PHS, Eqs 110a-113b) in Windwright.
First implementation attempt looked plausible (ran without error,
produced numbers in a reasonable range) but a discrete-vs-continuous
frequency-response comparison showed a real, unexplained ~31x
discrepancy. Rather than either (a) assume it's a discretization
approximation artifact and move on, or (b) assume the code is buggy and
start guessing at fixes, the real diagnostic step was: **the same paper
had already fully worked a simpler example (an RLC circuit, Section 4)
through the exact same general discretization formula.** Symbolically
re-solved that worked example from scratch (sympy, independent of any
existing code) and compared its answer to the same general formula
applied via this session's own implementation. Result: the general
formula matched to float precision -- confirming the *discretization
code itself* was correct, and narrowing the real question down to
something specific to the new model (which turned out to be genuine
numerical stiffness at the specific parameter values used, not a bug --
full account in Windwright's `docs/research/RESULT_radiation_phs_
implementation_2026-09-04.md`).

## Why this is worth recording as a technique, not just a one-off result

**Why:** this generalizes past this one physics model. Any time a paper
(or spec, or reference implementation) provides a fully-worked example
alongside a general formula/algorithm, that worked example is a free,
high-value independent oracle for verifying a from-scratch
reimplementation of the general case -- often better than inventing your
own test cases, because the paper's own worked numbers are exactly what
the paper's authors themselves checked. This is a stronger, more
specific instance of the general "verify against an independent oracle,
not the code under test" principle (Law 19 in Windwright's constitution)
-- concretely: *look for a worked example in the source material before
writing your own test oracle from scratch.*

**How to apply:** when implementing anything from a paper/spec that
includes both (a) a general method and (b) at least one fully-worked
example applying that method, always cross-check a from-scratch
reimplementation of the general method against the worked example
first, independently re-derived (don't just eyeball the paper's own
final numbers -- actually re-solve the example's equations yourself, so
you're not trusting a possible transcription error in either direction).
This is cheap relative to debugging a subtle discrepancy blind, and it
cleanly separates "is my general formula right" from "is this specific
new case doing something unusual" -- which is exactly what let tonight's
finding land on "real numerical stiffness, not a bug" with actual
confidence rather than a guess.
