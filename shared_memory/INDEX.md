# Shared Memory Index

One line per entry, newest-relevant first. See `README.md` for the format
and how any agent should use this. Keep this list in sync when adding or
retiring entries.

- [AI-independence goal](ai-independence-goal.md) — user is anticapitalist, doesn't intend to keep using paid Claude Code long-term; plans a local-first open-weight model with a first-party (never third-party) remote-compute fallback, plus a harness (lawkeeper) robust enough to compensate for lower model capability. Reframes lawkeeper's true priority.
- [Offline voice input + privacy contract](voice-input-offline-privacy.md) — deferred idea: context-aware fully-offline voice transcription for lawkeeper/idea-organizer, plus a requirement that any future product's privacy terms be unambiguous enough to be trivially enforceable, not hedged boilerplate.
- [Hermes-comparison direction, deliberately deferred](hermes-comparison-deferred.md) — adopting Hermes Agent's memory-provider pattern (not its verification model) for lawkeeper is a real future direction, explicitly not active work; full detail in lawkeeper/docs/FUTURE_DIRECTIONS.md and task #85.
- [Same-machine: read files directly, don't relay through chat](same-machine-direct-file-access-not-chat-relay.md) — when Claude and opencode are co-located on one box, read the other's log/state files directly instead of posting to team_chat.py and waiting for a reply; applies symmetrically to every agent.
- [Falcun's broader vision](falcun-broader-vision.md) — current code (evolving bug-hunting prompts) is only one instance of a broader "AI factory" / automated-research-and-discovery vision; evolutionary methodology is meant to be reusable across domains, not scoped to bug-hunting.
- [Explain jargon, don't dumb down](explain-jargon-not-dumbed-down.md) — user is smart with a strong vocabulary, just not a coder; define coding-specific terms inline rather than simplifying the whole explanation to a childlike level.
- [Prefers a labeled-recommendation choice format](prefers-askuserquestion-with-recommendations.md) — use a structured multiple-choice format for important decisions, mark the recommended option with its reason; Claude Code's `AskUserQuestion` widget has been observed unresponsive — fall back to plain text if a structured tool doesn't register clicks.
- [Research cadence improves grounding](research-cadence-improves-grounding.md) — periodically read real primary sources during work, not just when explicitly asked to fact-check; catches real bugs pattern-matching alone misses.
- [Blanket permission for non-destructive work](blanket-permission-non-destructive.md) — don't pause to ask "should I continue?"; only genuinely destructive actions (delete/move personal files, delete a branch, etc.) need a check-in.
