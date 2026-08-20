"""Tests for consensus_review.py -- the multi-AI tribunal tool.

Mocks the network/subprocess boundary (real API calls belong in manual
verification, not the test suite -- they cost real money and depend on
live rate-limit conditions, per the 2026-08-20 manual test run). What's
tested here is the tool's own logic: gated dispatch, honest degraded-
consensus reporting, and that a reviewer failure is never silently
counted as success (Law 23, lawkeeper's AI_CONSTITUTION.md).
"""
import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from conftest import REPO_ROOT, load_script

consensus_review = load_script("consensus_review.py")


@pytest.fixture
def spec_file(tmp_path):
    spec = {
        "id": "test",
        "title": "Test case",
        "context": "A test case.",
        "findings": [{"id": "F1", "title": "Test finding", "claim": "The sky is blue.", "evidence": "Observation."}],
    }
    p = tmp_path / "test.json"
    p.write_text(json.dumps(spec), encoding="utf-8")
    return p


class TestDraftGate:
    def test_draft_stages_without_sending(self, spec_file, tmp_path, monkeypatch):
        monkeypatch.setattr(consensus_review, "CONSENSUS_DIR", tmp_path / "consensus")
        with patch.object(consensus_review, "ask_reviewer") as mock_ask:
            consensus_review.draft(spec_file, 1)
            mock_ask.assert_not_called()

    def test_draft_not_overwritten_on_second_call(self, spec_file, tmp_path, monkeypatch, capsys):
        monkeypatch.setattr(consensus_review, "CONSENSUS_DIR", tmp_path / "consensus")
        consensus_review.draft(spec_file, 1)
        case_dir = consensus_review._case_dir(spec_file)
        original = consensus_review.draft_path(case_dir, 1).read_text(encoding="utf-8")
        consensus_review.draft(spec_file, 1)
        out = capsys.readouterr().out
        assert "already staged" in out
        assert consensus_review.draft_path(case_dir, 1).read_text(encoding="utf-8") == original


class TestRunGate:
    def test_run_without_approved_does_not_dispatch(self, spec_file, tmp_path, monkeypatch):
        monkeypatch.setattr(consensus_review, "CONSENSUS_DIR", tmp_path / "consensus")
        consensus_review.draft(spec_file, 1)
        with patch.object(consensus_review, "ask_reviewer") as mock_ask:
            consensus_review.run(spec_file, 1, approved=False)
            mock_ask.assert_not_called()

    def test_run_without_draft_raises(self, spec_file, tmp_path, monkeypatch):
        monkeypatch.setattr(consensus_review, "CONSENSUS_DIR", tmp_path / "consensus")
        with pytest.raises(SystemExit):
            consensus_review.run(spec_file, 1, approved=True)


class TestDegradedConsensus:
    """The core Law 23 property: a failed reviewer must never be silently
    treated as agreement or dropped -- the ledger must record exactly how
    many of the expected reviewers actually responded."""

    def test_partial_failure_recorded_honestly(self, spec_file, tmp_path, monkeypatch):
        monkeypatch.setattr(consensus_review, "CONSENSUS_DIR", tmp_path / "consensus")
        monkeypatch.setattr(consensus_review, "REVIEWERS", {"a": "model/a", "b": "model/b"})
        consensus_review.draft(spec_file, 1)

        def fake_ask(name, brief, panel="general"):
            if name == "a":
                return "F1: AGREE | fine", None
            return None, "simulated failure"

        with patch.object(consensus_review, "ask_reviewer", side_effect=fake_ask):
            consensus_review.run(spec_file, 1, approved=True)

        case_dir = consensus_review._case_dir(spec_file)
        ledger = json.loads((case_dir / "_ledger.json").read_text(encoding="utf-8"))
        entry = ledger[-1]
        assert entry["responded"] == 1
        assert entry["total"] == 2
        assert entry["results"]["a"]["status"] == "ok"
        assert entry["results"]["b"]["status"] == "error"
        assert entry["results"]["b"]["error"] == "simulated failure"

    def test_full_success_recorded_as_full(self, spec_file, tmp_path, monkeypatch):
        monkeypatch.setattr(consensus_review, "CONSENSUS_DIR", tmp_path / "consensus")
        monkeypatch.setattr(consensus_review, "REVIEWERS", {"a": "model/a"})
        consensus_review.draft(spec_file, 1)
        with patch.object(consensus_review, "ask_reviewer", return_value=("F1: AGREE | fine", None)):
            consensus_review.run(spec_file, 1, approved=True)
        case_dir = consensus_review._case_dir(spec_file)
        ledger = json.loads((case_dir / "_ledger.json").read_text(encoding="utf-8"))
        assert ledger[-1]["responded"] == ledger[-1]["total"] == 1


class TestSciencePanel:
    """The peer-review benchmark the user set: a 'science' panel with a
    real, grounded checklist, selectable per-round, not hardcoded to the
    generic reviewer prompt."""

    def test_science_panel_registered(self):
        assert "science" in consensus_review.PANELS
        assert "science" in [c for c in consensus_review.PANELS]

    def test_science_prompt_contains_real_checklist_items(self):
        prompt = consensus_review.PANELS["science"]
        for term in ("p-hacking", "Reproducibility", "Reasonable interpretation",
                     "Methodological soundness", "Source quality"):
            assert term in prompt, f"expected '{term}' in the science panel prompt"

    def test_run_passes_selected_panel_to_reviewer(self, spec_file, tmp_path, monkeypatch):
        monkeypatch.setattr(consensus_review, "CONSENSUS_DIR", tmp_path / "consensus")
        monkeypatch.setattr(consensus_review, "REVIEWERS", {"a": "model/a"})
        consensus_review.draft(spec_file, 1)
        seen_panels = []

        def fake_ask(name, brief, panel="general"):
            seen_panels.append(panel)
            return "1: PASS | fine\nOVERALL: PASSES REVIEW | fine", None

        with patch.object(consensus_review, "ask_reviewer", side_effect=fake_ask):
            consensus_review.run(spec_file, 1, approved=True, panel="science")
        assert seen_panels == ["science"]

    def test_unknown_panel_rejected(self, spec_file, tmp_path, monkeypatch):
        monkeypatch.setattr(consensus_review, "CONSENSUS_DIR", tmp_path / "consensus")
        consensus_review.draft(spec_file, 1)
        with pytest.raises(SystemExit):
            consensus_review.run(spec_file, 1, approved=True, panel="not-a-real-panel")


class TestAskClaudeAuthDetection:
    """Regression: a nested `claude -p` subprocess returning 'Not logged
    in' as stdout must be treated as a failure, not a real reply -- found
    by actually running this against a live subprocess, 2026-08-20."""

    def test_not_logged_in_raises(self):
        class FakeProc:
            stdout = "Not logged in · Please run /login"
            stderr = ""
        with patch.object(consensus_review.shutil, "which", return_value="/fake/claude"), \
             patch.object(consensus_review.subprocess, "run", return_value=FakeProc()):
            with pytest.raises(RuntimeError, match="not authenticated"):
                consensus_review.ask_claude("test brief")

    def test_real_reply_passes_through(self):
        class FakeProc:
            stdout = "F1: AGREE | genuine reasoning here"
            stderr = ""
        with patch.object(consensus_review.shutil, "which", return_value="/fake/claude"), \
             patch.object(consensus_review.subprocess, "run", return_value=FakeProc()):
            result = consensus_review.ask_claude("test brief")
            assert "AGREE" in result
