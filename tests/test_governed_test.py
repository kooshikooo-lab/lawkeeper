"""Tests for scripts/governed_test.py's run_mutation() (T4 discrimination
check) -- zero test coverage existed for this file before this pass.

Real bug found 2026-09-06 (relayed cross-repo: a Windwright session's own
mutation-testing pass independently hit the identical shape -- a "98.4%
kill rate" that turned out to be a broken baseline test failing on
unmutated code too, so every "kill" was that same pre-existing failure,
not real discrimination): run_mutation() ran pytest against the MUTATED
code and reported "discriminates: True" whenever that run failed, without
ever checking the test passes on the REAL, unmutated code first. Fixed by
adding a baseline pytest run before the mutation is applied.

Uses real files and a real pytest subprocess (governed_test.ROOT
monkeypatched to an isolated tmp_path) rather than mocking subprocess --
this tool's whole value is that it actually runs pytest against actually-
mutated source, and a mocked-subprocess test wouldn't prove that works.
"""

from __future__ import annotations

from conftest import load_script

governed_test = load_script("governed_test.py")


def _write_target(root, value: int = 10):
    target = root / "target.py"
    target.write_text(f"THRESHOLD = {value}\n", encoding="utf-8")
    return target


def _write_test(root, *, real_oracle: bool, always_fails: bool = False):
    """A real test file, importable by the real pytest subprocess
    run_mutation() launches. `import target` resolves because that
    subprocess runs with cwd=root (run_mutation's own subprocess.run
    call) -- pytest's default rootdir-relative import adds root itself to
    sys.path, no explicit sys.path insertion needed or present here."""
    if always_fails:
        body = (
            "import target\n"
            "def test_threshold():\n"
            "    assert target.THRESHOLD == 999  # wrong on purpose: fails always\n"
        )
    elif real_oracle:
        body = (
            "import target\n"
            "def test_threshold():\n"
            "    assert target.THRESHOLD == 10  # real oracle: discriminates\n"
        )
    else:
        body = (
            "import target\n"
            "def test_threshold():\n"
            "    assert target.THRESHOLD > 0  # weak oracle: survives most mutations\n"
        )
    test_file = root / "test_target.py"
    test_file.write_text(body, encoding="utf-8")
    return test_file


_CARD = {
    "test_id": "test_target",
    "mutation": {"file": "target.py", "attr": "THRESHOLD", "new_value": 20},
}


class TestRunMutationVerifiesBaselineFirst:
    def test_broken_baseline_refuses_the_mutation_check(self, tmp_path, monkeypatch, capsys):
        """The real bug: a test that already fails on unmutated code must
        not be scored as "discriminates" just because it also fails after
        mutation -- that's the same failure, not evidence of anything."""
        monkeypatch.setattr(governed_test, "ROOT", tmp_path)
        monkeypatch.chdir(tmp_path)
        _write_target(tmp_path)
        _write_test(tmp_path, real_oracle=False, always_fails=True)

        code = governed_test.run_mutation("test_target.py", _CARD, as_json=False)

        assert code == 1
        err = capsys.readouterr().err
        assert "does not pass on the REAL (unmutated) code" in err

    def test_baseline_refusal_leaves_the_target_file_untouched(self, tmp_path, monkeypatch):
        """Real regression guard: the refusal path returns before ever
        writing the mutated content, so the source file on disk must be
        byte-identical to what was written, not just "eventually restored"."""
        monkeypatch.setattr(governed_test, "ROOT", tmp_path)
        monkeypatch.chdir(tmp_path)
        target = _write_target(tmp_path)
        _write_test(tmp_path, real_oracle=False, always_fails=True)
        original = target.read_text(encoding="utf-8")

        governed_test.run_mutation("test_target.py", _CARD, as_json=False)

        assert target.read_text(encoding="utf-8") == original

    def test_real_oracle_discriminates_after_a_passing_baseline(self, tmp_path, monkeypatch):
        """Regression coverage for the existing correct path (had zero
        test coverage before this pass, not just the new baseline check):
        a real, working test with a genuine oracle passes the baseline
        and then genuinely fails under mutation -- T4 earned."""
        monkeypatch.setattr(governed_test, "ROOT", tmp_path)
        monkeypatch.chdir(tmp_path)
        _write_target(tmp_path)
        _write_test(tmp_path, real_oracle=True)

        code = governed_test.run_mutation("test_target.py", _CARD, as_json=False)

        assert code == 0

    def test_weak_oracle_passes_baseline_but_does_not_discriminate(self, tmp_path, monkeypatch, capsys):
        """A test with a real, passing baseline but a weak oracle (still
        passes after mutation) must be reported as NOT discriminating --
        the original bug this whole file guards against, just from the
        other side: a passing baseline is necessary but not sufficient."""
        monkeypatch.setattr(governed_test, "ROOT", tmp_path)
        monkeypatch.chdir(tmp_path)
        _write_target(tmp_path)
        _write_test(tmp_path, real_oracle=False)

        code = governed_test.run_mutation("test_target.py", _CARD, as_json=False)

        assert code == 1
        err = capsys.readouterr().err
        assert "does not discriminate" in err
