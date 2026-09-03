# What changed and why

Scope: the four things discussed — package-data/template resolution,
`lawkeeper init` failing loudly instead of silently, `--force` actually
working, and `check_delete` failing closed. Nothing else in the repo was
touched (the compliance watchdog's hardcoded `backend/`/`woodwind_designer/`
scan paths, the CI's missing `compile_requirements.py`, the `pip install
lawkeeper` vs `name = "guardrail"` mismatch beyond the rename below — those
are still open and listed at the bottom).

## 1. Template moved inside the package

**Before:** `template/` sat at the repo root, a sibling of `src/`.
`pyproject.toml` declared `package-data.guardrail = ["template/**/*"]`,
but setuptools resolves package-data relative to the *package* directory
(`src/guardrail/`), not the repo root. A built wheel shipped zero template
files. `cli.py` located the template via
`Path(__file__).parent.parent.parent / "template"`, which only happens to
work for an editable/source-checkout install — once installed from a wheel,
`__file__` lives directly under `site-packages/guardrail/`, and that
relative walk doesn't land on anything real either.

**After:** `template/` now lives at `src/guardrail/template/`. Location is
resolved with `importlib.resources.files("guardrail") / "template"`, which
works identically across editable installs, wheel installs, and zipapps.
Verified: `python -m build --wheel` now includes 20 template files (vs. 0
before); a wheel installed into a clean venv and run against a real `git
init`-ed directory writes the full 33-file scaffold.

## 2. `lawkeeper init` fails loudly instead of reporting false success

**Before:** if the template directory was missing/empty (as it always was
in a real wheel install), the copy loop iterated over nothing, printed
"scaffolding written to `<dir>`" and exited 0. A user would believe they
were governed while having only an empty `.guardrail.json`.

**After:** `cmd_init` now (a) checks the template directory exists before
doing anything, and refuses with a clear "packaging bug, not your fault"
message if not; (b) tracks every file it actually writes and verifies a
required set (constitution, `install_hooks.py`, `.guardrail.json`) exists on
disk afterward, refusing and explaining if not. Verified by deliberately
building a wheel with the template deleted: exit code 1, explicit stderr
message, zero files written — no more silent "success."

## 3. `--force` actually does something

**Before:** declared as a CLI flag, never read anywhere in `cmd_init`.
Re-running `init` on an already-governed project always refused, regardless
of the flag.

**After:** the "already governed" refusal now checks `args.force` and skips
the refusal (proceeding to overwrite) when set. Verified: `init` twice
without `--force` → second call exits 1; with `--force` → exits 0 and
rewrites.

## 4. Git-repo detection no longer silently drifts to the filesystem root

**Before:** if no `.git` was found by walking up from the target directory,
the loop just terminated when `walk == walk.parent` (filesystem root) and
used that as `root` anyway — silently trying to scaffold into `/` or
`C:\`. Separately, `_repo_root()`'s fallback (`Path(out.stdout.strip()) or
start`) never actually triggered, because `Path("")` is truthy in Python,
so a failed `git rev-parse` silently returned as if it had succeeded.

**After:** `_repo_root()` now returns `None` explicitly on failure (checks
`returncode` instead of relying on Python truthiness of empty strings).
`cmd_init` refuses outright — "not inside a git repository, run `git init`
first" — rather than guessing a root. Verified against a real non-git
directory: exit 1, nothing written.

## 5. `check_delete` fails closed on an unresolvable branch

**Before:** `sha, _ = run_git(["rev-parse", name]); if sha and not
content_preserved(sha):` — when `git rev-parse` couldn't resolve the branch
(bad ref, transient error, wrong working directory), `sha` came back empty,
the whole condition short-circuited to `False`, and the function fell
through to `return []` — i.e., "no violation, safe to delete" — for a
branch it had just failed to even identify. Applied to both the dev copy
(`scripts/guard_branch.py`) and the shipped copy
(`src/guardrail/template/scripts/guard_branch.py`), which had drifted
identical-but-separately.

**After:** an unresolvable branch now returns an explicit violation
("could not resolve this branch... refusing to approve deletion of
something that can't be verified") instead of silently passing. A new
regression test (`test_feature_delete_fails_closed_when_branch_unresolvable`)
locks this in; the existing content-preservation test was also fixed to
mock `run_git` directly instead of depending on a specific branch name
actually existing in whatever repo happens to run the suite (which is why
it failed when I ran it in a fresh checkout with no git history).

## New: `tests/test_init_smoke.py`

Every existing test imports `guardrail`/`scripts` modules straight from the
source checkout — none of them would ever have caught the packaging bug,
because they never go through an actual `pip install`. This new test
(marked `slow`) builds a real wheel, installs it into an isolated venv, and
runs `lawkeeper init` against a real `git init`-ed directory, asserting the
constitution and hooks actually land on disk. It also covers the
non-git-directory refusal and the `--force` behavior end-to-end. This is
the test that would have caught the original bug on day one.

Run it explicitly: `pytest tests/test_init_smoke.py -v` (needs `pip install
build`, included in the new `dev` extra).

## 6. Git hooks now land executable (found by actually running it)

**Before:** `_render()` writes hook files with `Path.write_text()`, which
doesn't preserve or set any file mode — every scaffolded hook landed as
`-rw-r--r--`. Git silently no-ops a non-executable hook (a soft "hint",
not an error) and the commit goes through with **zero enforcement**.
`install_hooks.py` printed "hooks ACTIVE" regardless. I only found this by
actually running the full flow — `init` → `install_hooks.py` → `git commit`
— against a real project, exactly as you asked. Every automated test in
this repo (including my new smoke test) checked that files existed, not
that they were executable, so nothing caught it until a real commit did.

**After:** the scaffold copy loop chmods anything under `scripts/git-hooks/`
+x at write time, and `install_hooks.py` independently re-checks and fixes
the bit itself (belt-and-suspenders — covers a fresh `git clone` or manual
copy that drops the bit again later, not just first `init`). Verified
against a clean project: hooks land `-rwxr-xr-x` with no manual chmod, a
commit containing `__pycache__` junk is correctly BLOCKED by the real
pre-commit hook, and a proper commit with a `GOVERNANCE-UPDATE` +
`Tests:` line goes through.

## New: lawkeeper-checker integration

`tools/lawkeeper-checker/` is the Rust edit-time syntax checker prototype
(6 rules, built and verified separately — see its own source comments).
It's now wired into `scripts/validate_pre_commit.py` as step 8: staged
`.rs` files get run through it if the binary is found (via
`LAWKEEPER_CHECKER_BIN` env var, or on PATH). If it's not found, the hook
prints a one-line note and continues — it never blocks a commit just
because the optional Rust tool isn't installed, since most Lawkeeper users
won't have it built.

Verified end-to-end, not just read: a real commit with a `.unwrap()`
violation in a fresh `.rs` file went through cleanly when the checker
wasn't on PATH, and was correctly BLOCKED with the exact violation message
once the checker was made available — then went through again once the
violation was actually fixed in the source.

## Status update (2026-09-04) — this list had gone stale

Two of the three items originally logged below as "still open" were fixed in
later commits, without this file ever being updated to say so — which
defeats the point of keeping a debt log at all. Corrected in place rather
than left to mislead the next reader:

- ~~CI's `dependency-locks` job calls nonexistent `compile_requirements.py`~~
  — **fixed** (commit `c7339de`): the job was removed outright, along with a
  separately-discovered bug where `powershell-lint` was mis-indented under
  `guard:` and had genuinely never run. See `.github/workflows/governance-guard.yml`.
- ~~`validate_commit_msg.py` silently uses an empty string for the commit
  message outside CI~~ — **fixed** (commit `ac64aef`): it now falls back to
  `git log -1 --format=%B` when run without a message-file argument, which
  is exactly what CI's push-only step needs.
- `scripts/compliance_watchdog.py`/`check_local_dependencies.py` hardcoding
  `backend/`/`woodwind_designer/` — **fixed** (commit `e0739f3`, generalized
  further in a later guardrail-fit-investigation pass): `scan_config.py` now
  auto-detects real `src/<package>/` directories, and every guard that used
  to hardcode those two names (`toolcheck.py`, `validate_pre_commit.py`'s
  placement rules and oversized-module allowlist, `validate_imports.py`'s
  deleted-module list, `compliance_watchdog.py`'s subsystem table) now uses
  it or reads project config instead. See
  `docs/GUARDRAIL_FIT_INVESTIGATION_2026-09-04.md` for the full audit.

Also fixed in that same later pass, not part of the original three:
`lawkeeper init` used to leave a freshly scaffolded project unable to pass
its own documented quickstart (`system_audit.py` FAILed immediately, before
any code was written, because the just-copied guard scripts tripped their
own rules with no baseline recorded yet); `init` now seeds one automatically.
The CI backstop's check sequence was also GitHub-Actions-only in practice
(the sequence existed nowhere outside that YAML) despite this project's own
stated goal of host independence; it's now `scripts/ci_checks.py`, a plain
script any CI (or none) can call. And `config.py` declared a whole
placement/regenerable/governance-files schema that nothing — not even its
own methods — ever read; deleted rather than left as unenforced-looking
documentation.

## Still genuinely open

- **`validate_pre_commit.py`'s step 5 (schema validation for instrument
  configs) calls `scripts/validate_instrument_configs.py`, which does not
  exist anywhere in this repo.** Found while auditing the same file for the
  `backend/`/`woodwind_designer/` cleanup above, but not fixed in that pass
  (different kind of bug — a missing script, not a blind spot — and this
  file had already grown a large diff). Currently harmless only because
  nothing in this repo stages a `config/*.json` file. It is NOT harmless for
  any project that adopts lawkeeper and organizes its own config under
  `config/*.json` (a common convention) — their commit would be BLOCKED by a
  subprocess call to a file that isn't there, with a confusing "config/*.json
  schema validation failed" error rather than "this check doesn't apply to
  you." This step is Windwright-specific domain logic (validating a specific
  instrument-config JSON schema) with no generic equivalent — it should
  likely be removed from the generic template entirely, the same reasoning
  already applied to the guard-blindness fixes above, rather than patched to
  degrade gracefully.
- `pip install lawkeeper` vs. `name = "guardrail"` mismatch — not re-checked
  in any later pass either; still exactly as originally logged below.
