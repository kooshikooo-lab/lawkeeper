"""Tests for scripts/noticeboard.py (shared agent noticeboard, 2026-09-26).

Theory card (Law 19)
  claim: a posted entry is parsed back with its fields; `check` shows each entry
    to a session exactly once; machine-board entries reach only the repos they
    name (or "all"); a session seen for the first time sees at most the last
    FIRST_SIGHT_SHOW entries; the Claude-hook output is the JSON shape Claude Code
    documents (hookSpecificOutput.hookEventName + additionalContext).
  independent oracle: hand-written board text with known ids and fields (not
    produced by the code under test) and the hook JSON shape from the Claude Code
    settings schema (update-config skill, read 2026-09-26).
  acceptance threshold: exact equality of ids, fields and counts.
  blind spot: concurrent appends from two processes at the same instant are not
    exercised; the real Claude Code hook invocation is not run here (checked by
    hand once, see docs/inter-agent/README.md); month roll-over reads all month
    files, so very old boards are re-parsed (cost, not correctness).
  trust level: T2 (independent oracle), not yet adversarially reviewed.
"""
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("noticeboard", ROOT / "scripts" / "noticeboard.py")
nb = importlib.util.module_from_spec(spec)
spec.loader.exec_module(nb)

BOARD = """# Noticeboard 2026-09

### NB-20260926T090000Z-aaaa · 2026-09-26T09:00:00Z
- from: session-A
- to: all
- repos: windwright
- action: none
- files: -
first note

### NB-20260926T091500Z-bbbb · 2026-09-26T09:15:00Z
- from: session-B
- to: session-A
- repos: windwright
- action: needed: read the plan
- files: docs/x.md
second note
line two
"""

MACHINE = """### NB-20260926T092000Z-cccc · 2026-09-26T09:20:00Z
- from: falcun-session
- to: all
- repos: falcun
- action: none
- files: -
only for falcun

### NB-20260926T093000Z-dddd · 2026-09-26T09:30:00Z
- from: falcun-session
- to: all
- repos: falcun, windwright
- action: none
- files: -
for both
"""


def _boards(tmp_path):
    repo, machine = tmp_path / "repo", tmp_path / "machine"
    repo.mkdir()
    machine.mkdir()
    (repo / "NOTICEBOARD_2026-09.md").write_text(BOARD, encoding="utf-8")
    (machine / "NOTICEBOARD_2026-09.md").write_text(MACHINE, encoding="utf-8")
    return repo, machine


def test_parse_fields_and_body():
    es = nb.parse_entries(BOARD, "repo")
    assert [e["id"] for e in es] == ["NB-20260926T090000Z-aaaa", "NB-20260926T091500Z-bbbb"]
    assert es[1]["to"] == "session-A"
    assert es[1]["action"] == "needed: read the plan"
    assert es[1]["files"] == "docs/x.md"
    assert es[1]["body"] == "second note\nline two"


def test_machine_board_filtered_by_repo(tmp_path):
    repo, machine = _boards(tmp_path)
    ids = [e["id"] for e in nb.load_entries(repo, machine, "windwright")]
    assert "NB-20260926T092000Z-cccc" not in ids          # falcun only
    assert "NB-20260926T093000Z-dddd" in ids              # names windwright
    assert len(ids) == 3


def test_each_entry_shown_once_then_new_only(tmp_path):
    repo, machine = _boards(tmp_path)
    cur = tmp_path / "cursors"
    entries = nb.load_entries(repo, machine, "windwright")
    shown, hidden = nb.unseen_for("s1", entries, cur)
    assert len(shown) == 3 and hidden == 0                 # first sight, <= FIRST_SIGHT_SHOW
    assert nb.unseen_for("s1", entries, cur) == ([], 0)    # nothing new
    eid, text = nb.new_entry_text("s2", "all", "windwright", "none", "", "third note")
    nb.append_entry(repo, text)
    shown, _ = nb.unseen_for("s1", nb.load_entries(repo, machine, "windwright"), cur)
    assert [e["id"] for e in shown] == [eid]
    assert shown[0]["body"] == "third note"


def test_first_sight_is_capped(tmp_path):
    entries = [{"id": f"NB-20260926T0900{i:02d}Z-000{i % 10}", "time": "t", "source": "repo"}
               for i in range(12)]
    shown, hidden = nb.unseen_for("fresh", entries, tmp_path / "c")
    assert len(shown) == nb.FIRST_SIGHT_SHOW and hidden == 0


def test_hook_output_shape(tmp_path, monkeypatch, capsys):
    repo, machine = _boards(tmp_path)
    monkeypatch.setattr(nb, "REPO_BOARD_DIR", repo)
    monkeypatch.setattr(nb, "CURSOR_DIR", tmp_path / "cursors")
    monkeypatch.setenv("AGENT_NOTICEBOARD_HOME", str(machine))
    monkeypatch.setattr(nb, "REPO_NAME", "windwright")
    assert nb.main(["check", "--session", "h1", "--format", "claude-hook", "--event", "PostToolUse"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["hookSpecificOutput"]["hookEventName"] == "PostToolUse"
    assert "NB-20260926T091500Z-bbbb" in out["hookSpecificOutput"]["additionalContext"]
    assert nb.main(["check", "--session", "h1", "--format", "claude-hook"]) == 0
    assert capsys.readouterr().out == ""                   # silent when nothing is new


def test_repo_name_from_remote_not_worktree_folder(tmp_path, monkeypatch):
    """Oracle: a hand-made git repo whose folder name differs from its remote's name."""
    import subprocess
    wt = tmp_path / "myrepo-wt-feature"
    wt.mkdir()
    subprocess.run(["git", "init", "-q", str(wt)], check=True)
    subprocess.run(["git", "-C", str(wt), "remote", "add", "origin",
                    "https://github.com/someone/MyRepo.git"], check=True)
    monkeypatch.delenv("NOTICEBOARD_REPO", raising=False)
    assert nb.repo_name_for(wt) == "myrepo"
    monkeypatch.setenv("NOTICEBOARD_REPO", "Other")
    assert nb.repo_name_for(wt) == "other"
    monkeypatch.delenv("NOTICEBOARD_REPO")
    plain = tmp_path / "Plain"
    plain.mkdir()
    assert nb.repo_name_for(plain) == "plain"            # no remote: folder name
