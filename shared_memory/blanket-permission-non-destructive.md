---
name: blanket-permission-non-destructive
description: User grants standing permission to proceed through multi-step work without pausing to ask, except for genuinely destructive actions.
metadata:
  type: feedback
---

The user has given blanket permission to continue through investigation and
routine work (reading files, running more analysis, continuing a review
pass, committing/pushing verified fixes, etc.) without stopping to ask
"should I continue?" at each step.

**Why:** Explicitly stated 2026-08-18: repeatedly pausing for confirmation on
non-destructive continuation is experienced as annoying, not careful. This
extends an earlier, narrower version of the same feedback ("don't ask
permission to just read files").

**How to apply:** Keep moving through multi-step work (reviews, research
passes, verification, committing already-reviewed changes) without a
check-in prompt, as long as the action isn't one of:
- deleting or moving the user's personal files,
- deleting a branch,
- or anything else in the standing prohibited/permission-required
  categories (financial transactions, credentials, publishing/posting
  publicly, changing account/security settings, permanently deleting data).

Those categories still require an explicit ask or are off-limits entirely —
this permission grant doesn't waive them, it waives the *routine* check-ins
around ordinary work. When genuinely unsure whether something crosses into
one of those categories, ask; otherwise, proceed.
