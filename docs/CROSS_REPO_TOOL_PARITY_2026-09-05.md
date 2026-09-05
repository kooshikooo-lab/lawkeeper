# Cross-repo tool parity: lawkeeper vs. Windwright vs. falcun (2026-09-05)

Real user request: check what exists in one repo's `scripts/` that another
could use, not left siloed (`shared_memory/user-quality-standard-
escalation-and-cross-repo-sharing-2026-09-04.md`). A `falcun` session
already did most of this analysis directly and well —
`falcun/docs/CROSS_REPO_GOVERNANCE_TOOL_INVENTORY_2026-09-04.md` — written
there because `SendMessage` to a lawkeeper session was unavailable at the
time, with an explicit note that lawkeeper's own repo is this finding's
natural home. This doc brings it home: re-verified the two headline claims
directly against both repos before writing this (not taken on faith), adds
nothing that contradicts the original, and does not touch
`claude/guardrail-fit-investigation-spmp2b` (a separate, active
investigation on a different branch, asking the reverse question — should
falcun adopt `guardrail` — not duplicated here).

## The headline gap: lawkeeper has no equivalent of falcun's `canon.py` / `prior_art.py`

Verified directly, 2026-09-05: `find . -iname "canon*.py" -o -iname
"prior_art*.py"` across this whole repo returns nothing; both files are
real and substantial in `falcun/agent/`.

- **`canon.py`** — a propose-then-confirm registry of `CanonicalClaim`s
  (a specific question, tied to a specific source, with the exact
  verbatim supporting quote). `propose_claim()` always enters PROPOSED;
  only `confirm_claim()` (human, or an agent that directly read the
  cited quote this session) moves it to CONFIRMED. Wired into
  `validate_commit_msg.py`'s Rule 5: a domain-knowledge-bearing commit
  must name a confirmed claim by ID. Built 2026-08-29 after two of
  falcun's own fabricated acoustics claims were caught and corrected.
- **`prior_art.py`** — a mechanical "did you check for an existing
  tool/library/paper first" gate: a `PriorArtCheck` log entry naming
  real search terms/sources/decisions, required (Rule 7) before any new
  file lands under a configured `new_code_paths` glob. Built after
  falcun caught itself skipping its own written "check first" norm more
  than once (a from-scratch physics-model reimplementation written while
  a real, installable package for the same job was already named in its
  own research docs).

**Why this is a real gap in the tool meant to generalize this pattern,
not a falcun-specific need:** lawkeeper's own `AI_CONSTITUTION.md` already
states both principles as prose with zero mechanical enforcement —
Law 3 ("Never duplicate — search before writing") has no code-level check
anywhere in `src/guardrail/laws/`, and Law 20 ("never claim verified
without a fresh check... never fabricate") is enforced only by an agent's
own discipline, not a hook. `canon.py`/`prior_art.py` are exactly the
missing mechanism for both — a real, working, adversarially-motivated
design, not a prototype. Porting them would mean: two new modules under
`src/guardrail/` (or a `canon`/`prior_art` law pair), two new
`validate_commit_msg.py` rules mirroring falcun's Rule 5/7 pattern, a
`.guardrail.json` schema addition (`new_code_paths`, matching falcun's
own config shape), and real tests proving the propose/confirm and
log-then-check flows actually gate a commit — a genuine feature, not a
small patch. **Not implemented here** — flagging for a real decision
(build it now, or let the parallel `guardrail-fit-investigation` branch's
work conclude first, since it may reach related conclusions from the
other direction).

## The reverse gap: falcun has no equivalent of 4 real lawkeeper tools

Re-verified 2026-09-05 (`find` across falcun for each name; falcun's own
doc already confirmed this the same way):

- **`governed_test.py`** — the single most valuable of the four per
  falcun's own analysis: wraps test runs, refuses to run a test file
  missing its theory card, classifies CRASH/RAN-BUT-FAILED/PASS with a
  trust level. Directly on-theme with the "a green suite isn't evidence
  the thing works" discipline both repos already claim to hold.
- **`orphan_scan.py`** (Law 21) — would have mechanically caught a real,
  already-confirmed-dead function in falcun's own `agent/probes.py`
  (`_run_falsification_check`), per falcun's own doc.
- **`claude_stop_hook.py`** — already a known, logged gap on falcun's
  side (`falcun/docs/WORKPLAN.md` Phase 7), blocked on `guardrail` not
  being installed/vendored there — not new information, just confirmed
  still open.
- **`mine_failure_patterns.py`** — falcun has real failure-pattern data
  scattered across `docs/WORKPLAN.md` with no equivalent mining/
  normalization tool.

These four are lawkeeper's actual shipped or dev-tooling strengths
already; whether/how falcun adopts them is squarely the
`guardrail-fit-investigation` branch's question, not re-litigated here.

## Smaller items, not independently re-verified this pass (falcun's own assessment, spot-checked for consistency)

- Windwright-only tools correctly **not** flagged as portable:
  `quality_gate.py`/`quality_gate_local.py` (illustration-vs-reference
  vision comparison, genuinely Windwright-domain), `scan_all_precommit.py`,
  `sweep_diff_check.py`.
- `code_compliance_checker.py` — falcun's doc independently flagged its
  docstring still says "for Windwright" even in lawkeeper's own copy as
  worth checking. **Independently confirmed** by this lawkeeper session
  on 2026-09-04/05 (`docs/AI_FAILURE_PATTERNS.md`'s Laws 4-7 entry): it's
  real, unadapted Windwright content (Levine-Schwinger radiation-formula
  checks), dev-only, not shipped — a real, separate decision (delete/
  rewrite/keep) already flagged there, not re-flagged twice here.
- `check_declared_dependencies.py`, `memory_query.py`, `hardware_scanner/`,
  `scan_config.py` — falcun's doc left these unread for general
  applicability. Quick lawkeeper-side read: `hardware_scanner/` is
  genuinely personal-hardware-shopping-specific, not a governance tool,
  correctly low priority. `scan_config.py` is a shared dependency other
  ported tools would need (already the real, positive Law 7 example),
  not a standalone port target. `check_declared_dependencies.py` and
  `memory_query.py` are real and plausibly portable but not yet checked
  against falcun/Windwright's actual needs — genuinely open, not decided
  here.
