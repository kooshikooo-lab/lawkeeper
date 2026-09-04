"""Memory-provider subsystem.

Adopts Hermes Agent's `MemoryProvider` *pattern* (the interface shape and
the prefetch-before-turn injection idea) -- not its verification model.
See docs/FUTURE_DIRECTIONS.md, "Adopt Hermes's memory-provider pattern
(not its verification model)" for the full comparison and rationale.
"""

from .provider import MemoryEntry, MemoryProvider
from .failure_pattern_provider import FailurePatternMemoryProvider
from .user_preference_provider import UserPreferenceProvider

__all__ = [
    "MemoryEntry", "MemoryProvider",
    "FailurePatternMemoryProvider", "UserPreferenceProvider",
]
