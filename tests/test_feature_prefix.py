"""Tests for Config.feature_regexes() and the 2026-09-04 feature_prefix fix.

Two real bugs found together while investigating a branch-naming complaint,
not by inspection: (1) `feature_prefix` was a configurable field that
`feature_regexes()` never actually used -- it hardcoded the "opencode/..."
pattern directly, so editing the field in .guardrail.json silently did
nothing. (2) the default itself named a specific tool (OpenCode), which
misattributes work once a different tool does it. Fixed together: the
regex is now genuinely derived from `feature_prefix`, the default changed
to the tool-agnostic "agent/{topic}/{machine}", and the pre-fix default is
always additionally accepted so existing branches are never retroactively
orphaned.
"""

import json
from pathlib import Path

import pytest

from guardrail.config import Config


class TestFeaturePrefixDefault:
    def test_default_is_tool_agnostic(self):
        cfg = Config()
        assert cfg.feature_prefix == "agent/{topic}/{machine}"

    def test_new_convention_branch_accepted(self):
        cfg = Config()
        regexes = cfg.feature_regexes()
        assert any(r.match("agent/mesh-repair/desktop") for r in regexes)
        assert any(r.match("agent/mesh-repair/laptop") for r in regexes)

    def test_legacy_opencode_branch_still_accepted(self):
        """Existing branches created under the old convention must never
        become orphans just because the default changed."""
        cfg = Config()
        regexes = cfg.feature_regexes()
        assert any(r.match("opencode/mesh-repair/desktop") for r in regexes)

    def test_invalid_machine_rejected_in_both_conventions(self):
        cfg = Config()
        regexes = cfg.feature_regexes()
        assert not any(r.match("agent/mesh-repair/phone") for r in regexes)
        assert not any(r.match("opencode/mesh-repair/phone") for r in regexes)

    def test_unrelated_prefix_rejected(self):
        """A tool name that is neither the new nor the legacy convention
        must not be silently accepted -- this is acceptance-only for the
        two known conventions, not a wildcard."""
        cfg = Config()
        regexes = cfg.feature_regexes()
        assert not any(r.match("devin/mesh-repair/desktop") for r in regexes)


class TestFeaturePrefixConfigurable:
    def test_custom_prefix_from_guardrail_json(self, tmp_path):
        (tmp_path / ".guardrail.json").write_text(
            json.dumps({"feature_prefix": "work/{topic}/{machine}"}),
            encoding="utf-8",
        )
        cfg = Config.load(tmp_path)
        regexes = cfg.feature_regexes()
        assert any(r.match("work/mesh-repair/desktop") for r in regexes)

    def test_custom_prefix_does_not_disable_legacy_acceptance(self, tmp_path):
        """A repo that configures its own feature_prefix should still
        accept pre-existing "opencode/..." branches -- the legacy pattern
        is unconditional, not tied to what the configured prefix is."""
        (tmp_path / ".guardrail.json").write_text(
            json.dumps({"feature_prefix": "work/{topic}/{machine}"}),
            encoding="utf-8",
        )
        cfg = Config.load(tmp_path)
        regexes = cfg.feature_regexes()
        assert any(r.match("opencode/mesh-repair/desktop") for r in regexes)

    def test_custom_machines_reflected_in_both_regexes(self, tmp_path):
        (tmp_path / ".guardrail.json").write_text(
            json.dumps({"machines": ["desktop", "server"]}),
            encoding="utf-8",
        )
        cfg = Config.load(tmp_path)
        regexes = cfg.feature_regexes()
        assert any(r.match("agent/mesh-repair/server") for r in regexes)
        assert not any(r.match("agent/mesh-repair/laptop") for r in regexes)

    def test_malicious_prefix_cannot_inject_regex(self, tmp_path):
        """Adversarial: a .guardrail.json-supplied feature_prefix containing
        regex metacharacters must not change match semantics beyond its
        literal characters -- the template escaping must hold even when
        the input is deliberately hostile, not just well-formed."""
        (tmp_path / ".guardrail.json").write_text(
            json.dumps({"feature_prefix": ".*/{topic}/{machine}"}),
            encoding="utf-8",
        )
        cfg = Config.load(tmp_path)
        regexes = cfg.feature_regexes()
        # The literal ".*" prefix must be required verbatim, not treated as
        # a wildcard -- so a branch missing that literal text must still
        # fail to match this regex (the legacy regex is independent and
        # may or may not match; check the configured one specifically).
        configured = regexes[0]
        assert configured.match(".*/mesh-repair/desktop")
        assert not configured.match("anything/mesh-repair/desktop")
