---
name: research-cadence-improves-grounding
description: User feedback that periodic literature/research pauses measurably improve how well an agent understands the underlying theory before/during implementation, not just when something breaks.
metadata:
  type: feedback
---

Early in the Windwright project, the user more frequently asked agents
(including Claude instances) to pause and do real research (reading papers,
docs, prior art) before or during implementation work. They observed this
had a real, if imperfect, effect: the model seemed to genuinely internalize
the underlying theory better than when jumping straight into code, and this
"stuck" at least for the rest of that session.

**Why:** grounding in real sources catches things pure pattern-matching from
training data misses or gets subtly wrong — concrete example from
2026-08-18: reading Noreland et al. 2013 and Debut/Kergomard/Laloë 2005 in
full (not just searching for a quick answer) is what surfaced that a
mid-bore bore "bulge" in a Bass Clarinet in G design was a real
under-constrained-optimizer bug, not a discovery — real enlargements are
1.9-4.4mm near the mouthpiece, not a 270mm mid-bore feature. That grounding
also directly led to catching a second real bug (naive semitone-ratio
scaling of tonehole positions vs. the repo's own existing, correctly
bore-diameter-aware `hole_positions_for_scale` function).

**How to apply:** don't treat "look up real sources" as a one-off, reactive
step only taken when something looks wrong or an explicit fact-check is
requested. Build it into the regular working rhythm on this project —
periodically (e.g., before starting a new subsystem, when a result looks
surprising, or every so often during a long session) pause to read real,
primary sources (papers, the codebase's own docstrings/citations, official
docs) rather than relying purely on recalled/trained knowledge, even when
not explicitly asked to "fact-check" or "research" at that moment. This
applies to any agent working the project, not just ones explicitly asked to
research. Related: the 2026-08-18 knowledge base build
(`Windwright/docs/knowledge_base/INDEX.md`) exists partly to make this
cheaper to do going forward — real local papers, already indexed, no need
to re-search from scratch each time.
