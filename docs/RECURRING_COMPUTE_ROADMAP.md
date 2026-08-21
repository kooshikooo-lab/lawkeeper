# Recurring Compute Roadmap

Started 2026-08-21, per the user's explicit request: stop treating every
compute run as a one-off ask, and instead have a clear map of (a) what
we're actually working toward per project, (b) which processes should
just recur on their own because they're unambiguously in the right
direction, and (c) the real, correct mechanism for each -- not
everything belongs on the same kind of schedule.

## The one real constraint that shapes everything below

Checked directly before writing this plan, not assumed: this session's
`CronCreate` tool is **session-only** -- jobs live in this Claude
session's memory, nothing is written to disk, and even recurring jobs
auto-expire after 7 days. It cannot be the backbone for anything meant
to keep running for weeks or months, or to survive this conversation
ending. For that, the real, durable mechanism is the OS's own scheduler
(Windows Task Scheduler) or a persistent script, independent of any
Claude Code session being open. This roadmap uses each mechanism for
what it's actually good at:

- **Windows Task Scheduler** -- genuinely durable, unattended, long-term
  recurring jobs (daily/weekly). Right for anything that should keep
  happening even if no Claude session is open for days.
- **CronCreate (this session)** -- short-term, bounded check-ins during
  active work (hours to a few days, hard cap 7). Right for "keep an eye
  on the pipeline run every few hours while I'm around this week," wrong
  for "run this every day forever."
- **Manual/on-demand headless runs** (`opencode run`, as used tonight
  for the Windwright pipeline) -- right for heavy, judgment-requiring
  work that shouldn't fire blindly on a timer without someone able to
  redirect priorities first.

A second real constraint: this desktop has **one GPU (GTX 1060, 6GB)**.
The Windwright pipeline (Blender + image-gen), local-model inference
(opencode's coding assistant), and the hardware_scanner don't all need
GPU, but the ones that do can't run at full effectiveness simultaneously
-- scheduling needs to account for that, not assume infinite parallel
capacity.

---

## Per-project goals (what "the right direction" actually means)

### Windwright
Push toward genuinely best-possible-optimized instruments, with the
full pipeline (optimize -> STL -> Blender -> photorealistic image,
quality-gated against real reference photos) as the standing production
process, not a one-off demo. Secondary: keep resolving the real
settled-vs-debatable architecture questions already identified
(module-size threshold validity, further optimizer-algorithm
comparisons) with real data, not re-assertion.

### falcun
Real, citation-grounded research (the literature pipeline built
tonight) and a maturing invention-search system -- `ground_concept()` is
now confirmed working; the real next step is wiring in the
public-benefit/harm-avoidance dimension `RESEARCH_ETHICS.md` calls for,
not yet done. Longer-term: the evolutionary methodology as a reusable
"AI factory" pattern, not scoped to bug-hunting alone.

### lawkeeper
The downloadable Agent SDK prototype (Stage 1 done and committed;
Stages 2-4 -- porting governance checks, packaging, dogfooding -- not
started) and standing governance hygiene: orphan-script sweeps,
failure-pattern logging, keeping tools like hardware_scanner actually
maintained rather than built-once-and-forgotten (the exact Law 21
pattern already caught twice this session, in `model_switcher.py` and
`team_chat_monitor.py`).

### orbital-study
Mostly human-directed creative/canon work -- deliberately **not**
included in the recurring-automation list below. Worldbuilding decisions
are yours to make, not something to run on a schedule.

---

## Candidate recurring processes

| Process | Why it belongs here | Proposed cadence | Mechanism |
|---|---|---|---|
| Windwright full pipeline (optimize -> STL -> Blender -> image-gen) | The actual production process pushing toward better instruments | Triggered after any real algorithm/objective change, or ~weekly otherwise | Manual/on-demand headless run (needs judgment on which designs to target) |
| Full test suites, all 4 repos | Catches real regressions fast (found 5 real Windwright failures + a live corruption bug tonight, just by running it) | Nightly | Windows Task Scheduler |
| `hardware_scanner` | Literally built tonight to watch for deals over time -- worthless run once | Daily | Windows Task Scheduler (session-bound CronCreate is the wrong tool for this specifically -- its whole point is outliving any one session) |
| `system_audit.py` / `compliance_watchdog.py` / `orphan_scan.py` | Cheap, mechanical, catches drift before it accumulates (tonight's stale-WORKPLAN.md entry is a real example of what happens without this) | Weekly deep sweep (pre-commit hooks already cover the per-commit case) | Windows Task Scheduler |
| falcun literature refresh on tracked topics | Catches genuinely new papers without a person re-running searches by hand | Monthly | Windows Task Scheduler |
| Session/failure-pattern hygiene sweep (AI_FAILURE_PATTERNS review, loose-thread check) | The "don't leave work behind" discipline already established -- currently manual/ad hoc | End of each significant work session | Manual (needs judgment on what actually happened) |

---

## What this roadmap deliberately does not do

- It does not schedule anything yet. Cadence above is a real proposal,
  not a commitment -- Task Scheduler entries are a standing resource
  commitment across every future session, worth your explicit
  confirmation on frequency before they're created, not something to
  set silently.
- It does not attempt to run Windwright's pipeline and other GPU work
  concurrently -- the single-GPU constraint above means these need real
  sequencing, not naive parallelism.
- It does not include orbital-study -- creative/canon work stays
  human-paced.

## Immediate next step

Confirm cadence/priority for the table above (or adjust it), then set up
the real Windows Task Scheduler entries for the ones marked that way --
that's the part that needs doing once, correctly, rather than re-decided
every session.
