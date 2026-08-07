"""Tests for the checkbox-choice protocol (guardrail.choices + `lawkeeper choose`)."""
from __future__ import annotations

import json
import subprocess
import sys
from io import StringIO
from pathlib import Path

import pytest

from guardrail.choices import (Choice, ChoiceResult, ask, conflicts_violations,
                               load_spec, resolve_token, spec_to_choices, validate)


SAMPLE = [
    Choice("1", "Opus", conflicts=("2",)),
    Choice("2", "Haiku"),
    Choice("o", "Other", custom=True),
]


def test_resolve_token_by_id_and_index():
    assert resolve_token("1", SAMPLE) == "1"
    assert resolve_token("2", SAMPLE) == "2"
    assert resolve_token("3", SAMPLE) == "o"  # 1-based position
    assert resolve_token("0", SAMPLE) is None
    assert resolve_token("99", SAMPLE) is None
    assert resolve_token("nope", SAMPLE) is None


def test_conflicts_violations_empty_when_ok():
    assert conflicts_violations(SAMPLE, ["1"]) == []
    assert conflicts_violations(SAMPLE, []) == []


def test_conflicts_violations_detected():
    v = conflicts_violations(SAMPLE, ["1", "2"])
    assert len(v) == 1
    assert "Opus" in v[0] and "Haiku" in v[0]


def test_validate_accepts_non_conflicting():
    res = validate(SAMPLE, ["1"], None)
    assert res.selected == ["1"]
    assert res.cancelled is False
    assert res.custom is None


def test_validate_rejects_conflicting():
    res = validate(SAMPLE, ["1", "2"], None)
    assert res.cancelled is True


def test_ask_single_toggle_done():
    out = StringIO()
    res = ask("Title", "Body", SAMPLE, input_lines=["1", "done"], out=out)
    assert res.selected == ["1"]
    assert res.cancelled is False


def test_ask_unknown_token_ignored_then_done():
    out = StringIO()
    res = ask("Title", "", SAMPLE, input_lines=["nope", "2", "done"], out=out)
    assert res.selected == ["2"]
    assert "unknown option" in out.getvalue()


def test_ask_conflict_blocks_done_then_resolves():
    out = StringIO()
    res = ask("Title", "", SAMPLE,
              input_lines=["1", "2", "done", "2", "done"], out=out)
    assert res.selected == ["1"]
    assert "CONFLICT" in out.getvalue()


def test_ask_custom_token():
    out = StringIO()
    res = ask("Title", "", SAMPLE, input_lines=["custom: my value", "done"], out=out)
    assert res.selected == ["o"]
    assert res.custom == "my value"


def test_ask_cancel_aborts():
    res = ask("Title", "", SAMPLE, input_lines=["cancel"])
    assert res.cancelled is True
    assert res.selected == []


def test_ask_stop_iteration_cancels():
    res = ask("Title", "", SAMPLE, input_lines=["1"])
    assert res.cancelled is True


def test_ask_single_select_clears_others():
    out = StringIO()
    res = ask("Title", "", SAMPLE, input_lines=["1", "2", "done"], out=out, multi=False)
    assert res.selected == ["2"]


def test_spec_to_choices_and_load_spec(tmp_path: Path):
    spec = {
        "title": "Pick",
        "body": "Choose:",
        "multi": True,
        "choices": [
            {"id": "1", "text": "Opus", "conflicts": ["2"]},
            {"id": "2", "text": "Haiku"},
            {"id": "o", "text": "Other", "custom": True},
        ],
    }
    p = tmp_path / "spec.json"
    p.write_text(json.dumps(spec), encoding="utf-8")
    loaded = load_spec(str(p))
    assert loaded["title"] == "Pick"
    choices = spec_to_choices(loaded)
    assert choices[0] == Choice("1", "Opus", conflicts=("2",), custom=False)
    assert choices[2].custom is True


def _cli(argv, root):
    return subprocess.run([sys.executable, "-m", "guardrail.cli", *argv],
                          cwd=root, capture_output=True, text=True, encoding="utf-8")


def test_cli_choose_noninteractive_valid(tmp_path: Path):
    spec = {"title": "M", "choices": [
        {"id": "1", "text": "Opus", "conflicts": ["2"]}, {"id": "2", "text": "Haiku"}]}
    p = tmp_path / "spec.json"
    p.write_text(json.dumps(spec), encoding="utf-8")
    r = _cli(["choose", "--file", str(p), "--select", "1"], tmp_path)
    assert r.returncode == 0, r.stderr
    data = json.loads(r.stdout.strip().splitlines()[-1])
    assert data["selected"] == ["1"]
    assert data["cancelled"] is False


def test_cli_choose_noninteractive_conflict(tmp_path: Path):
    spec = {"title": "M", "choices": [
        {"id": "1", "text": "Opus", "conflicts": ["2"]}, {"id": "2", "text": "Haiku"}]}
    p = tmp_path / "spec.json"
    p.write_text(json.dumps(spec), encoding="utf-8")
    r = _cli(["choose", "--file", str(p), "--select", "1", "--select", "2"], tmp_path)
    assert r.returncode == 1, r.stderr
    data = json.loads(r.stdout.strip().splitlines()[-1])
    assert data["cancelled"] is True


def test_cli_choose_unknown_token(tmp_path: Path):
    spec = {"title": "M", "choices": [{"id": "1", "text": "Opus"}]}
    p = tmp_path / "spec.json"
    p.write_text(json.dumps(spec), encoding="utf-8")
    r = _cli(["choose", "--file", str(p), "--select", "bogus"], tmp_path)
    assert r.returncode == 2
    assert "unknown option" in r.stderr


def test_cli_choose_with_custom(tmp_path: Path):
    spec = {"title": "M", "choices": [{"id": "o", "text": "Other", "custom": True}]}
    p = tmp_path / "spec.json"
    p.write_text(json.dumps(spec), encoding="utf-8")
    r = _cli(["choose", "--file", str(p), "--select", "o", "--custom", "my text"], tmp_path)
    assert r.returncode == 0, r.stderr
    data = json.loads(r.stdout.strip().splitlines()[-1])
    assert data["selected"] == ["o"]
    assert data["custom"] == "my text"
