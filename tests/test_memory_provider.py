"""Tests for the MemoryProvider abstraction and its failure-pattern
implementation. See docs/FUTURE_DIRECTIONS.md, "Adopt Hermes's
memory-provider pattern (not its verification model)".
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC = REPO_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from guardrail.memory import FailurePatternMemoryProvider, MemoryEntry, MemoryProvider


def test_memory_provider_is_abstract():
    """MemoryProvider itself cannot be instantiated -- concrete providers
    must implement initialize() and prefetch()."""
    import pytest

    with pytest.raises(TypeError):
        MemoryProvider()  # type: ignore[abstract]


def test_failure_pattern_provider_initializes_and_loads_real_corpus():
    provider = FailurePatternMemoryProvider()
    provider.initialize()
    assert provider._initialized is True
    # The real corpus (Windwright + lawkeeper AI_FAILURE_PATTERNS.md) has
    # dozens of entries as of 2026-08-20 -- assert a conservative floor,
    # not an exact count, so this doesn't break every time a new entry is
    # added.
    assert len(provider._corpus) >= 10


def test_prefetch_lazily_initializes():
    """prefetch() must work even if initialize() was never called first --
    that is the whole point of 'runs automatically before every turn'."""
    provider = FailurePatternMemoryProvider()
    assert provider._initialized is False
    results = provider.prefetch("permission wall external directory headless dispatch")
    assert provider._initialized is True
    assert isinstance(results, list)


def test_prefetch_finds_relevant_entry_for_a_real_query():
    """Query wording drawn from tonight's actual external_directory
    failure-pattern entry -- must retrieve it, not just return *something*."""
    provider = FailurePatternMemoryProvider()
    results = provider.prefetch("headless dispatch external_directory permission wall sibling repo")
    assert len(results) > 0
    assert all(isinstance(r, MemoryEntry) for r in results)
    combined_text = " ".join(r.text.lower() for r in results)
    assert "external_directory" in combined_text or "external directory" in combined_text


def test_prefetch_ranks_by_relevance_descending():
    provider = FailurePatternMemoryProvider()
    results = provider.prefetch("headless dispatch external_directory permission wall sibling repo", limit=10)
    relevances = [r.relevance for r in results]
    assert relevances == sorted(relevances, reverse=True)


def test_prefetch_respects_limit():
    provider = FailurePatternMemoryProvider()
    results = provider.prefetch("law severity fix root cause", limit=2)
    assert len(results) <= 2


def test_prefetch_empty_query_returns_nothing():
    provider = FailurePatternMemoryProvider()
    assert provider.prefetch("") == []


def test_prefetch_nonsense_query_returns_nothing():
    provider = FailurePatternMemoryProvider()
    results = provider.prefetch("zzqxvbnm qwvxjklp nonexistent gibberish")
    assert results == []


def test_sync_turn_and_shutdown_are_safe_no_ops_by_default():
    """Concrete providers only need to override these if they actually
    persist something -- the base class must not require it."""
    provider = FailurePatternMemoryProvider()
    provider.sync_turn("some query", "some response")
    provider.shutdown()
