"""Tests for Config.merge_regex() and the 2026-09-06 merge_prefix fix.

Same real bug shape as tests/test_feature_prefix.py's feature_prefix fix
(2026-09-04), found by checking every Config field systematically
(guardrail fit investigation, task 4) rather than stopping at the one
already known: `merge_prefix` was a configurable field
scripts/guard_branch.py's classify() never actually used -- it hardcoded
`r"^merge/[a-z0-9-]+$"` directly, so editing the field in .guardrail.json
silently did nothing. Fixed: the regex is now genuinely derived from
`merge_prefix`.
"""

import json

from guardrail.config import Config


class TestMergePrefixDefault:
    def test_default_is_merge_topic(self):
        cfg = Config()
        assert cfg.merge_prefix == "merge/{topic}"

    def test_default_pattern_accepted(self):
        cfg = Config()
        assert cfg.merge_regex().match("merge/governance")

    def test_unrelated_prefix_rejected(self):
        cfg = Config()
        assert not cfg.merge_regex().match("staging/governance")
        assert not cfg.merge_regex().match("merge-governance")


class TestMergePrefixConfigurable:
    def test_custom_prefix_from_guardrail_json(self, tmp_path):
        (tmp_path / ".guardrail.json").write_text(
            json.dumps({"merge_prefix": "staging/{topic}"}),
            encoding="utf-8",
        )
        cfg = Config.load(tmp_path)
        assert cfg.merge_regex().match("staging/governance")

    def test_old_default_no_longer_matches_a_custom_prefix(self, tmp_path):
        """Unlike feature_prefix, merge_prefix has no legacy-acceptance
        carve-out (no prior rename happened for it) -- a project that
        configures a custom prefix genuinely replaces the default, it
        doesn't additionally accept it."""
        (tmp_path / ".guardrail.json").write_text(
            json.dumps({"merge_prefix": "staging/{topic}"}),
            encoding="utf-8",
        )
        cfg = Config.load(tmp_path)
        assert not cfg.merge_regex().match("merge/governance")

    def test_malicious_prefix_cannot_inject_regex(self, tmp_path):
        """Adversarial, same discipline as test_feature_prefix.py's
        equivalent: a .guardrail.json-supplied merge_prefix containing
        regex metacharacters must not change match semantics beyond its
        literal characters."""
        (tmp_path / ".guardrail.json").write_text(
            json.dumps({"merge_prefix": ".*/{topic}"}),
            encoding="utf-8",
        )
        cfg = Config.load(tmp_path)
        regex = cfg.merge_regex()
        assert regex.match(".*/governance")
        assert not regex.match("anything/governance")
