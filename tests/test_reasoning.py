"""Tests for the hide/show internal-reasoning option (Law 12 discipline)."""

import json
from pathlib import Path

from guardrail.config import Config
from guardrail.core.primitives import CheckResult, Status
from guardrail.core.reasoning import emit, is_enabled
from guardrail.core.runner import Report


class TestConfigDefaults:
    def test_defaults_off(self):
        cfg = Config()
        assert cfg.show_internal_reasoning is False
        assert cfg.reasoning_log == "docs/reasoning.log"

    def test_loads_from_guardrail_json(self, tmp_path):
        (tmp_path / ".guardrail.json").write_text(
            json.dumps({"show_internal_reasoning": True, "reasoning_log": "docs/r.log"}),
            encoding="utf-8",
        )
        cfg = Config.load(tmp_path)
        assert cfg.show_internal_reasoning is True
        assert cfg.reasoning_log == "docs/r.log"


class TestEmit:
    def test_disabled_writes_nothing(self, tmp_path):
        cfg = Config()
        log = emit("secret reasoning", tmp_path, cfg)
        assert log == ""
        assert not (tmp_path / "docs/reasoning.log").exists()

    def test_enabled_appends_timestamped_entry(self, tmp_path):
        cfg = config_enabled()
        log = emit("why this branch", tmp_path, cfg)
        assert log == str(tmp_path / "docs/reasoning.log")
        content = (tmp_path / "docs/reasoning.log").read_text(encoding="utf-8")
        assert "why this branch" in content
        assert content.startswith("[")  # timestamp prefix

    def test_enabled_appends_multiple(self, tmp_path):
        cfg = config_enabled()
        emit("first", tmp_path, cfg)
        emit("second", tmp_path, cfg)
        content = (tmp_path / "docs/reasoning.log").read_text(encoding="utf-8")
        assert content.count("\n") == 2
        assert "first" in content and "second" in content


def config_enabled() -> Config:
    cfg = Config()
    cfg.show_internal_reasoning = True
    return cfg


class TestReportReasoning:
    def _report(self):
        return Report(
            [
                CheckResult(1, Status.FAIL, "README.md missing", {"file": "README.md"}),
                CheckResult(12, Status.PASS, "AGENTS.md present", {"file": "AGENTS.md"}),
            ],
            Path("."),
        )

    def test_hide_omits_details(self):
        out = self._report().human_text(show_reasoning=False)
        assert "details" not in out.lower()
        assert "file" not in out  # no per-law reasoning lines

    def test_show_includes_details(self):
        out = self._report().human_text(show_reasoning=True)
        assert "file:" in out  # reasoning details surfaced
        assert "README.md" in out
