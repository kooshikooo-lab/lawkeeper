"""Tests for `lawkeeper update` and the provenance `init` now records
(docs/DESIGN_NOTE_mutmut_and_pinned_distribution_2026-10-10.md, steps 1-2).

Uses a small fake template tree (monkeypatched over _template_root /
_extras_template_root) so each case controls exactly what "upstream"
changed; init's own required-file check forces the five names below.
"""
import json
import subprocess

import pytest

from guardrail import cli, template_sync

_FILES = {
    "docs/AI_CONSTITUTION.md": "# __PROJECT_NAME__ constitution v1\n",
    "scripts/install_hooks.py": "print('hooks v1')\n",
    "scripts/gate_pretooluse.py": "GATE = 1\n",
    ".claude/settings.json": "{}\n",
    "AGENTS.md.tmpl": "agents for __PROJECT_NAME__\n",
}


def _write_tree(root, files):
    for rel, text in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8", newline="\n")


@pytest.fixture
def repo(tmp_path, monkeypatch):
    tpl = tmp_path / "tpl"
    _write_tree(tpl, _FILES)
    monkeypatch.setattr(cli, "_template_root", lambda: tpl)
    monkeypatch.setattr(cli, "_extras_template_root", lambda: tmp_path / "no-extras")
    r = tmp_path / "proj"
    r.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=r, check=True)
    monkeypatch.chdir(r)
    assert cli.main(["init", ".", "--name", "proj"]) == 0
    return r, tpl


def _cfg(r):
    return json.loads((r / ".guardrail.json").read_text(encoding="utf-8"))


def _bump(tpl, rel, text):
    (tpl / rel).write_text(text, encoding="utf-8", newline="\n")


def test_init_records_version_and_hashes_of_what_it_wrote(repo):
    r, _ = repo
    cfg = _cfg(r)
    assert cfg["template_version"] == cli.__version__
    assert set(cfg["template_files"]) >= {"docs/AI_CONSTITUTION.md", "AGENTS.md"}
    for rel, digest in cfg["template_files"].items():
        if rel == ".guardrail.json":
            continue
        assert template_sync.sha256((r / rel).read_bytes()) == digest


def test_update_when_nothing_changed(repo, capsys):
    assert cli.main(["update"]) == 0
    assert "up to date" in capsys.readouterr().out


def test_upstream_change_is_dry_run_until_apply(repo, capsys):
    r, tpl = repo
    _bump(tpl, "scripts/gate_pretooluse.py", "GATE = 2\n")
    assert cli.main(["update"]) == 0
    assert "update available: scripts/gate_pretooluse.py" in capsys.readouterr().out
    assert (r / "scripts/gate_pretooluse.py").read_text() == "GATE = 1\n"

    assert cli.main(["update", "--apply"]) == 0
    assert (r / "scripts/gate_pretooluse.py").read_text() == "GATE = 2\n"
    assert _cfg(r)["template_files"]["scripts/gate_pretooluse.py"] == template_sync.sha256(b"GATE = 2\n")
    capsys.readouterr()
    assert cli.main(["update"]) == 0
    assert "up to date" in capsys.readouterr().out


def test_local_customisation_with_unchanged_upstream_is_kept(repo, capsys):
    r, _ = repo
    (r / "AGENTS.md").write_text("my own rules\n", encoding="utf-8", newline="\n")
    assert cli.main(["update", "--apply"]) == 0
    assert "kept (local customisation): AGENTS.md" in capsys.readouterr().out
    assert (r / "AGENTS.md").read_text() == "my own rules\n"


def test_conflict_is_shown_and_never_overwritten_even_with_apply(repo, capsys):
    r, tpl = repo
    (r / "AGENTS.md").write_text("my own rules\n", encoding="utf-8", newline="\n")
    _bump(tpl, "AGENTS.md.tmpl", "new upstream rules for __PROJECT_NAME__\n")
    assert cli.main(["update", "--apply"]) == 1
    out = capsys.readouterr().out
    assert "CONFLICT: AGENTS.md" in out
    assert "-my own rules" in out and "+new upstream rules for proj" in out
    assert (r / "AGENTS.md").read_text() == "my own rules\n"


def test_missing_file_is_reported_not_recreated(repo, capsys):
    r, tpl = repo
    (r / "scripts/gate_pretooluse.py").unlink()
    _bump(tpl, "scripts/gate_pretooluse.py", "GATE = 2\n")
    assert cli.main(["update", "--apply"]) == 0
    assert "missing locally: scripts/gate_pretooluse.py" in capsys.readouterr().out
    assert not (r / "scripts/gate_pretooluse.py").exists()


def test_new_upstream_file_added_only_on_apply(repo, tmp_path):
    r, tpl = repo
    _write_tree(tpl, {"docs/NEW.md": "new\n"})
    assert cli.main(["update"]) == 0
    assert not (r / "docs/NEW.md").exists()
    assert cli.main(["update", "--apply"]) == 0
    assert (r / "docs/NEW.md").read_text() == "new\n"


def test_crlf_checkout_is_not_mistaken_for_customisation(repo, capsys):
    r, tpl = repo
    p = r / "scripts/gate_pretooluse.py"
    p.write_bytes(p.read_bytes().replace(b"\n", b"\r\n"))
    _bump(tpl, "scripts/gate_pretooluse.py", "GATE = 2\n")
    assert cli.main(["update", "--apply"]) == 0
    assert "CONFLICT" not in capsys.readouterr().out
    assert p.read_text() == "GATE = 2\n"


def test_repo_without_provenance_is_reported_and_untouched(repo, capsys):
    r, tpl = repo
    cfg = _cfg(r)
    del cfg["template_files"], cfg["template_version"]
    (r / ".guardrail.json").write_text(json.dumps(cfg), encoding="utf-8")
    before = (r / "AGENTS.md").read_bytes()
    _bump(tpl, "AGENTS.md.tmpl", "changed\n")
    assert cli.main(["update", "--apply"]) == 1
    assert "no provenance" in capsys.readouterr().out
    assert (r / "AGENTS.md").read_bytes() == before
