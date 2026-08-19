---
name: voice-input-offline-privacy
description: Deferred idea -- context-aware, fully offline voice input for lawkeeper/idea-organizer, plus a requirement that any future product's privacy terms be unambiguous enough to be trivially enforceable, not hedged boilerplate.
metadata:
  type: project
---

The user reflected (2026-08-19) on this session's voice-recognition
quality: they want voice input that (a) uses conversation/project context
to guess what was actually said, correcting transcription errors the way
Claude did manually all session ("law keeper" → lawkeeper, "Deep sick" →
Devin/opencode), and (b) never sends audio to a remote server — a
principled data-privacy stance, not just an accuracy preference. "One thing
that lawkeeper should have."

**Technical shape:** `whisper.cpp`/`whisper-rs` locally, with a
vocabulary-biasing/rescoring pass against known project terms — fully
offline. This sharpens (not duplicates) the idea-organizer app's already-
planned Phase 0 voice spike — see the plan file at
`C:\Users\Admin\.claude\plans\golden-puzzling-raccoon.md` (Claude-Code-side
plan file; may not be readable by other tools, but the requirement stands
on its own).

**The legal point, which the user was explicit and confident about:**
separate from the technical offline requirement, any future product's
privacy terms should be written specifically and unambiguously enough that
a breach would be trivially provable — "they could make a lawsuit and be
very confident that they would win because it's such a clear breach of
contract." Not vague "we take privacy seriously" language with hedges and
carve-outs. This is a concrete drafting instruction for task #58 (the
Bookchin-inspired company-structure/manifesto doc) whenever that gets
written, not just a technical design note.

Full detail: `lawkeeper/docs/FUTURE_DIRECTIONS.md` and task #86.

Related: [[ai-independence-goal]] (the same underlying anticapitalist /
data-sovereignty stance, applied here to voice input specifically rather
than the AI model itself). [[hermes-comparison-deferred]] (same
"deliberately deferred, catalog redundantly" pattern).
