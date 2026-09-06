"""Tests for orphan_scan.py -- real, mechanical Law 21 detection.

Uses a real, temporary git repo (git init + real commits) rather than
mocking git entirely -- this tool's whole value is real commit-history
data, and a test that fakes the git layer wouldn't actually prove the
tool works against real git output shapes.
"""
import subprocess
from pathlib import Path

from conftest import load_script

orphan_scan = load_script("orphan_scan.py")


def _git(repo: Path, *args):
    subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, check=True)


def _init_real_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "testrepo"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "test@test.com")
    _git(repo, "config", "user.name", "Test")
    return repo


def _commit_file(repo: Path, rel_path: str, content: str):
    p = repo / rel_path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    _git(repo, "add", rel_path)
    _git(repo, "commit", "-q", "-m", f"add {rel_path}")


class TestIsOneOffTaskScript:
    def test_matches_known_one_off_patterns(self):
        assert orphan_scan.is_one_off_task_script("export_bass_clarinet_stl")
        assert orphan_scan.is_one_off_task_script("refine_pvc_chalumeau")
        assert orphan_scan.is_one_off_task_script("generate_baseline")
        assert orphan_scan.is_one_off_task_script("validate_trumpet_baseline")
        assert orphan_scan.is_one_off_task_script("test_something")

    def test_matches_2026_08_21_added_patterns(self):
        """Real false positives found by actually reading all 11
        remaining Windwright candidates from the 2026-08-21 round-up --
        10 of 11 were legitimate one-off utilities, not forgotten code."""
        assert orphan_scan.is_one_off_task_script("debug_chalumier_compare")
        assert orphan_scan.is_one_off_task_script("verify_cone_theory")
        assert orphan_scan.is_one_off_task_script("view_browser")
        assert orphan_scan.is_one_off_task_script("propose_tasks")
        assert orphan_scan.is_one_off_task_script("_run_benchmark_live")
        assert orphan_scan.is_one_off_task_script("blender_render_stl")
        assert orphan_scan.is_one_off_task_script("validate_chromatic_flute")
        assert orphan_scan.is_one_off_task_script("phase5_export_all")

    def test_does_not_match_real_infrastructure_names(self):
        assert not orphan_scan.is_one_off_task_script("train_lora")
        assert not orphan_scan.is_one_off_task_script("team_chat_monitor")
        assert not orphan_scan.is_one_off_task_script("gamification_test")
        assert not orphan_scan.is_one_off_task_script("orphan_scan")


class TestScanRepoRealGit:
    def test_referenced_script_is_not_flagged(self, tmp_path):
        repo = _init_real_repo(tmp_path)
        _commit_file(repo, "scripts/helper.py", "def do_thing(): pass\n")
        _commit_file(repo, "scripts/main.py", "# uses scripts/helper.py's do_thing()\n")
        results = orphan_scan.scan_repo(repo)
        helper = next(r for r in results if r["basename"] == "helper")
        assert helper["external_refs"] > 0

    def test_genuinely_unreferenced_non_one_off_script_is_flagged(self, tmp_path):
        repo = _init_real_repo(tmp_path)
        _commit_file(repo, "scripts/abandoned_tool.py", "def unused(): pass\n")
        results = orphan_scan.scan_repo(repo)
        r = next(r for r in results if r["basename"] == "abandoned_tool")
        assert r["external_refs"] == 0
        assert not r["is_one_off"]
        assert r["commits"] == 1

    def test_one_off_named_script_not_flagged_even_with_zero_refs(self, tmp_path):
        repo = _init_real_repo(tmp_path)
        _commit_file(repo, "scripts/export_widget_stl.py", "def export(): pass\n")
        results = orphan_scan.scan_repo(repo)
        r = next(r for r in results if r["basename"] == "export_widget_stl")
        assert r["external_refs"] == 0
        assert r["is_one_off"] is True  # excluded from flagging by naming pattern, not by reference count

    def test_self_reference_in_own_docstring_does_not_count_as_external(self, tmp_path):
        """Real regression case: a script's own docstring often repeats
        its own filename (e.g. 'Usage: python scripts/foo.py') -- that
        must not be counted as an external reference to itself."""
        repo = _init_real_repo(tmp_path)
        _commit_file(repo, "scripts/self_describing.py",
                     '"""Usage: python scripts/self_describing.py [args]\n\nself_describing does a thing.\n"""\n')
        results = orphan_scan.scan_repo(repo)
        r = next(r for r in results if r["basename"] == "self_describing")
        assert r["external_refs"] == 0

    def test_no_scripts_or_tools_dir_returns_empty(self, tmp_path):
        repo = _init_real_repo(tmp_path)
        _commit_file(repo, "src/thing.py", "pass\n")
        assert orphan_scan.scan_repo(repo) == []

    def test_package_dir_under_src_is_auto_discovered_and_scanned(self, tmp_path):
        """Real gap found 2026-09-05, cross-repo (Falcun ported this
        scanner and hit it against agent/, src/falcun/): the original
        scripts/tools-only scope meant a module built, tested, and never
        wired into any real code path in a src/ package would never even
        become a candidate. Package dirs are now auto-discovered via
        src/*/__init__.py rather than hardcoded to any one repo's package
        name."""
        repo = _init_real_repo(tmp_path)
        _commit_file(repo, "src/mypackage/__init__.py", "")
        _commit_file(repo, "src/mypackage/abandoned.py", "def unused(): pass\n")
        _commit_file(repo, "src/mypackage/used.py", "def real(): pass\n")
        _commit_file(repo, "src/mypackage/caller.py", "from mypackage.used import real\n")
        results = orphan_scan.scan_repo(repo)
        by_basename = {r["basename"]: r for r in results}
        assert "abandoned" in by_basename, "src/*/ packages must now be scanned as candidates"
        assert by_basename["abandoned"]["production_refs"] == 0
        assert by_basename["used"]["production_refs"] > 0

    def test_scaffolding_template_dir_is_excluded_from_candidates(self, tmp_path):
        """template/ and template_extras/ trees are copied wholesale by
        path (cli.py's _copy_template_tree), never referenced by
        individual basename -- every file in them would otherwise
        false-positive as an orphan. Excluded from candidate collection
        entirely rather than left to flag on every single scaffolded
        file."""
        repo = _init_real_repo(tmp_path)
        _commit_file(repo, "src/mypackage/__init__.py", "")
        _commit_file(repo, "src/mypackage/template/scaffold_only.py", "# copied wholesale\n")
        results = orphan_scan.scan_repo(repo)
        assert not any(r["basename"] == "scaffold_only" for r in results), (
            "scaffolding under a template/ dir must not become a candidate at all"
        )

    def test_dynamically_loaded_module_is_a_documented_false_positive(self, tmp_path):
        """Confirmed live against this repo's own src/guardrail/laws/:
        a module discovered via pkgutil.iter_modules rather than
        imported by literal name will show 0 production_refs despite
        being real, wired-in code. Not a bug -- documented in the
        module docstring as a real, known blind spot; this test proves
        the scanner behaves exactly as documented, not silently
        different."""
        repo = _init_real_repo(tmp_path)
        _commit_file(repo, "src/mypackage/__init__.py", "")
        _commit_file(
            repo, "src/mypackage/loader.py",
            "import pkgutil, importlib\n"
            "for info in pkgutil.iter_modules(__path__):\n"
            "    importlib.import_module(f'mypackage.{info.name}')\n",
        )
        _commit_file(repo, "src/mypackage/plugin_one.py", "def run(): pass\n")
        results = orphan_scan.scan_repo(repo)
        plugin = next(r for r in results if r["basename"] == "plugin_one")
        assert plugin["production_refs"] == 0, (
            "a dynamically-discovered module is a documented false positive, "
            "not something this heuristic scanner can resolve by itself"
        )

    def test_production_refs_excludes_test_only_and_doc_only_mentions(self, tmp_path):
        """Real gap found 2026-09-05, cross-repo: Falcun's port of this
        scanner proved a module referenced only by its own test file
        plus one doc mention (agent/zotero_bridge.py: 8 external_refs,
        0 real production callers) read as "referenced" under the old
        single-count version, hiding a genuine orphan. Reproduced here
        with the same shape: a script mentioned only in its own test
        file and in a doc must show external_refs > 0 but
        production_refs == 0, and must now be flagged."""
        repo = _init_real_repo(tmp_path)
        _commit_file(repo, "scripts/only_tested.py", "def do_thing(): pass\n")
        _commit_file(repo, "tests/test_only_tested.py",
                      "# tests only_tested.do_thing\nfrom only_tested import do_thing\n")
        _commit_file(repo, "docs/NOTES.md", "See scripts/only_tested.py for details.\n")
        results = orphan_scan.scan_repo(repo)
        r = next(r for r in results if r["basename"] == "only_tested")
        assert r["external_refs"] > 0, "the test file + doc mention should still count as external_refs"
        assert r["production_refs"] == 0, "test-file-only and doc-only mentions must not count as production"

    def test_untracked_dotdir_content_does_not_count_as_a_reference(self, tmp_path):
        """Real bug found 2026-09-05, re-running this scan against
        Windwright: a stale git worktree checkout sitting on disk under
        the repo root (.claude/worktrees/<name>/, untracked, confirmed via
        `git ls-files`) contained its own copy of an orphaned script.
        Every basename match inside that stale copy inflated the real
        script's "external reference" count -- a real orphan was hidden
        (external_refs > 0) purely because of local disk clutter, not any
        real consumer. Fixed by skipping any dot-prefixed directory
        component under repo_root when building the haystack, matching
        the existing .git exclusion generalized rather than special-cased
        per clutter directory."""
        repo = _init_real_repo(tmp_path)
        _commit_file(repo, "scripts/abandoned_tool.py", "def unused(): pass\n")
        # Untracked, not committed -- a real worktree/cache directory is
        # never part of the tracked tree either; still sits on disk.
        stale = repo / ".claude" / "worktrees" / "some-worktree" / "scripts" / "abandoned_tool.py"
        stale.parent.mkdir(parents=True)
        stale.write_text("# a stale duplicate of abandoned_tool mentioning itself\n"
                          "# abandoned_tool abandoned_tool abandoned_tool\n", encoding="utf-8")

        results = orphan_scan.scan_repo(repo)

        r = next(r for r in results if r["basename"] == "abandoned_tool")
        assert r["external_refs"] == 0, (
            "a stale, untracked worktree copy's self-mentions must not count "
            "as external references to the real script"
        )
