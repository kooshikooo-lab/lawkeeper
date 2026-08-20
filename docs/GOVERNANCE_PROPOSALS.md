# Governance Proposals — pending user decision

Three questions surfaced live during the 2026-08-19/20 overnight session
that are genuinely the user's call, not mine to originate. Per the user's
own instruction ("logged... not decided"), nothing below has been acted
on beyond drafting a recommendation. This doc exists so "logged for
discussion" has a real, findable home instead of scattering across
Discussion #23 comments — see [[research-cadence-improves-grounding]] and
the failure pattern this whole doc is a response to
(`docs/AI_FAILURE_PATTERNS.md`, deferred-items-never-resurface entry).

**Status convention:** each item is `OPEN` until the user picks an option
(or a different one), at which point it moves to `AI_CONSTITUTION.md` (if
it's a standing rule) or gets marked `RESOLVED: <date>, <what was
decided>` and left here for the record.

---

## 1. Technical-vs-directional decision flagging

**OPEN.**

**The problem, in the user's own words:** "there's a flaw with the AI
where it... asks me for technical decisions that I don't think... I don't
care... but then sometimes it makes decisions that it seems to not
understand that these decisions are affecting things in a way that is
much more unwanted." Two failure directions, not one: over-asking on
trivial technical choices (annoying) and under-asking on choices that
quietly change direction (worse — silently narrows or redirects the
actual outcome).

**What happened live that illustrates both sides:**
- Laptop-opencode hit a genuine case of this correctly: independently
  verifying issue #67's real scope, then explicitly separating "fix issue
  #40" (uncontroversial bug fix, went ahead without asking) from "which
  Tauri UI automation approach" (a real fork in what gets built, held
  open). See Windwright Discussion #23, 2026-08-20T12:12–12:43.
- The orbital-study `quality`-vs-`mechanics` fitness-weight question
  (`STEPS_1_4_SUMMARY.md`) is the same pattern on my side: raised
  `mechanics` (verified non-directional signal), declined to touch
  `quality` (verified it would push toward narrative polish, a real
  direction change), and wrote down why instead of picking silently.

**Candidate heuristic** (not yet a rule — proposing it as a starting
point): a choice is *technical* (proceed without asking) when reversing
it later costs little and it doesn't change what the output represents
or means. A choice is *directional* (ask, or hold and flag) when it
changes what gets built, what's true about the content, or forecloses an
option the user might have wanted — even if the immediate code change is
small. Weight/threshold tuning that changes *content selection criteria*
(like the `quality` case) reads as directional under this test even
though it's a one-line diff; a library/refactor/formatting choice reads
as technical even when it touches many files.

**Recommendation:** adopt something like the above as a new
`AI_CONSTITUTION.md` law, with 2-3 worked examples (the two above are
real ones) rather than a purely abstract definition — abstract rules are
exactly what produced the current miscalibration.

**Re-check when:** the user reviews this doc, or a third live example of
the same ambiguity comes up before then (log it as a bullet here rather
than re-deciding ad hoc).

---

## 2. Commit / push / audit cadence

**OPEN.**

**The problem:** during autonomous multi-hour work, how often should an
agent commit, how often (if ever) should it push without being asked, and
how often should it run a self-audit (`scripts/system_audit.py` or
equivalent)? Current de facto practice this session: commit after every
verified step, never push, no fixed audit cadence (audits happened
reactively, triggered by the user noticing something looked off — see the
orbital-study working-tree collision, resolved by separating into
`f0d409f` + `74bddeb`).

**Why it matters concretely:** the working-tree collision happened
*because* two autonomous sessions (this one, and the user's own GUI
opencode session) had uncommitted work sitting in the same tree at once
with no push/audit checkpoint forcing either side to notice. A fixed
cadence would have caught it sooner; no cadence at all relies on the user
happening to look.

**Options, not a recommendation** (this one is more clearly a values
question — how much autonomy vs. how much checkpoint-visibility — than a
technical one, so no default is proposed):
- **(a) Commit-only, ever.** Push is always an explicit ask. Simplest,
  safest, but the user has to actively pull/check to see remote state.
- **(b) Commit per verified step, push on a timer** (e.g. every N commits
  or every hour of active work) regardless of whether the user is
  present. Gives remote visibility without per-push asks, but means an
  agent can push work the user hasn't seen yet.
- **(c) Commit per verified step, push only at natural stopping points**
  (a plan's own checkpoint, like this session did after
  `STEPS_1_4_SUMMARY.md`) — a middle ground between (a) and (b).
- **Audit cadence, independent of the above:** run `system_audit.py` (or
  the per-repo equivalent) at a fixed interval (e.g. every hour of
  autonomous work) rather than only reactively.

**Re-check when:** the user reviews this doc.

---

## 3. Naesann Causeway / procedural-name-as-canon policy

**OPEN.**

**The problem:** orbital-study's character-removal work (commit
`74bddeb`, 2026-08-20) removed all AI-invented hardcoded character
content per explicit user directive. One item was deliberately left
unresolved rather than folded into that mechanical fix: some
*procedurally-generated* names (e.g. "Naesann Causeway") appear in
historical version packs under `versions/` (now gitignored per
`STEPS_1_4_SUMMARY.md`, but pre-existing exports may still reference
them) and in `runs/pending_narrative_promotions.jsonl`. These are not the
specifically-named hand-authored characters the user objected to (Veya,
Iri, Sorel, etc.) — they're outputs of the generator doing exactly what
it's designed to do (procedural name synthesis via
`_CHAR_NAME_PREFIXES`/`_CHAR_NAME_SUFFIXES` in `scene_grammar.py`).

**Why this is a distinct question from the character removal:** the
character removal was about content *authored by the AI outside its
role* (writing lore/personality/backstory unprompted). Procedural name
generation is the AI doing its actual, requested job (the evolutionary
generator). Whether *output of the sanctioned generator* should also be
scrubbed from historical packs is a scope question about how far
"nothing AI-invented without explicit ask" extends — not an oversight in
the original fix.

**Options:**
- **(a) Leave historical packs as-is** — they represent what the
  generator actually produced under the (now-improved) system; only new
  runs need to be clean, which Step 1's verification already confirmed
  they are.
- **(b) Retroactively regenerate/purge** old packs containing procedural
  names, treating "canon" as needing to be clean going all the way back.

**Recommendation:** (a) — the generator's procedural output isn't the
thing the user objected to, and Step 1 already confirms new runs are
clean going forward, which was the actual concern. But this is flagged as
a recommendation, not a decision, since it touches what "canon" means for
the project.

**Re-check when:** the user reviews this doc.
