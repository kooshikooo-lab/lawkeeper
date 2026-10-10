# Design note — mutmut trial result and pinned-reference distribution (2026-10-10)

Follows up two leads from `docs/RESEARCH_EXTERNAL_SCAN_2026-10-01.md` (sections 3
and 6), queued in `docs/SESSION_HANDOFF_2026-10-07.md`. User picked both on
2026-10-10. This note changes no governance text and no code; each proposal
below needs a separate approval before anything is built.

## 1. mutmut trial — blocked on this machine, with two findings

Tried `mutmut 3.8.0` (pip, in a throwaway venv on E:, outside the repo) against
a copy of `scripts/gate_pretooluse.py` + `scripts/guard_branch.py` with
`tests/test_gate_pretooluse.py`.

- **It does not run on native Windows.** `mutmut run` exits with: "To run
  mutmut on Windows, please use the WSL" (upstream tracking issue:
  boxed/mutmut#397). This machine has no WSL distribution, so no mutation score
  was produced. Nothing about the gate's test strength is learned from this
  trial.
- **Layout mismatch.** mutmut mutates importable packages/modules. Lawkeeper's
  guard scripts are loaded by path (`tests/conftest.py::load_script`) and are
  not a package, so even on Linux they would need a package-shaped copy or a
  small adapter first.

**Options, cheapest first** (decision for the user, not taken here):
1. Run mutmut on `ubuntu-latest` in a throwaway CI job (the existing `guard`
   job already runs there) against a package-shaped copy of the gate. Report
   the score; do not make it a required check.
2. Install WSL on the desktop (a system change; not done).
3. Drop mutmut and extend Law 18's own `run_mutation` to accept several
   mutations per card. Smaller, but hand-declared, which is the gap mutmut
   would have closed.

Recommendation: option 1, as a one-off measurement first. Decide on 3 only if
the score shows real survivors.

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
