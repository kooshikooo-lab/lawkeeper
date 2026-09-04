---
name: user-quality-standard-escalation-and-cross-repo-sharing-2026-09-04
description: Direct user directive tonight -- quality/constitution-compliance standard needs to increase substantially across all sessions/repos, and tools/solutions found in one repo must always be checked for portability to the others, not left siloed.
metadata:
  type: feedback
---

Written by a Claude session working in Windwright (same machine), per
direct instruction to relay this here too, not just in Windwright. The
user's own words, not paraphrased soft:

> a lot of sloppiness when it comes to following the constitution... the
> whole repo should be audited... not only in that regard... we need to
> have a solid testing mechanism... tools built and not wired in is way
> worse than no tools built — it's like an illusion, leading you astray...
> the standard needs to be increased substantially, right now things are
> dysfunctional.

> all tools found in one repo should always be checked for its
> applicability in other repos. There's been a lot of tools found in one
> repo or in one branch that has not been ported where it should be...
> having solutions in one repo that is not implemented in another — it's
> horrible.

**Why:** stated directly, applies to every session/agent working across
this user's projects (Windwright, Lawkeeper, Falcun), not scoped to one.
Two distinct, concrete standards, not just a mood:
1. A tool/script that exists but isn't wired into a real enforcement
   point (git hook, CI, an audit script that actually runs) does not
   count as done — check this for anything new, here or elsewhere.
2. Before building something, check whether it already exists in one of
   the other repos and should be ported in, not rebuilt; after building
   something here that isn't Lawkeeper-specific, check whether Windwright
   or Falcun should have it too.

**How to apply:** concretely, right now — two real, already-verified
candidates from tonight's Windwright session worth checking against
Lawkeeper's own scope:
- `scripts/validate_locked_constants.py` + `scripts/check_tool_
  registry.py` (already flagged in [[windwright-cosmic-ray-works-native-
  windows-not-wsl]], now actually wired into Windwright's real commit-msg
  hook and `system_audit.py`, not just standalone anymore).
- `import-linter` (PyPI, real, mature) — Windwright just used it to catch
  a real, live architecture violation on its first run (a `backend`
  module importing from the GUI package). If Lawkeeper's own guardrail
  template has similar layering rules it wants enforced (this project's
  own README already frames it as "mechanical policy that blocks bad
  commits"), this is a real, working example of exactly that pattern for
  import-boundary rules specifically, not something to reinvent.

Full detail, if useful: `docs/research/RESULT_import_linter_and_physics_
constant_audit_2026-09-04.md` in Windwright, on the consolidation-staging
worktree (`merge/audio-synthesis-consolidated-2026-09-04-work`, at
`C:\Users\Admin\Desktop\windwright-audio-consolidation` — same machine,
same direct-file-access convention this note itself follows, see
[[same-machine-direct-file-access-not-chat-relay]]).
