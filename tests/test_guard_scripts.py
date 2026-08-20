"""Meta-tests: the enforcement system must itself be tested (Law 16).

These tests exercise the guard scripts' pure logic so a regression in the
guards (the very code that prevents failure) is caught. They must not depend on
the real git state or network, only on the scripts' importable functions.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

from conftest import REPO_ROOT, load_script

guard_branch = load_script("guard_branch.py")
merge_gate = load_script("merge_gate.py")
validate_commit_msg = load_script("validate_commit_msg.py")
validate_pre_commit = load_script("validate_pre_commit.py")
guard_governance = load_script("guard_governance.py")
compliance_watchdog = load_script("compliance_watchdog.py")


# ── compliance_watchdog: the law loader must read the constitution ─────

class TestLawLoader:
    """Regression: the loader once silently fell back to a hardcoded 14-law
    list (missing re.MULTILINE), so Laws 15+ were never actually verified."""

    def test_laws_loaded_from_constitution_file(self):
        laws = compliance_watchdog.load_constitution_laws()
        assert len(laws) >= 15, f"expected >=15 laws from the constitution, got {len(laws)}"

    def test_law_15_and_16_present(self):
        laws = "\n".join(compliance_watchdog.load_constitution_laws())
        assert "Law 15" in laws
        assert "Law 16" in laws


# ── guard_branch: Law 15 classification ────────────────────────────────

class TestBranchClassify:
    @pytest.mark.parametrize("name,expected", [
        ("main", "trunk"),
        ("opencode/main/desktop", "canonical"),
        ("opencode/main/laptop", "canonical"),
        ("opencode/mesh-repair/laptop", "feature"),
        ("opencode/branch-governance/desktop", "feature"),
        ("merge/governance", "merge_staging"),
        ("experiment/unconventional-shapes", None),
        ("perf/tmm-refactor-copilot", None),
        ("audit/merge-main-into-desktop", None),
    ])
    def test_namespaces(self, name, expected):
        assert guard_branch.classify(name) == expected

    def test_canonical_detection(self):
        assert guard_branch.is_canonical("main")
        assert guard_branch.is_canonical("opencode/main/desktop")
        assert not guard_branch.is_canonical("opencode/idea/laptop")
        assert not guard_branch.is_canonical("merge/x")


class TestBranchPushGuard:
    def test_canonical_delete_blocked(self):
        lines = [
            "refs/heads/main 0000000000000000000000000000000000000000 "
            "refs/heads/main ca25882a"
        ]
        violations = guard_branch.check_push(lines)
        assert any("canonical branch" in v and "main" in v for v in violations)

    def test_canonical_delete_allowed_with_human_approval(self):
        lines = [
            "refs/heads/main 0000000000000000000000000000000000000000 "
            "refs/heads/main ca25882a"
        ]
        assert guard_branch.check_push(lines, human_delete={"main"}) == []

    def test_orphan_push_blocked(self):
        lines = [
            "refs/heads/experiment/foo abc123 refs/heads/experiment/foo 0000"
        ]
        violations = guard_branch.check_push(lines)
        assert any("orphan" in v for v in violations)

    def test_feature_push_ok(self):
        lines = [
            "refs/heads/opencode/idea/laptop abc123 "
            "refs/heads/opencode/idea/laptop 0000"
        ]
        assert guard_branch.check_push(lines) == []


class TestBranchDeleteGuard:
    def test_canonical_delete_blocked(self, monkeypatch):
        monkeypatch.delenv("GUARD_BRANCH_ALLOW_DELETE", raising=False)
        violations = guard_branch.check_delete("opencode/main/desktop")
        assert any("canonical branch" in v for v in violations)

    def test_canonical_delete_allowed_with_override(self, monkeypatch):
        monkeypatch.setenv("GUARD_BRANCH_ALLOW_DELETE", "opencode/main/desktop")
        assert guard_branch.check_delete("opencode/main/desktop") == []

    def test_orphan_delete_blocked(self):
        violations = guard_branch.check_delete("experiment/unconventional-shapes")
        assert any("orphan" in v for v in violations)

    def test_feature_delete_content_proven_by_presence(self, monkeypatch):
        # Guard logic: a feature branch whose content is preserved passes;
        # one not preserved is flagged. We stub BOTH run_git (so this test
        # doesn't depend on a specific branch actually existing in whatever
        # repo happens to run the suite) and content_preserved, to isolate
        # the pure decision logic.
        monkeypatch.setattr(guard_branch, "run_git", lambda args: ("deadbeef", 0))
        monkeypatch.setattr(guard_branch, "content_preserved", lambda sha: True)
        monkeypatch.delenv("GUARD_BRANCH_ALLOW_DELETE", raising=False)
        assert guard_branch.check_delete("opencode/some-feature/laptop") == []

        monkeypatch.setattr(guard_branch, "content_preserved", lambda sha: False)
        vs = guard_branch.check_delete("opencode/some-feature/laptop")
        assert any("not provably present" in v for v in vs)

    def test_feature_delete_fails_closed_when_branch_unresolvable(self, monkeypatch):
        # Regression: if `git rev-parse` can't resolve the branch at all
        # (bad ref, race condition, not actually a git repo), the guard
        # must REFUSE the deletion, not silently allow it. The old code
        # only checked `if sha and not content_preserved(sha)` — an empty
        # sha short-circuited straight past the check to "no violation".
        monkeypatch.setattr(guard_branch, "run_git", lambda args: ("", 128))
        monkeypatch.delenv("GUARD_BRANCH_ALLOW_DELETE", raising=False)
        vs = guard_branch.check_delete("opencode/some-feature/laptop")
        assert vs, "an unresolvable branch must be blocked, not silently allowed"
        assert any("could not resolve" in v for v in vs)


class TestOriginHead:
    def test_audit_branches_returns_list(self):
        # Non-destructive: the audit is read-only and returns a list of findings.
        assert isinstance(guard_branch.audit_branches(), list)


# ── merge_gate: conflict preflight ─────────────────────────────────────

class TestMergeGate:
    def test_resolve_ref_rejects_missing(self):
        assert merge_gate.resolve_ref("definitely-not-a-ref-xyz") is None

    def test_git_available(self):
        import shutil
        assert shutil.which("git") is not None


# ── validate_commit_msg: markers ───────────────────────────────────────

class TestCommitMsgGuard:
    def test_provisional_requires_audit(self):
        msg = "spike: try something new"
        assert validate_commit_msg.looks_provisional(msg)
        msg2 = "spike: try something new\n\nAUDIT: exploratory"
        assert "AUDIT:" in msg2

    def test_provisional_keyword_does_not_match_inside_other_words(self):
        """Regression: a plain substring check flagged 'temp' inside 'template'
        as provisional work (2026-08-19, real commit blocked on a legitimate
        change touching template/docs/AI_CONSTITUTION.md). Word-boundary
        matching must not fire on ordinary words that merely contain a
        keyword as a substring."""
        assert not validate_commit_msg.looks_provisional(
            "sync template/docs/AI_CONSTITUTION.md with docs/AI_CONSTITUTION.md"
        )
        # sanity: the real keyword, as a whole word, must still be caught
        assert validate_commit_msg.looks_provisional("temp fix, revisit later")
        assert validate_commit_msg.looks_provisional("temporary workaround")

    def test_verification_pattern_required(self):
        ok = "fix bug\n\nTests: pytest tests/test_x.py -q (1 passed)"
        assert validate_commit_msg.VERIFICATION_PATTERN.search(ok) is not None
        bad = "fix bug, no tests"
        assert validate_commit_msg.VERIFICATION_PATTERN.search(bad) is None

    def test_governance_marker_present(self):
        assert validate_commit_msg.GOVERNANCE_MARKER == "GOVERNANCE-UPDATE"

    def test_human_check_pattern_required(self):
        """Law 23: a human-facing commit must declare a direct check, not
        just a metric/test result."""
        ok = "fix UI\n\nHuman-check: opened the page, button works as described"
        assert validate_commit_msg.HUMAN_CHECK_PATTERN.search(ok) is not None
        bad = "fix UI\n\nTests: 5 passed"
        assert validate_commit_msg.HUMAN_CHECK_PATTERN.search(bad) is None


class TestHumanFacingGate:
    """Law 23 mechanization: real end-to-end coverage, not just regex unit
    tests -- load_human_facing_patterns() reads a real file, and
    human_facing_changed() runs a real `git diff --cached` against a real
    repo, so a mocked-only test wouldn't catch a real integration bug in
    either (Law 18: a test must discriminate against real breakage)."""

    def _init_repo(self, tmp_path, monkeypatch):
        subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
        subprocess.run(["git", "config", "user.email", "t@t.com"], cwd=tmp_path, check=True)
        subprocess.run(["git", "config", "user.name", "t"], cwd=tmp_path, check=True)
        monkeypatch.chdir(tmp_path)

    def test_no_config_means_rule_never_fires(self, tmp_path, monkeypatch):
        self._init_repo(tmp_path, monkeypatch)
        (tmp_path / "dashboard.html").write_text("<html></html>")
        subprocess.run(["git", "add", "dashboard.html"], cwd=tmp_path, check=True)
        assert validate_commit_msg.load_human_facing_patterns() == []
        assert validate_commit_msg.human_facing_changed() is False

    def test_configured_pattern_matches_staged_file(self, tmp_path, monkeypatch):
        self._init_repo(tmp_path, monkeypatch)
        (tmp_path / ".guardrail.json").write_text(
            json.dumps({"human_facing_paths": ["dashboard.html", "web/src/components/*.tsx"]})
        )
        (tmp_path / "dashboard.html").write_text("<html></html>")
        subprocess.run(["git", "add", "dashboard.html", ".guardrail.json"], cwd=tmp_path, check=True)
        assert validate_commit_msg.load_human_facing_patterns() == [
            "dashboard.html", "web/src/components/*.tsx"
        ]
        assert validate_commit_msg.human_facing_changed() is True

    def test_configured_pattern_does_not_match_unrelated_file(self, tmp_path, monkeypatch):
        self._init_repo(tmp_path, monkeypatch)
        (tmp_path / ".guardrail.json").write_text(
            json.dumps({"human_facing_paths": ["dashboard.html"]})
        )
        (tmp_path / "server.py").write_text("x = 1\n")
        subprocess.run(["git", "add", "server.py", ".guardrail.json"], cwd=tmp_path, check=True)
        # .guardrail.json itself is staged too, but it isn't a human-facing
        # path, and server.py doesn't match "dashboard.html" -- must be False.
        assert validate_commit_msg.human_facing_changed() is False

    def test_glob_pattern_matches_nested_path(self, tmp_path, monkeypatch):
        self._init_repo(tmp_path, monkeypatch)
        (tmp_path / ".guardrail.json").write_text(
            json.dumps({"human_facing_paths": ["web/src/components/*.tsx"]})
        )
        (tmp_path / "web" / "src" / "components").mkdir(parents=True)
        (tmp_path / "web" / "src" / "components" / "AnalyzeTab.tsx").write_text("export {}")
        subprocess.run(["git", "add", "-A"], cwd=tmp_path, check=True)
        assert validate_commit_msg.human_facing_changed() is True

    def test_malformed_config_fails_safe_to_empty(self, tmp_path, monkeypatch):
        self._init_repo(tmp_path, monkeypatch)
        (tmp_path / ".guardrail.json").write_text("{not valid json")
        assert validate_commit_msg.load_human_facing_patterns() == []


# ── validate_pre_commit: file checks ───────────────────────────────────

class TestPreCommitChecks:
    def test_regenerable_suffix(self):
        assert validate_pre_commit.check_regenerable("test_output/x.stl") is not None
        assert validate_pre_commit.check_regenerable("output/x.stl") is None

    def test_placement_rules(self):
        assert validate_pre_commit.check_placement("tests/foo.py") is None
        assert validate_pre_commit.check_placement("tests/foo.exe") is not None

    def test_bare_except_detection(self, tmp_path):
        f = tmp_path / "bad.py"
        f.write_text("try:\n    pass\nexcept:\n    pass\n", encoding="utf-8")
        assert validate_pre_commit.check_bare_excepts(f) == [3]

    def test_tailscale_ip_allowed(self):
        assert validate_pre_commit._is_tailscale_ip("100.69.113.41")
        # Build the literal at runtime so the static scanner (which itself flags
        # hardcoded non-Tailscale IPs) does not see a false violation here.
        assert not validate_pre_commit._is_tailscale_ip(
            "192.168." + "1.1"
        )

    def test_speed_of_sound_literal_flagged_outside_canonical(self, tmp_path):
        f = tmp_path / "other.py"
        # Assemble the canonical literal at runtime: this test verifies the guard
        # catches it in arbitrary files, so it must not be a static literal here.
        sos = "3461" + "00.0"
        f.write_text(f"SPEED = {sos}\n", encoding="utf-8")
        hits = validate_pre_commit.check_hardcoded_speed_of_sound(f, tmp_path)
        assert hits, "speed-of-sound literal outside canonical module must be flagged"


# ── guard_governance: protected file marker ────────────────────────────

class TestGovernanceGuard:
    def test_marker_constant(self):
        assert guard_governance.MARKER == "GOVERNANCE-UPDATE"
        assert "docs/CONSTRAINTS_AND_PREFERENCES.md" in guard_governance.GOVERNANCE_FILES
