# Session Round-Up — 2026-08-21

Requested directly: a deep search of this session for loose threads,
plus a complete, mechanical survey of unused/forgotten scripts across
repos. Part 1 is exhaustive (this session is fully in context). Part 2
was re-run to completion after an initial bounded pass was explicitly
rejected -- rebuilt as a real single-pass scanner, all 169 scripts
across 4 repos' scripts/tools directories actually checked, not
sampled.

---

## Part 1 -- This session's loose threads

### Real, unresolved, and worth closing
1. **Law 23's compressed text was never written back.** The user
   approved a 3-sentence compressed version of Law 23 in chat; the
   long-form version from commit `da5adc2` is still what's actually in
   `docs/AI_CONSTITUTION.md` (verified directly -- still present at
   line 340+). Real, simple fix, never done.
2. **Falcun's `ground_concept()` bug is still live.** Every genome in
   the invention-search module's test run falls through to the
   hardcoded `concept_a`/`concept_b` fallback -- confirmed still
   present in `src/falcun/invention/genome.py:511`, verified directly.
   Logged in `WORKPLAN.md` Phase 5, never actually fixed.
3. **`fitness.py` has no public-benefit/harm-avoidance dimension** per
   `RESEARCH_ETHICS.md` -- designed, logged, not built.
4. **Verification-tier tagging** (raw/mechanically_checked/
   panel_reviewed/expert_reviewed) -- designed in `RESEARCH_ETHICS.md`,
   not wired into Curio's note format or the invention genome's output.
5. **Law 23 Layer 3** (independent-audit surfacing tool) -- designed
   only, never built. The honest caveat from its own design stands: an
   AI checking another AI's claim is decorrelated, not immune.
6. **`sciwrite-lint` integration** into `consensus_review.py`'s science
   panel -- real, open-source, sourced tool identified, never wired in.
7. **Governance mechanism audit** (controlled-experiment methodology,
   `docs/RESEARCH_governance_mechanism_audit.md`) -- fully scoped, zero
   work started.
8. **`model_switcher.py`'s `audit`/`vision` roles** still point at
   `claude-opus-4.8`, confirmed still marked "KNOWN ISSUE: likely
   unavailable" in the code itself -- deliberately deferred, still
   deferred.
9. **Claude Code Stop hook** -- built, tested (12/12 passing in
   isolation), but the live test inside this actual session's managed
   environment never fired. Root cause genuinely unresolved (hosted-
   environment hook support vs. a missed hot-reload) -- needs a plain
   local `claude` CLI session to actually test in, which this session
   isn't.
10. **`E:\Admin\Lawkeeper` vs. the real repo mismatch** -- this
    session's actual Claude Code project root isn't the git repo it's
    been working in all night. Real, structural, not urgent, not
    resolved.
11. **The scheduled loose-thread-audit idea** (this section's own
    subject, proposed by the user mid-round-up) -- logged in
    `FUTURE_DIRECTIONS.md`, `mcp__scheduled-tasks__*` tools identified
    as the real mechanism, not yet investigated.
12. **Falcun's "manifesto" document** -- explicitly named as wanted,
    needs the user's direction on scope before drafting.
13. **Bioengineering research round** -- seeded with one item
    (bioprinted organoids), the rest of the negative-filter survey
    never run.
14. **Human enhancement research round** -- not surveyed at all.
15. **Phase 3 deep-dive on the 51 picked papers** -- full-text fetching
    just built and verified (10/10 real runs after fixing a real
    intermittent retry bug), but the actual synthesis pass across the
    51 papers hasn't started.
16. **The domain-vs-methodology two-axis tagging idea** (aging/
    biogerontology vs. engineering-biology-specifically) -- proposed in
    conversation, not yet applied to the 51 picks or built into any
    tool.

### Confirmed done, not loose (checked, not assumed)
- Law 22 amendment (hedge-phrase rule) -- committed, in
  `AI_CONSTITUTION.md`.
- `governance-recall` skill -- ported to lawkeeper and falcun, committed.
- The lawkeeper 3-way merge (origin/main + laptop's executor branch) --
  fully resolved, tested, pushed.
- `docs/RESEARCH_ETHICS.md` -- drafted, user-confirmed with 4
  additions, committed.
- `docs/examples/` consensus_review.py worked example -- committed.
- `scripts/claude_stop_hook.py` -- code itself verified correct (12
  real tests + manual reproduction of both historical failures); only
  the live-environment firing is unresolved (see #9 above).

---

## Part 2 -- Cross-repo unused/forgotten script survey (complete pass)

The first attempt used a shell loop doing one `grep -rl` per candidate
file, which timed out against Windwright's 132-script `scripts/`
directory (O(candidates x repo size)). Rebuilt as a proper single-pass
scanner (`orphan_scan.py`) that reads the whole repo once, builds one
haystack, then checks every candidate's basename against it -- O(repo
size) total. Ran to completion against all 4 repos' scripts/tools
directories, 169 scripts scanned in total. Test files (`test_*.py`) and
known one-off experiment/task-script naming patterns (`export_*`,
`refine_*`, `generate_*`, `validate_*_baseline`, etc. -- Windwright has
dozens, meant to be run manually per-experiment, "unreferenced" is
their normal correct state) are excluded from flagging, not silently
dropped from the count.

**Total real orphan candidates found: 17, across all 4 repos.**

### Windwright -- 14 candidates
- `scripts/train_lora.py` (1 commit, 12 days) -- LoRA fine-tuning for
  constitutional compliance. Connects directly to the user's stated
  long-term goal (local open-weight model + a harness robust enough to
  compensate for lower capability).
- `scripts/prepare_training_data.py` (1 commit, 12 days) -- pairs
  directly with `train_lora.py`; the whole local-model-training effort
  was built and abandoned together, same real thread, two files.
- `scripts/github_mcp.py` (2 commits, 2 days) -- substantial, real
  tool: wraps `gh` CLI as MCP tools for opencode (issues/PRs/releases/
  team channel, keyring-based token handling). Zero Python-level
  references is plausibly a false signal here -- an MCP tool is
  registered via config, not imported -- worth checking
  `opencode.jsonc`/MCP config directly before concluding it's actually
  unused.
- `scripts/github_updates_check.py` (2 commits, 2 days) -- explicitly
  documented as complementing `github_monitor.py` (wiki tracking,
  all-discussion coverage the main monitor doesn't do). Real, built
  intentionally as a companion, unclear if ever actually run.
- `scripts/propose_tasks.py` (3 commits, 2 days) -- generates/posts a
  real laptop-vs-desktop task-division proposal. 3 commits suggests
  real repeated use despite zero cross-references (plausible: a
  human-invoked coordination script, not meant to be imported).
- `scripts/worker_startup.py` (2 commits, 2 weeks) -- thin, no real
  docstring at the top, just an `install_package()` function. Real
  candidate for genuinely unclear/incomplete, not just "manually
  invoked."
- `scripts/view_browser.py` (1 commit, 2 weeks) -- small
  dev-convenience browser launcher. Legitimate manual-use utility; low
  signal of being forgotten just because nothing imports it.
- `scripts/_run_benchmark_live.py`, `debug_chalumier_compare.py`,
  `validate_chromatic_flute.py`, `verify_cone_theory.py`,
  `blender_render_scale_comparison.py`, `blender_render_stl.py`,
  `phase5_export_all.py` -- real orphan-shaped by the scanner's
  criteria, but names read as one-off debug/verify/export scripts that
  didn't match the naming-pattern exclusion list; not individually
  investigated further given real time already spent -- a real, honest
  residual, not swept away.

### Falcun -- 1 real candidate (of 2 flagged)
- `tools/gamification_test.py` (1 commit, 6 days) -- real, well-
  designed engagement-verification tool for Evolve-a-Life's game loop
  (lifespan/interest/novelty/agency metrics via an "easily-bored
  agent"). Built, apparently never run/reported on since. A real,
  proactive Law-23-adjacent check sitting unused.
- `tools/render_literature_html.py` flagged too, but this is a real
  false positive: built 39 minutes before this scan (this session's
  own work), invoked directly by hand as a CLI entry point, not meant
  to be referenced by other code. Not a genuine orphan.

### orbital-study -- 1 candidate
- `scripts/team_chat_monitor.py` (1 commit, 2 days) -- background
  monitor logging every team-chat comment (not machine-filtered) to a
  persistent local file specifically so an agent can see what arrived
  while idle. Directly relevant: this exact session hit repeated
  "other machine posted while you were typing, cursor not advanced"
  friction with `team_chat.py` tonight -- this tool looks built
  specifically to prevent that, and was never actually run.

### lawkeeper -- 0 candidates
Clean. (An earlier, cruder manual check flagged `memory_query.py` and
`check_declared_dependencies.py` as low-reference, but the real,
careful scanner found real external references to both once
self-references were correctly subtracted -- the cruder check was
wrong, corrected here rather than left standing.)

## Recommended next actions, in priority order
1. **`team_chat_monitor.py`** -- smallest fix, highest value: directly
   prevents a friction pattern that hit this exact session multiple
   times tonight. Run it / wire it in.
2. **`train_lora.py` + `prepare_training_data.py`** -- real,
   substantial work toward the user's own stated long-term local-model
   goal, abandoned mid-thread. Worth a real decision: pick back up, or
   explicitly mark superseded/abandoned with a reason (matching the
   "no permanent limbo" discipline used earlier tonight on Windwright's
   ADRs).
3. **`gamification_test.py`** -- real verification tool for whether
   Evolve-a-Life is actually engaging, never run. Cheap to actually run
   once and get a real answer.
4. **`github_mcp.py`** -- check the real MCP config before concluding
   anything; the zero-references signal may be a false negative for
   this specific file.
