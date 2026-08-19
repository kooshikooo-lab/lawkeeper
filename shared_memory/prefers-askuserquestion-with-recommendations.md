---
name: prefers-askuserquestion-with-recommendations
description: User likes a checkbox-style UI for important decisions, especially with a clearly marked recommended option and reasoning. (Claude-specific tool; other agents should approximate with a clearly labeled recommended option in plain text.)
metadata:
  type: feedback
---

For important/multi-option decisions, use a checkbox/multiple-choice format
rather than asking in unstructured prose, and mark the recommended option
clearly (with a one-line reason) when one exists. In Claude Code this is the
`AskUserQuestion` tool specifically; an agent without that tool should still
follow the underlying preference — a short, labeled list of concrete
options with the recommended one called out and justified, not just an
open-ended "what do you want to do?"

**Why:** Confirmed directly (2026-08-19, while relaying a 5-question decision
post from GitHub Discussion #23): the user said they like this format and
want it used whenever there are important decisions — specifically because
seeing the recommendation alongside the reasoning lets them quickly agree
with it when the reasoning checks out, rather than having to reconstruct
the tradeoffs themselves from prose.

**How to apply:** When a real decision point has 2-4 concrete options (not
just open-ended questions), default to a structured choice format over
plain-text asking. Put the recommended option first, label it clearly
("(Recommended)"), and give its reasoning explicitly — don't just assert
it's recommended. Note (2026-08-19): the `AskUserQuestion` widget's
click-boxes have been observed not registering clicks in this environment —
if a structured question tool is unresponsive, fall back to a plain-text
numbered list immediately rather than retrying the same broken widget.

Related: [[research-cadence-improves-grounding]] — same session, same
discipline of grounding claims/recommendations in something checkable
rather than just asserting them.
