# Governance mechanism audit — does it actually work, empirically

Queued 2026-08-20 from the user, directly following the Law 23 incident.
Not started yet — this file scopes it so it isn't lost, per Law 12's own
discipline (a real `Re-check when:`, not a vague someday).

## The ask, precisely

Three related but distinct things get called "the constitution" loosely,
and the audit needs to check each, not just the prose:
1. **The prose** — `AI_CONSTITUTION.md`'s laws themselves.
2. **The code** — git hooks, `validate_commit_msg.py`/`validate_pre_commit.py`/
   `guard_branch.py` (the only 3 laws actually mechanically enforced, per
   tonight's own earlier finding), `compliance_watchdog.py`, etc.
3. **Adaptive mechanisms** — the memory-provider system
   (`src/guardrail/memory/`), anything that changes agent behavior based
   on accumulated state rather than a fixed rule.

The audit's real question for all three, in every repo where applicable
(mainly lawkeeper, but the same mechanisms exist in Windwright/orbital-
study/falcun too): **does this actually change what happens, measurably,
or does it just exist?** Same spirit as Law 21 ("a capability with no
consumer is a bug") but broadened from "is it consumed" to "does it
actually work when consumed."

## Proposed methodology — controlled comparison, not just reading the code

Same experimental discipline already used once tonight (the gradient-vs-
NSGA-II optimizer comparison in Windwright, `docs/EXPERIMENT_optimizer_competition.md`)
applied to governance itself, not code architecture:

1. **Test branches with varied rule-set configurations** — different hook
   implementations, different subsets/wordings of constitution laws,
   different compliance-check configurations, run in parallel.
2. **Assign very similar (not identical) tasks** to opencode/Claude under
   each variant. The user's own caught methodological point: literally
   the same task twice isn't a fair trial — an agent that already did it
   once has different priors on the second pass, so the tasks need to be
   comparable in difficulty/shape but not identical.
3. **Compare outcomes empirically** — did the varied rule set actually
   catch a problem the other didn't, produce a different real decision,
   change what got verified before being reported done? Real measurements
   (did it block a bad commit, did it produce a `Human-check:` claim, did
   the claim turn out true on inspection), not impressions.

## Open design questions (not yet resolved)

- What counts as a fair "very similar task" pair -- needs real thought,
  flagged by the user as the hard part, not solved here.
- Scope: lawkeeper's own mechanisms first (it's the canonical source),
  then check whether Windwright/orbital-study/falcun's copies have drifted
  from lawkeeper's version or diverged in ways that matter.
- Whether this needs dedicated test branches per repo, or one shared
  experimental harness that can point at any of them.

## Re-check when

Before the next major governance change is proposed, or when there is a
multi-hour unattended window available to actually run controlled
comparisons (this needs real wall-clock time across parallel branches,
not a quick pass).
