"""Mutation-driven tests for gate_pretooluse.py (mutmut run, 2026-10-11).

Split from test_gate_pretooluse.py (500-line module limit). Each group pins
behavior a surviving mutant showed was unpinned: the verdict level/branch/
reason exactly as the human sees them, the argument parsers' edge cases, and
the Windows path translation (exercised on every platform by faking os.name).
"""
import os
import sys
import types
from pathlib import Path

# Imported by name (see test_gate_pretooluse.py) so mutmut can attribute tests.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts import gate_pretooluse as gate  # noqa: E402

_ALL_REASON = ("a force/delete push with --all/--mirror, which can update multiple refs "
               "(including a canonical branch) without naming any of them explicitly")
_VAR_SUFFIX = "(shell variable/substitution)"


class TestVerdictsExact:
    def test_risk_stores_its_three_fields(self):
        r = gate.Risk("ask", "b", "why")
        assert (r.level, r.branch, r.reason) == ("ask", "b", "why")

    def test_multi_ref_force_is_ask_with_reason(self):
        for cmd in ("git push --force --all", "git push --delete origin --mirror"):
            r = gate.inspect_command(cmd)
            assert (r.level, r.branch, r.reason) == ("ask", None, _ALL_REASON), cmd

    def test_unresolvable_component_without_branch_is_ask(self):
        r = gate.inspect_command("git push --force $REMOTE")
        assert (r.level, r.branch) == ("ask", None)
        assert r.reason == ("a force/delete push with no explicit branch and an unresolvable "
                            "(shell variable/substitution) component")

    def test_unresolvable_current_branch_is_ask(self, monkeypatch):
        monkeypatch.setattr(gate, "_current_branch", lambda cwd=None: None)
        r = gate.inspect_command("git push --force")
        assert (r.level, r.branch) == ("ask", None)
        assert r.reason == ("a force/delete push with no explicit branch, and the current branch "
                            "could not be resolved (unresolvable directory change, or not a git checkout)")

    def test_canonical_current_branch_reason(self, monkeypatch):
        monkeypatch.setattr(gate, "_current_branch", lambda cwd=None: "main")
        r = gate.inspect_command("git push --force")
        assert (r.level, r.branch) == ("hardline", "main")
        assert r.reason == "a force/delete push with no explicit refspec, on canonical branch 'main'"

    def test_explicit_canonical_target_reason(self):
        r = gate.inspect_command("git push --force origin main")
        assert r.reason == "a force/delete push targeting canonical branch 'main'"

    def test_unresolvable_target_reason(self):
        r = gate.inspect_command("git push --force origin $B")
        assert (r.level, r.branch) == ("ask", None)
        assert r.reason == f"a force/delete push whose target '$B' could not be resolved {_VAR_SUFFIX}"

    def test_branch_delete_reasons(self):
        r = gate.inspect_command("git branch -D main")
        assert (r.level, r.branch) == ("hardline", "main")
        assert r.reason == "a branch delete targeting canonical branch 'main'"
        r = gate.inspect_command("git branch -D $B")
        assert (r.level, r.branch) == ("ask", None)
        assert r.reason == f"a branch delete whose target '$B' could not be resolved {_VAR_SUFFIX}"

    def test_branch_without_delete_flag_is_not_inspected(self):
        assert gate.inspect_command("git branch main") is None
        assert gate.inspect_command("git branch -a") is None

    def test_push_delete_flag_alone_is_risky(self):
        r = gate.inspect_command("git push --delete origin main")
        assert (r.level, r.branch) == ("hardline", "main")

    def test_non_push_git_command_is_no_opinion(self):
        assert gate.inspect_command("git status") is None
        assert gate.inspect_command("git status && git log") is None

    def test_hardline_outranks_an_earlier_ask(self):
        r = gate.inspect_command("git push --force $X && git push --force origin main")
        assert r.level == "hardline"

    def test_first_ask_is_kept_over_a_later_ask(self):
        r = gate.inspect_command("git push --force $X && git push --force origin $Y")
        assert r.level == "ask" and "unresolvable" in r.reason

    def test_a_valueless_git_option_does_not_hide_a_later_push(self):
        assert gate.inspect_command("git --version && git push -f origin main").level == "hardline"


class TestTokenisation:
    def test_quoted_arguments_are_unquoted(self):
        assert gate.inspect_command("git push --force 'origin' \"main\"").level == "hardline"

    def test_absolute_git_path_is_recognised(self):
        assert gate.inspect_command("/usr/bin/git push -f origin main").level == "hardline"
        # Known gap (card blind_spot): shlex posix mode eats backslashes, so an
        # unquoted C:\...\git path is not recognised by inspect_command.

    def test_basename(self):
        assert gate._basename("/a/b/git") == "git"
        assert gate._basename("a\\b\\git") == "git"
        assert gate._basename("git") == "git"

    def test_backtick_substitution_is_unresolvable(self):
        r = gate.inspect_command("git push --force origin `echo main`")
        assert r.level == "ask"

    def test_refspec_parsing(self):
        assert gate._parse_push_refspec("main") == ("main", False)
        assert gate._parse_push_refspec("a:b") == ("b", False)
        assert gate._parse_push_refspec("a:b:main") == ("b:main", False)
        assert gate._parse_push_refspec(":main") == ("main", True)
        assert gate._parse_push_refspec("+main") == ("main", True)


class TestCurrentBranch:
    def test_branch_name_returned_only_on_success(self, monkeypatch):
        for out, code, want in (("feat", 0, "feat"), ("garbage", 1, None),
                                ("", 0, None), ("HEAD", 0, None), ("head", 0, "head")):
            monkeypatch.setattr(gate.guard_branch, "run_git", lambda a, o=out, c=code: (o, c))
            assert gate._current_branch() == want, (out, code)

    def test_dash_C_prefix_is_used_when_a_directory_is_given(self, monkeypatch):
        seen = []
        monkeypatch.setattr(gate.guard_branch, "run_git", lambda a: seen.append(a) or ("x", 0))
        gate._current_branch("/some/dir")
        gate._current_branch()
        assert seen[0][:2] == ["-C", "/some/dir"] and seen[1][0] == "rev-parse"


class TestJoinDir:
    def test_unresolvable_targets(self):
        U = gate._UNKNOWN_DIR
        assert gate._join_dir(U, "x") is U
        assert gate._join_dir(None, "") is U
        assert gate._join_dir(None, "-") is U
        assert gate._join_dir(None, "~") is U
        assert gate._join_dir(None, "~/x") is U
        assert gate._join_dir(None, "$X") is U
        assert gate._join_dir("/b", "`x`") is U

    def test_resolvable_targets(self):
        assert gate._join_dir(None, "rel") == "rel"
        assert gate._join_dir("base", "rel") == os.path.join("base", "rel")
        assert gate._join_dir("base", "C:/x") == "C:/x"
        assert gate._join_dir("base", "c:/x") == "c:/x"
        assert gate._join_dir("base", os.path.abspath("x")) == os.path.abspath("x")


class TestMsysToNative:
    @staticmethod
    def _fake_os(monkeypatch, name):
        monkeypatch.setattr(gate, "os", types.SimpleNamespace(name=name, path=os.path, environ=os.environ))

    def test_translates_drive_paths_on_windows(self, monkeypatch):
        self._fake_os(monkeypatch, "nt")
        assert gate._msys_to_native("/e/lawkeeper") == "E:/lawkeeper"
        assert gate._msys_to_native("/E/x") == "E:/x"
        assert gate._msys_to_native("/e") == "E:/"
        assert gate._msys_to_native("/e/") == "E:/"

    def test_leaves_other_shapes_alone(self, monkeypatch):
        self._fake_os(monkeypatch, "nt")
        for p in ("/ee/x", "rel/x", "C:/x", "/", ""):
            assert gate._msys_to_native(p) == p

    def test_noop_off_windows(self, monkeypatch):
        self._fake_os(monkeypatch, "posix")
        assert gate._msys_to_native("/e/lawkeeper") == "/e/lawkeeper"


class TestParseGitInvocation:
    def test_dash_C_reroots_and_chains(self, tmp_path):
        base = str(tmp_path)
        sub, args, cwd = gate._parse_git_invocation(["git", "-C", "sub", "push", "-f"], base)
        assert (sub, args, cwd) == ("push", ["-f"], os.path.join(base, "sub"))
        _, _, cwd = gate._parse_git_invocation(["git", "-C", base, "-C", "b", "push"], None)
        assert cwd == os.path.join(base, "b")

    def test_option_forms_and_cursor_advance(self):
        U = gate._UNKNOWN_DIR
        for toks in (["git", "--git-dir=/g", "push", "x"], ["git", "--git-dir", "/g", "push", "x"],
                     ["git", "--work-tree=/w", "push", "x"], ["git", "--work-tree", "/w", "push", "x"]):
            sub, args, cwd = gate._parse_git_invocation(toks, "/b")
            assert (sub, args) == ("push", ["x"]) and cwd is U, toks
        for toks in (["git", "-c", "a=b", "push", "x"], ["git", "--no-pager", "push", "x"],
                     ["git", "--namespace", "n", "push", "x"]):
            sub, args, cwd = gate._parse_git_invocation(toks, "/b")
            assert (sub, args, cwd) == ("push", ["x"], "/b"), toks

    def test_no_subcommand(self):
        assert gate._parse_git_invocation(["git", "--no-pager"], None) is None
        assert gate._parse_git_invocation(["git", "-C"], None) is None
        assert gate._parse_git_invocation(["git"], None) is None


class TestDirectoryTrackingEdges:
    def test_chdir_and_chained_relative_cd(self, two_checkouts):
        _, main = two_checkouts
        parent, leaf = main.rsplit("/", 1)
        assert gate.inspect_command(f"chdir {main} && git push --force").level == "hardline"
        assert gate.inspect_command(f"cd {parent} && cd {leaf} && git push --force").level == "hardline"

    def test_popd_cd_without_arg_and_cd_with_two_args_are_unknown(self, two_checkouts):
        for cmd in ("popd && git push --force", "cd && git push --force",
                    "cd a b && git push --force"):
            assert gate.inspect_command(cmd).level == "ask", cmd


class TestOverrideEnv:
    def test_exact_match_only(self, monkeypatch):
        monkeypatch.delenv("GUARD_BRANCH_ALLOW_FORCE", raising=False)
        monkeypatch.delenv("GUARD_BRANCH_ALLOW_DELETE", raising=False)
        assert gate._overridden(None) is False and gate._overridden("") is False
        assert gate._overridden("main") is False
        monkeypatch.setenv("GUARD_BRANCH_ALLOW_DELETE", "main")
        assert gate._overridden("main") is True and gate._overridden("other") is False
        monkeypatch.delenv("GUARD_BRANCH_ALLOW_DELETE")
        monkeypatch.setenv("GUARD_BRANCH_ALLOW_FORCE", "main")
        assert gate._overridden("main") is True
