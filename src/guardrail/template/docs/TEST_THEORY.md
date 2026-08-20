# TEST THEORY — the single source of truth for understanding each test

Every test suite gets a theory card with four fields. An agent running a test
MUST have read its card first (see `.opencode/skills/test-theory/SKILL.md`).
Without this, a test result is a pass/fail with no meaning.

The key property every card must have: **an independent oracle.** A test that
asserts the code equals its own constant (self-referential) is marked BROKEN and
is worthless — see the reference-constants example.

---

## test_analytical_pipes.py

- **Theory:** A cylindrical pipe's resonances follow the wave equation exactly.
  Open-open: f_n = n·c/(2·L_eff). Closed-open: f_n = (2n-1)·c/(4·L_eff).
- **Oracle:** The analytic pipe formula, with an end correction of 0.66·r
  (NOTE: this is a curve-fit, see docs/end_correction_resolved.md — the true
  unflanged value is 0.6133·r; the 0.66 is absorbing another systematic error).
- **Good vs bad:** TMM within 60 cents of theory. >60c means the solver's
  register/axis/boundary convention is broken, NOT that the formula is wrong.
- **Debug:** if it fails, reproduce one (L, r, n) case by hand; check register
  (open fundamental = register 2), then the end-correction used.

## test_reference_physics.py

- **Theory:** The reference layer (backend/physics/reference/) is executable
  ground truth: Levine-Schwinger unflanged end correction 0.6133·r, radiation
  resistance (ka)²/4.
- **Oracle:** The cited physics constants (Levine-Schwinger 1948).
- **Good vs bad:** `test_reference_constants` currently asserts the function
  equals 0.6133·7.5 — this is SELF-REFERENTIAL (passes whether 0.6133 is right or
  wrong). The VALUABLE test is `test_radiation_stub_is_flagged`: it asserts the
  known BesselRadiation stub (Re(Z)=0.5) is flagged by the reference. If that
  test starts PASSING (stub unflagged), the stub was fixed — update it.
- **Debug:** distinguish "constant echo" (weak) from "stub flagged" (real).

## test_cone_cross_validation.py

- **Theory:** A truncated cone closed near its small end behaves like an open
  cylinder: full harmonic series, f_n ≈ n·c/2L. Closed at the large end gives an
  inharmonic spectrum. This is WHY saxophones/oboes overblow at the octave.
- **Oracle:** The full-harmonic-series relation + the virtual-apex correction
  (x0 = r_small·L/(r_large-r_small); f1 = c/(2·(L+x0))).
- **Good vs bad:** f2/f1 ratio ≈ 2.0 (full series). A ratio ≈ 1.5 means the axis
  convention is inverted (radii[0] interpreted as mouthpiece instead of bell).
- **Debug:** this test is the discriminator for the axis-convention bug. If it
  fails, the cone is being closed at the wrong end.

## test_openwind_solver.py

- **Theory:** TMM and OpenWInD FEM are two independent solvers that must agree on
  the same geometry. They are complementary (ADR-006): TMM drives optimization,
  OpenWInD validates.
- **Oracle:** cross-solver agreement (differential testing).
- **Good vs bad:** <60 cents. >60c = register/boundary-convention mismatch
  between the two solvers (the exact bug class in failure #9).
- **Debug:** check the register convention (open = n+1, reed = n), the register
  vent state, and the axis (TMM 0=bell, OpenWInD 0=mouthpiece).

## test_variable_bore.py + test_hole_methods.py

- **Theory:** A scale of notes is reached by placing toneholes. Three methods:
  Sequential (bell→mouthpiece), Independent (each hole alone), Simultaneous (all
  at once).
- **Oracle:** the target note frequencies (a real scale).
- **Good vs bad:** <200 cents RMS. Xaphoon C (open-open, major scale) reaches
  only ~294c by ANY of the three methods — because it needs CROSS-FINGERINGS,
  which none of the three implement. This is a KNOWN LIMITATION (xfail), not a
  regression. The "Independent" method is also known-broken (~437c) because it
  optimizes each hole as if it were the only hole.
- **Debug:** if a non-Xaphoon instrument exceeds 200c, it's a real bug. If only
  Xaphoon/Independent fail, it's the documented cross-fingering limitation.

## v2_validation_runner.py (scripts/)

- **Theory:** Validates the TMM solver against published reference instruments
  (the Inria 2026 benchmark cylinders/cones, Bowen bass clarinet, UNSW flute).
- **Oracle:** the fixture's target frequencies (published/analytic).
- **Good vs bad:** <10 cents mean-abs (CROSS_SOFTWARE_MEAN_ABS_CENTS). The two
  Inria cylinders now validate at ~1.9c. Fixtures with no bore_profile are
  "targets-only" and are SKIPPED, not failed.
- **Debug:** each harmonic needs its OWN register (register advances per
  harmonic; a fixed register returns the fundamental for every target — this was
  the 2800-4300c bug). Also check the end correction (see end_correction_resolved.md).

## test_metrics.py

- **Theory:** cents math (1200·log2(f/target)), RMS, and intonation tiers
  (SANE > ACCEPTABLE > PROFESSIONAL).
- **Oracle:** pure math (independently checkable).
- **Good vs bad:** exact values; tier ordering must be monotonic.
- **Debug:** a failure here is a math bug, not a physics bug.

## test_mesh_repair_gate.py

- **Theory:** a printable STL must be watertight AND manifold AND a single
  connected component.
- **Oracle:** known-good (koncovka_C) and known-bad (nonwatertight_target)
  fixtures.
- **Good vs bad:** watertight passes, non-watertight fails. If BOTH pass, the
  gate stopped checking (regression).
- **Debug:** this is the discriminator — the known-bad fixture must fail.

## test_property_based.py + test_physics_properties.py (new this session)

- **Theory:** physical invariants and relations that hold for ANY geometry:
  S/V = 2/r for a cylinder, quarter/half-wave length ratio, 2^(1/12) semitone,
  junction transmission symmetry.
- **Oracle:** pure relations (metamorphic) + the reference module (differential).
- **Good vs bad:** exact relations. A failure is a real invariant violation.
- **Debug:** these were written to be RED on a known stub, GREEN on truth.

---

## The three statuses (never collapse them)

| Status | Meaning |
|---|---|
| CRASH | exception / rc != 0 |
| RAN-BUT-FAILED | completed, result outside threshold |
| PASS | within threshold |

"Ran" is never a synonym for "passed". A 402c instrument is RAN-BUT-FAILED, not
"worked".

---

# The protocol (enforced, not prose)

This file IS the protocol. The wrapper (`scripts/governed_test.py`) enforces it
mechanically — do not rely on an agent reading this and remembering it.

## Mandatory protocol (the wrapper will not let you skip it)

1. **Never invoke pytest directly.** Run tests through
   `python scripts/governed_test.py tests/test_X.py`.
2. The wrapper **refuses to run** a test whose theory card is missing or malformed.
   A missing card is an infrastructure failure — fix the card first, do not
   "run it anyway".
3. The wrapper prints theory / oracle / blind-spot / acceptance BEFORE the result.
4. On failure, the wrapper **refuses to resolve the run** until you supply
   `--classify CODE BUG | TEST BUG | KNOWN LIMITATION` with a justification that
   references the printed oracle/threshold.
5. Every report must state the number WITH its threshold ("402.8c against a <20c
   target = BROKEN"), never a bare pass/fail.

## How to spot a bad test (ranked checklist)

1. **No independent oracle** — asserts against a value derived from the same code
   path it tests, or another module built the same way.
2. **Fabricated fixture data** — numbers that don't satisfy the physical relation
   they claim (harmonic ratios, monotonicity, symmetry). 10-second hand-check.
3. **Silent mock/stub fallback on failure** — try/except around a real dependency
   that falls back to a mock and still reports PASS.
4. **Tolerance loosened to hide a failure** — with no physical justification.
5. **Tautological assertion** — recomputes the formula-under-test inline.
6. Single happy-path case, no boundary/edge case.
7. Catches an exception and treats ANY caught exception as pass.
8. Docstring claims one algorithm, body implements another (correlation² as "Sobol").
9. Never once failed in git history — often not wired to the path it claims.

## Adversarial review (state transition, not a suggestion)

A change's result is **UNTRUSTED until adversarially reviewed**. Before trusting
a non-trivial change (especially physics):

```
python scripts/ai_review.py --prompt docs/AI_REVIEW_PROMPT.md \
    --files <changed files...> --output docs/ADVERSARIAL_REVIEW_<date>.md
```

Then fact-check the model's answer empirically (run a one-liner against the real
numbers). Model confidence is not evidence. A skipped adversarial pass is an
incomplete task, exactly as a skipped test is.

## Trust levels (T0-T5)

| Level | Meaning |
|---|---|
| T0 | smoke / execution only |
| T1 | assertion exists |
| T2 | independent oracle |
| T3 | adversarially reviewed |
| T4 | mutation / discrimination verified (known-bad fixture) |
| T5 | validated against independent physics / reference |

A report must state trust level, not just "pass": "17 tests pass, 11 are T3+,
6 are T1" — not "all pass".
