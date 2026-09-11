"""Characterization tests for gate_pretooluse.py's scope boundary.

These are NOT tests of desired behavior -- they pin the gate's ACTUAL
reach so the claim in the hook's own docstring (the "SCOPE BOUNDARY"
section) is falsifiable rather than folklore. If gate_pretooluse.py is
ever extended to inspect script contents, the BOUNDARY tests below go
red and force the docstring to change in the same commit.

Methodology ported deliberately (not just the idea) from
DimitriGeelen/agentic-engineering-framework's tier0_scope_boundary.bats
(Apache-2.0; see docs/RESEARCH_agent_harness_landscape.md), which this
repo's own research found and the user asked to be ported: every
BOUNDARY assertion ("this is NOT flagged") is paired with a CONTROL
assertion proving the harness can observe a flag at all. Without the
control, an "allowed" result is indistinguishable between "the gate
deliberately does not cover this" and "the test harness is broken and
cannot detect anything" -- the exact failure AEF's own fixture design
notes they had to catch (a quoted-variable fixture that accidentally
passed regardless of whether the boundary was real).

Also includes idempotency characterization: AEF's real T-1506 incident
(a stateful, single-use approval FILE consumed via `rm -f` then
re-checked, self-defeating under duplicate hook registration) does not
apply here -- gate_pretooluse.py has no persistent state and performs
no file-write side effects at all. That is asserted structurally below,
not just claimed in a comment, so it stays true rather than becoming
folklore itself.
"""
from pathlib import Path

from conftest import REPO_ROOT, load_script

gate = load_script("gate_pretooluse.py")


# ── Positive controls: prove the harness CAN observe a hardline verdict ─

class TestControlsHarnessCanObserveAFlag:
    """Without these, every BOUNDARY "not flagged" result below would be
    unfalsifiable -- it could mean the boundary is real, or it could
    mean inspect_command() itself is broken and flags nothing at all."""

    def test_control_the_same_danger_typed_inline_is_flagged(self):
        risk = gate.inspect_command("git push --force origin main")
        assert risk is not None
        assert risk.level == "hardline"

    def test_control_danger_is_flagged_even_with_a_script_path_also_present(self):
        # Proves it's the STRING that matters, not merely the presence
        # of something that looks like a file path in the command.
        risk = gate.inspect_command("git push --force origin main && cat deploy.sh")
        assert risk is not None
        assert risk.level == "hardline"


# ── The boundary itself: a script's CONTENTS are invisible to this hook ─

class TestBoundaryScriptContentsAreOpaque:
    """Each test writes a real script file whose CONTENTS are
    unambiguously hardline-dangerous, then invokes it BY NAME (never by
    inlining the dangerous command itself) -- the hook must not see
    inside it, matching the documented SCOPE BOUNDARY."""

    def _make_destructive_script(self, tmp_path: Path, name: str = "deploy.sh") -> Path:
        script = tmp_path / name
        script.write_text("#!/bin/bash\ngit push --force origin main\n", encoding="utf-8")
        return script

    def test_boundary_invoking_via_bash_is_not_flagged(self, tmp_path):
        script = self._make_destructive_script(tmp_path)
        assert "push --force" in script.read_text(encoding="utf-8")  # premise: really is dangerous
        assert gate.inspect_command(f"bash {script}") is None

    def test_boundary_invoking_directly_is_not_flagged(self, tmp_path):
        script = self._make_destructive_script(tmp_path)
        assert "push --force" in script.read_text(encoding="utf-8")
        assert gate.inspect_command(str(script)) is None

    def test_boundary_other_interpreters_are_equally_opaque(self, tmp_path):
        script = tmp_path / "deploy.py"
        script.write_text(
            'import subprocess; subprocess.run(["git", "push", "--force", "origin", "main"])\n',
            encoding="utf-8",
        )
        assert gate.inspect_command(f"python3 {script}") is None

    def test_boundary_a_shell_function_wrapping_the_real_command_is_opaque(self):
        # The Bash tool call the hook sees is the function's name, not
        # what it expands to -- there is no function-body resolution.
        assert gate.inspect_command("deploy_prod") is None


# ── Doc-sync: the documented claim must not silently drift from reality ─

class TestDocumentationStatesTheBoundary:
    """If the SCOPE BOUNDARY text is ever deleted from the docstring
    while the actual behavior stays limited, these tests catch that --
    the BOUNDARY tests above would still pass, silently, with no
    written claim left for a reader to check them against."""

    def _hook_source(self) -> str:
        return (REPO_ROOT / "scripts" / "gate_pretooluse.py").read_text(encoding="utf-8")

    def test_docstring_names_the_scope_boundary_explicitly(self):
        source = self._hook_source()
        assert "SCOPE BOUNDARY" in source
        assert "never opens, reads, or inspects the contents" in source

    def test_theory_card_documents_the_same_boundary(self):
        card = (REPO_ROOT / "test_governance" / "cards" / "test_gate_pretooluse.yaml").read_text(
            encoding="utf-8"
        )
        assert "indirection through a wrapper script" in card


# ── Idempotency: the AEF T-1506 bug class structurally cannot occur ─────

class TestNoStatefulSideEffects:
    """AEF's real T-1506 incident: a single-use approval FILE, consumed
    via rm -f then re-checked, self-defeats under duplicate hook
    registration (the same hook registered in both project and
    user-level settings.json fires twice per call; the first
    invocation consumes the approval, the second finds it gone and
    blocks). That bug class requires persistent, mutating, single-use
    state. gate_pretooluse.py has none -- asserted structurally here,
    not just claimed in a comment, so a future change that DOES add
    file-mutating state (e.g. porting AEF's own single-use command-hash
    approval flow) is forced to also add real duplicate-firing coverage
    at the same time, rather than silently inheriting this test's
    now-stale "no state" guarantee."""

    def test_module_performs_no_write_mode_file_io(self):
        source = (REPO_ROOT / "scripts" / "gate_pretooluse.py").read_text(encoding="utf-8")
        write_indicators = ["write_text(", "write_bytes(", "\"w\")", "'w')", ".unlink(", "os.remove("]
        found = [w for w in write_indicators if w in source]
        assert not found, (
            f"gate_pretooluse.py now contains file-mutation code ({found}) -- the "
            "no-persistent-state premise this test class documents no longer holds. "
            "If this is a deliberate addition (e.g. AEF-style single-use approval), "
            "add real duplicate-hook-firing test coverage alongside it, don't just "
            "delete this assertion."
        )

    def test_repeated_identical_invocations_produce_identical_verdicts(self):
        # Simulates duplicate hook registration firing twice for the
        # same call: since there is no state, both firings must agree.
        command = "git push --force origin main"
        first = gate.inspect_command(command)
        second = gate.inspect_command(command)
        assert (first is None) == (second is None)
        if first is not None:
            assert first.level == second.level
            assert first.branch == second.branch

    def test_repeated_ask_tier_invocations_also_agree(self):
        command = "git push --force origin $BRANCH"
        first = gate.inspect_command(command)
        second = gate.inspect_command(command)
        assert first is not None and second is not None
        assert first.level == second.level == "ask"
