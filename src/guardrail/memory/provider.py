"""MemoryProvider: a pluggable interface for durable, cross-session memory.

Adapted from Hermes Agent's `agent/memory_provider.py`, per the comparison
in docs/FUTURE_DIRECTIONS.md ("Adopt Hermes's memory-provider pattern (not
its verification model)"). What's adopted: the interface shape (an
`initialize` / `prefetch` / `sync_turn` / `shutdown` lifecycle) and the
core idea that `prefetch(query)` runs *before every turn*, keyed on the
incoming message, so only relevant memory is injected instead of a whole
file being read manually.

What is deliberately NOT adopted: Hermes's soft in-context verification
nudges (`agent/verify_hooks.py`) -- text appended to a conversation
encouraging a model to check its work, with nothing mechanically
enforcing it. That is the opposite of Law 16 ("guards MUST NOT depend on
the agent being well-behaved"). This module is retrieval only; it has no
opinion about verification, which stays exactly where lawkeeper already
enforces it -- mechanical hooks, not prompts.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class MemoryEntry:
    """One retrieved memory, scored for relevance to a specific query."""

    id: str
    text: str
    source: str
    relevance: float = 0.0


class MemoryProvider(ABC):
    """Pluggable memory-provider interface.

    Lifecycle: call `initialize()` once per process/session. Call
    `prefetch(query)` before every turn, keyed on the incoming message --
    that is the property worth adopting from Hermes: relevance-based
    injection instead of a human (or agent) having to remember to open a
    file. `sync_turn` and `shutdown` are optional hooks with no-op
    defaults; override them only if a concrete provider needs to persist
    something after a turn or release a resource at the end.
    """

    @abstractmethod
    def initialize(self) -> None:
        """Load/prepare whatever the provider needs. Called once."""

    @abstractmethod
    def prefetch(self, query: str, limit: int = 5) -> list[MemoryEntry]:
        """Return up to `limit` memories relevant to `query`, most relevant first.

        Must be safe to call before `initialize()` -- concrete providers
        should lazily initialize on first use rather than raise, since the
        whole point is this runs automatically before every turn, not as
        a step an agent has to remember to invoke first.
        """

    def sync_turn(self, query: str, response: str) -> None:
        """Optional: record something from a completed turn. No-op by default."""
        return None

    def shutdown(self) -> None:
        """Optional: release resources. No-op by default."""
        return None
