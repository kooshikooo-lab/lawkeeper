"""Tests for UserPreferenceProvider. See docs/ADAPTIVE_INTERFACE_PLAN.md."""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC = REPO_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from guardrail.memory import UserPreferenceProvider


def _provider(tmp_path):
    return UserPreferenceProvider(store_path=tmp_path / "prefs.json")


def test_initialize_creates_default_profile_when_no_file_exists(tmp_path):
    provider = _provider(tmp_path)
    provider.initialize()
    assert provider._profile["style"] == "balanced"
    assert provider._profile["adhd_mode"] is False


def test_prefetch_lazily_initializes(tmp_path):
    provider = _provider(tmp_path)
    assert provider._initialized is False
    results = provider.prefetch("anything")
    assert provider._initialized is True
    assert isinstance(results, list)


def test_prefetch_returns_nothing_for_default_balanced_profile(tmp_path):
    """A profile with no corrections yet has nothing worth injecting --
    this must not manufacture a preference that hasn't been established."""
    provider = _provider(tmp_path)
    assert provider.prefetch("anything") == []


def test_sync_turn_detects_too_much_jargon_correction(tmp_path):
    provider = _provider(tmp_path)
    provider.sync_turn("that's a whole lot of jargon", "response text")
    assert provider._profile["jargon_corrections"] == 1
    assert provider._profile["style"] == "simplify_more"


def test_sync_turn_detects_dont_dumb_down_correction(tmp_path):
    provider = _provider(tmp_path)
    provider.sync_turn("don't dumb it down", "response text")
    assert provider._profile["dumbed_down_corrections"] == 1
    assert provider._profile["style"] == "less_simplify"


def test_sync_turn_ignores_unrelated_text(tmp_path):
    provider = _provider(tmp_path)
    provider.sync_turn("what's the weather like", "response text")
    assert provider._profile["jargon_corrections"] == 0
    assert provider._profile["dumbed_down_corrections"] == 0
    assert provider._profile["style"] == "balanced"


def test_sync_turn_detects_adhd_mode_trigger(tmp_path):
    provider = _provider(tmp_path)
    provider.sync_turn("can you turn on adhd mode", "response text")
    assert provider._profile["adhd_mode"] is True


def test_prefetch_after_correction_returns_the_style_preference(tmp_path):
    provider = _provider(tmp_path)
    provider.sync_turn("that's a whole lot of jargon", "response text")
    results = provider.prefetch("anything")
    assert len(results) == 1
    assert "simplify_more" in results[0].text


def test_prefetch_after_adhd_trigger_returns_the_formatting_rules(tmp_path):
    provider = _provider(tmp_path)
    provider.sync_turn("get to the point", "response text")
    results = provider.prefetch("anything")
    texts = " ".join(r.text for r in results)
    assert "ADHD mode is ON" in texts
    assert "cap lists at 5" in texts


def test_profile_persists_across_provider_instances(tmp_path):
    """The whole point of persisting to disk: a correction made in one
    session must still apply in the next one."""
    store = tmp_path / "prefs.json"
    first = UserPreferenceProvider(store_path=store)
    first.sync_turn("that's a whole lot of jargon", "response")

    second = UserPreferenceProvider(store_path=store)
    second.initialize()
    assert second._profile["jargon_corrections"] == 1
    assert second._profile["style"] == "simplify_more"


def test_shutdown_saves_even_without_explicit_sync_turn_save(tmp_path):
    store = tmp_path / "prefs.json"
    provider = UserPreferenceProvider(store_path=store)
    provider.initialize()
    provider._profile["adhd_mode"] = True  # mutate directly, bypass sync_turn
    provider.shutdown()

    reloaded = UserPreferenceProvider(store_path=store)
    reloaded.initialize()
    assert reloaded._profile["adhd_mode"] is True


def test_corrupted_store_file_falls_back_to_default_instead_of_crashing(tmp_path):
    store = tmp_path / "prefs.json"
    store.write_text("not valid json {{{", encoding="utf-8")
    provider = UserPreferenceProvider(store_path=store)
    provider.initialize()  # must not raise
    assert provider._profile["style"] == "balanced"


def test_word_boundary_no_false_positive_on_dont_dumb_down():
    """'i know what api is' should not match some unrelated word
    containing 'dumb' or similar -- word-boundary safety, same lesson
    already logged in AI_FAILURE_PATTERNS.md (2026-08-19, LAW 16,
    'temp' matching inside 'template')."""
    import re
    from guardrail.memory.user_preference_provider import _DUMBED_DOWN_RE
    assert not any(p.search("this is a dumbwaiter") for p in _DUMBED_DOWN_RE)
