# Guardrail Fit Investigation — 2026-09-04

**Question:** does lawkeeper's own enforcement stack (the guard scripts it runs
on itself, in `scripts/`) actually fit the project it's protecting — or is it
still partly wearing the shape of the project it was extracted from
(`instrument-designer` / "Windwright", which had `backend/` and
`woodwind_designer/` directories that lawkeeper doesn't have)?

Method: read every guard script in `scripts/`, ran the checks that are safe to
run read-only (`system_audit.py`, the pytest suite, `check_local_dependencies.py`,
`toolcheck.py`), and cross-checked `FIXES.md`'s "still open" list against the
current code to see if it's stale.

## Verdict: partial fit. Half the stack was retrofitted to see lawkeeper's
real layout (`src/guardrail/`); half still can't see it at all.

### Fixed and working
- **`scripts/scan_config.py`** (added later) auto-detects any `src/<pkg>/`
  with an `__init__.py`, plus `scripts/` and `tests/`. It's wired into
  `compliance_watchdog.py`'s violation scan and `check_local_dependencies.py`,
  so bare-except / hardcoded-IP / oversized-module checks and the dependency
  checker **do** correctly see `src/guardrail/` now.
- **Template drift is actually tested.** `tests/test_template.py` asserts the
  shipped scaffold (`src/guardrail/template/`) stays byte-identical to the
  live `scripts/`/`docs/`/`AGENTS.md` this repo runs on itself. I diffed them
  directly too — currently in sync (only difference: `compliance_baseline.json`,
  which is project-specific data, correctly not shipped in the template).
- **`validate_commit_msg.py`'s CI fallback** — `FIXES.md` still lists "silently
  uses an empty string for the commit message" as open. It isn't: the code now
  reads `git log -1 --format=%B` when run without a message-file argument
  (documented in the file's own comment), which is exactly what CI's push-only
  step needs. **`FIXES.md` is stale on this point.**
- **CI's dead `dependency-locks` job** — `FIXES.md` also lists this as open.
  It isn't: the job was removed from `governance-guard.yml` (see the comment
  block at the bottom of that file explaining why). **Stale on this point too.**

### Still broken — the guardrails are blind to their own home
Three guard scripts still hardcode `backend/` and `woodwind_designer/` —
directory names from the old project, which don't exist anywhere in
lawkeeper:

1. **`scripts/validate_pre_commit.py` — the actual pre-commit hook.**
   - `PLACEMENT_RULES` only knows `backend/`, `tests/`, `scripts/`, `docs/`.
     There is **no rule for `src/`**, so nothing enforces file-type boundaries
     inside `src/guardrail/` — the one directory that's actually lawkeeper's
     source code.
   - `OVERSIZED_ALLOWLIST` lists 11 files under `backend/` and 2 under
     `woodwind_designer/engine/`, none of which exist here.
   - `SPEED_OF_SOUND_CANONICAL_FILE = "backend/tmm_acoustics.py"` — a
     physics-one-source-of-truth check (Law 7) for a physical constant this
     project has no reason to reference. Dead code, but harmless (can never
     match a staged file).
2. **`scripts/toolcheck.py`** — `LOCAL_ROOTS` and the "Live" import-scan roots
   are `{"backend", "scripts", "woodwind_designer", ...}`. `src/guardrail/`
   is not scanned, so this check's phantom/orphan/forgotten-dependency report
   never sees lawkeeper's own imports.
3. **`scripts/compliance_watchdog.py`'s `SUBSYSTEM_TABLE`** — the "Step 3:
   identify your subsystem" line every boot-sequence printout shows still
   lists `geometry.py`, `tmm_acoustics.py`, `woodwind_designer/`, etc. It's
   inert (only feeds a printout, not a check) but actively misleading to
   anyone — human or agent — reading `--boot` output for guidance on *this*
   project.

**Net effect:** if someone adds a stray non-`.py` file directly under
`src/guardrail/`, or the tool-registry / import checks need to reason about
lawkeeper's own dependencies, those three guards give false confidence — not
because they're broken, but because they're still checking a different
project's floor plan.

### Environment note (not a code bug)
`python scripts/system_audit.py` **FAILs in this fresh checkout**:
`core.hooksPath` is unset because `scripts/install_hooks.py` hasn't been run
here yet. Expected for any new clone — flagging it because Law 16.4 says the
audit must pass before a commit to a canonical branch, and it currently
doesn't in this session.

### Test suite
`pytest -q` (excluding the 3 `slow` end-to-end tests in `test_init_smoke.py`,
which build a real wheel + venv and weren't run in this pass to keep it
light): **44 passed, 0 failed.** Recommend running the slow suite too before
any release — it's the one that would have caught the original packaging bug.

## Recommended next steps (unfinished work, prioritized)
1. Point `validate_pre_commit.py`, `toolcheck.py`, and `validate_imports.py`
   at `scan_config.get_scan_paths()` the same way `compliance_watchdog.py`
   and `check_local_dependencies.py` already are, instead of their own
   hardcoded `backend/`/`woodwind_designer/` lists. This is the same fix
   `scan_config.py`'s docstring already describes doing once — it just wasn't
   applied everywhere.
2. Add a `src/` entry to `PLACEMENT_RULES` (or otherwise decide + enforce
   what belongs in `src/guardrail/`).
3. Refresh `compliance_watchdog.py`'s `SUBSYSTEM_TABLE` to describe
   lawkeeper's own modules (`cli.py`, `config.py`, `template/`), or drop the
   table if it's not worth maintaining per-project.
4. Update `FIXES.md`'s "Not fixed here" list — 2 of its 4 items are already
   fixed; leaving them listed as open makes the debt log unreliable as a
   status source.
5. Before any release: run the `slow` test suite (`pytest tests/test_init_smoke.py -v`)
   and re-verify `pip install lawkeeper` vs. the `guardrail` package/import
   name mismatch that `FIXES.md` flags as still open — not re-checked in this
   pass.

## What I did not check
Windows-only paths (`check_powershell_51_compat.py`, the `.ps1` hook
installer) — this session runs on Linux, so those scripts were read but not
executed.
