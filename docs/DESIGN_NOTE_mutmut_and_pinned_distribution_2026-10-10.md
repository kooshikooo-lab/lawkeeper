# Design note — mutmut trial result and pinned-reference distribution (2026-10-10)

Follows up two leads from `docs/RESEARCH_EXTERNAL_SCAN_2026-10-01.md` (sections 3
and 6), queued in `docs/SESSION_HANDOFF_2026-10-07.md`. User picked both on
2026-10-10. This note changes no governance text and no code; each proposal
below needs a separate approval before anything is built.

## 1. mutmut trial -- result (Linux CI, 2026-10-10)

**Not runnable on this machine:** `mutmut 3.8.0` refuses native Windows ("please
use the WSL", boxed/mutmut#397) and there is no WSL here. So it was run once on
`ubuntu-latest` from a throwaway branch (workflow and branch since deleted;
nothing merged), against `scripts/gate_pretooluse.py` as of PR #34, with
`tests/test_gate_pretooluse.py` only.

**Result: 479 mutants -- 284 killed, 145 survived, 50 have no covering test.**
That is 59% killed overall, 66% of the mutants the tests can reach.
- The 50 "no tests" are all in `main()`, which the tests exercise through a
  subprocess; mutmut only tracks in-process coverage, so this is a measurement
  gap, not an untested function.
- The 145 survivors are real: the gate's tests do not pin down many
  mutations. The run's output was truncated to its last 80 lines, so only 30
  survivors were seen by function (`inspect_command` 17, `_parse_git_invocation`
  6, `decide` 4, `_overridden` 3). Those two parser functions hold the
  `cd`/`-C` tracking added in PR #34, so that code is the least well pinned.
  The full per-mutant list was not kept.

**What it took (relevant if this is repeated):** mutmut can only attribute
tests to mutants when the module is imported by name; the repo's tests load
scripts by path (`conftest.load_script`), which gave "could not find any test
case for any mutant". The run only worked after copying the gate tests into a
separate directory and rewriting their import to `import scripts.gate_pretooluse
as gate`. Making this permanent means changing how `test_gate_pretooluse.py`
imports the gate.

**Law 18 comparison:** Law 18's single hand-declared mutation per theory card
cannot see a 145-survivor gap like this; mutmut did, in about 25 seconds of
mutation time. Recommendation (not acted on): keep the T4 check, add a
non-blocking mutmut CI job for the gate, and use its survivor list to add
targeted tests. Needs the user's OK because it adds a CI workflow and a test
import change.

## 2. Pinned-reference distribution — proposed shape

**Problem (verified in the 2026-10-01 scan, section 3):** `lawkeeper init`
copies the template tree into a consuming repo; the only way to take later
fixes is `init --force`, a blind overwrite. Re-checked today:
`src/guardrail/cli.py` still has no `update`/`sync` command, and
`.guardrail.json` (written by `cmd_init`) records only `project_name`,
`machines` and `canonical_branches` — **no template version and no per-file
hashes**, so nothing can say which upstream version a repo was scaffolded from
or which files the repo has since customised.

**Proposal, in the order it would have to be built:**
1. **Record provenance at init.** `.guardrail.json` gains `template_version`
   (the `guardrail.__version__`) and a `template_files` map of path → sha256 of
   the file as written. Additive; existing repos simply lack the keys.
2. **`lawkeeper update` (diff first, write only on request).** Compare each
   template file against the recorded hash: unchanged locally → safe to replace
   with the new version; changed locally → show a three-way diff and leave it
   alone unless named. Without recorded hashes (pre-change repos) it reports
   "no provenance" rather than guessing.
3. **Mutable-ref warning for recorded external pins.** Where docs or config
   record a pinned external commit (the AEF clone, research clones), add an
   advisory check that the ref is a full 40-hex SHA. Copy pre-commit's idea but
   not its gap: its `WarnMutableRev` skips dotted tags such as `v2.0`; a plain
   "is it 40 hex characters" test has no such hole. Advisory only, like the
   original.

**Not proposed:** adopting the pre-commit framework itself. Lawkeeper's hooks are
plain git hooks via `core.hooksPath`; the gap is distribution, not execution.

**Law relevance:** step 1–2 touch `src/guardrail/cli.py` and the scaffolded
`.guardrail.json` schema (not protected governance text). Step 3 is a new check;
under Law 21 it needs a consumer before it is built — the AEF-as-base
evaluation is the only current one, so it should wait for that.

## 3. Decisions this leaves for the user

- mutmut: run option 1 as a CI measurement? (recommended)
- Provenance + `lawkeeper update` (steps 1–2): build? (recommended, small)
- Mutable-ref check (step 3): defer until the AEF evaluation gives it a consumer.
