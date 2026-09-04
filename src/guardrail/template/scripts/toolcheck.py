"""Tool registry checker: installed vs declared vs imported vs call-site.

Cross-checks three sources of truth:
  installed  = pip list (what's in the environment)
  declared   = pyproject.toml [project.dependencies] + optional extras
  imported   = AST scan of scripts/, tests/ (whitelisted files), and every
               real src/<package>/ directory (auto-detected, see
               scan_config.get_scan_paths) for top-level imports

Flags:
  FORGOTTEN  - installed + imported nowhere in code (candidate for uninstall/archive)
  PHANTOM    - imported by code but NOT declared in pyproject (must be declared)
  ORPHAN     - declared in pyproject but imported nowhere (superseded?)
  UNWIRED    - imported but no pytest file covers it (integration gap)

Exit code 1 if any PHANTOM or FORGOTTEN exists (the two states that cause
"installed and forgotten" drift). Run as:  python scripts/toolcheck.py
"""
from __future__ import annotations

import ast
import re
import sys
import tomllib
from importlib import metadata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

try:
    from scan_config import get_scan_paths  # normal `python scripts/x.py` run
except ImportError:
    # Same fallback as compliance_watchdog.py/guard_branch.py: a plain sibling
    # import only works when Python itself put scripts/ on sys.path (running
    # the file directly). tests/test_guard_scripts.py loads this module via
    # importlib.util.spec_from_file_location instead, which does not.
    sys.path.insert(0, str(ROOT / "scripts"))
    from scan_config import get_scan_paths

# Libraries that are imported under a different name than the pip package.
PACKAGE_ALIASES = {
    "sklearn": "scikit-learn",
    "skfem": "scikit-fem",
    "yaml": "pyyaml",
    "PIL": "pillow",
    "cv2": "opencv-python",
    "jaxlib": "jax",
    "flax": "flax",
    "bs4": "beautifulsoup4",
    "dotenv": "python-dotenv",
    "distributed": "dask",
    "torchvision": "torchvision",
    "torchaudio": "torchaudio",
    "FreeCAD": "freecad",
    "Part": "freecad",
    "Mesh": "freecad",
    "Import": "freecad",
    "fpdf": "fpdf2",
    "uvicorn": "uvicorn",
}

# Import roots that are genuinely third-party but only present via a FreeCAD
# install (their pip package is `freecad`). We still require `freecad` declared.
FREECAD_MODULES = {"FreeCAD", "Part", "Mesh", "Import"}

# Import roots provided by an external application's bundled Python, with no
# pip package in the host env. Mirrors the FreeCAD case above, but there is no
# pip package to declare (Blender's `bpy` is not the PyPI `bpy`). Declared in
# TOOLS.md under "External applications" instead of pyproject.
EXTERNAL_APP_MODULES = {"bpy"}

# Local top-level package dirs — their whole subtree is never a pip package.
LOCAL_ROOTS = {"backend", "woodwind_designer", "tests", "scripts", "conftest",
               "blender_addon"}

# Third-party roots we knowingly exclude (stdlib / noisy).
STDLIBISH = {
    # pkgutil: real gap found 2026-09-04 -- flagged PHANTOM the moment
    # toolcheck.py started scanning src/guardrail/ (this fix's whole point),
    # which is where the repo's only real import of it lives
    # (src/guardrail/core/registry.py, stdlib plugin-discovery). Genuinely
    # stdlib, just missing from this list until now.
    "pkgutil",
    "os", "sys", "io", "json", "math", "time", "re", "ast", "argparse",
    "pathlib", "dataclasses", "typing", "collections", "functools", "itertools",
    "subprocess", "tempfile", "shutil", "copy", "enum", "abc", "warnings",
    "logging", "random", "struct", "socket", "hashlib", "glob", "urllib",
    "importlib", "uuid", "string", "queue", "threading", "multiprocessing",
    "textwrap", "statistics", "decimal", "fractions", "contextlib", "profile",
    "pstats", "cProfile", "gc", "platform", "signal", "datetime", "pickle",
    "traceback", "unicodedata", "numbers", "operator", "inspect", "csv",
    "base64", "runpy", "sqlite3", "concurrent", "__future__", "trace",
    "tomllib", "unittest", "zipfile", "xml", "types", "builtins", "weakref",
    "configparser", "email", "html", "http", "urllib.request", "tarfile",
    "bz2", "gzip", "zlib", "lzma", "fnmatch", "glob", "pprint", "tokenize",
    "keyword", "linecache", "dis", "code", "codecs", "reprlib", "stringprep",
    "html.parser", "ftplib", "smtplib", "mimetypes", "binascii", "array",
    "asyncio", "select", "selectors", "ssl", "curses", "ctypes", "datetime",
    "calendar", "locale", "gettext", "getpass", "pty", "pwd", "grp", "spwd",
    "resource", "mmap", "msvcrt", "winreg", "winsound", "venv", "ensurepip",
    "this", "antigravity", "turtle", "tkinter", "webbrowser", "zipimport",
    "filecmp", "difflib", "fileinput", "secrets", "stat", "marshal", "token",
}


def _src_package_names() -> set[str]:
    """This project's own importable package name(s) - any directory under
    src/ containing __init__.py.

    Fixes the documented "toolcheck.py false-flags the guardrail import"
    bug: pyproject.toml's [project].name is "lawkeeper" (the distribution
    name), but the actual package is src/guardrail/ - a deliberate rename
    (see pyproject.toml's package-data comment). _declared() only reads
    real third-party dependencies, so it never learns "guardrail" is this
    project's own code; scripts/guard_branch.py's legitimate self-import
    (`from guardrail.config import Config`, its packaged-install fallback
    path) then looked identical to an undeclared third-party dependency.
    A self-import is never phantom - you don't declare your own package as
    a dependency of itself.
    """
    names = set()
    src_dir = ROOT / "src"
    if src_dir.is_dir():
        for entry in src_dir.iterdir():
            if entry.is_dir() and (entry / "__init__.py").exists():
                names.add(entry.name)
    return names


def _is_local(root: str) -> bool:
    """True if the import root is a local package subtree, not a pip package."""
    if root in LOCAL_ROOTS or root in _src_package_names():
        return True
    # backend.foo / woodwind_designer.bar appear as their second segment in
    # ImportFrom.module when scanning relative-import-adjacent code; treat any
    # subpackage dir OR module file under a local root as local. Modules nested
    # deeper than the top level (e.g. backend/experiments/sibling.py imported
    # bare by another experiment) are local too.
    # This loop used to check LOCAL_ROOTS only, so a nested import inside this
    # project's own src/guardrail/ (or any real src/<pkg>/, auto-detected the
    # same way _src_package_names() does) was never caught by this fallback -
    # only the exact top-level package name matched, one line up.
    local_bases = LOCAL_ROOTS | {f"src/{name}" for name in _src_package_names()}
    for base in local_bases:
        base_dir = ROOT / base
        if not base_dir.exists():
            continue
        candidate = base_dir / root
        if candidate.is_dir() or (candidate.with_suffix(".py")).is_file():
            return True
        if any(p.name == root + ".py" or p.name == root for p in base_dir.rglob("*")):
            return True
    return False


def _installed() -> set[str]:
    """Fast enumeration of installed distributions via importlib.metadata."""
    pkgs = set()
    for dist in metadata.distributions():
        name = (dist.metadata.get("Name") or "").strip().lower().replace("_", "-")
        if name:
            pkgs.add(name)
    return pkgs


def _declared() -> dict[str, set[str]]:
    """Return {extra_name: set(package_names)} from pyproject."""
    with open(ROOT / "pyproject.toml", "rb") as f:
        data = tomllib.load(f)
    declared: dict[str, set[str]] = {}
    main = set()
    for dep in data.get("project", {}).get("dependencies", []):
        dep = dep.strip()
        dep = re.sub(r"\[[^\]]*\]", "", dep)  # strip extras: uvicorn[standard]
        main.add(re.sub(r"[<>=~!].*$", "", dep).strip().lower())
    declared["main"] = main
    for extra, deps in data.get("project", {}).get("optional-dependencies", {}).items():
        s = set()
        for dep in deps:
            dep = dep.strip()
            dep = re.sub(r"\[[^\]]*\]", "", dep)
            s.add(re.sub(r"[<>=~!].*$", "", dep).strip().lower())
        declared[extra] = s
    return declared


def _imported() -> set[str]:
    """AST-scan the LIVE pipeline for third-party import roots.

    Live = scripts/, every real src/<package>/ directory (auto-detected via
    scan_config.get_scan_paths, the same resolver compliance_watchdog.py and
    check_local_dependencies.py already use), plus the pytest-whitelisted
    test files. Legacy ad-hoc test scripts in tests/ are intentionally
    excluded (they are not run by pytest and would produce false phantom
    reports) - get_scan_paths()'s own tests/ entry is skipped here for
    that reason; the whitelist below is scanned instead.

    Used to hardcode ["backend", "scripts", "woodwind_designer"] - leftover
    directory names from the project this repo was extracted from, neither
    of which exist here. This project's own real source, src/guardrail/,
    was never scanned as a result: its imports were invisible to the
    phantom/orphan/forgotten dependency report.
    """
    imported: set[str] = set()

    def _scan_file(path: Path) -> None:
        if "__pycache__" in str(path):
            return
        try:
            tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
        except SyntaxError:
            return
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    root = alias.name.split(".")[0]
                    if not _is_local(root) and root not in STDLIBISH:
                        imported.add(root)
            elif isinstance(node, ast.ImportFrom):
                if node.level > 0:  # relative import -> local package
                    continue
                if node.module:
                    root = node.module.split(".")[0]
                    if not _is_local(root) and root not in STDLIBISH:
                        imported.add(root)

    for base in get_scan_paths(ROOT):
        if base.name == "tests":
            continue  # scanned separately below, whitelist-only
        for path in base.rglob("*.py"):
            _scan_file(path)
    # whitelisted tests only
    for tf in _whitelisted_test_files():
        path = ROOT / "tests" / tf
        if path.exists():
            _scan_file(path)
    return imported


def _whitelisted_test_files() -> set[str]:
    with open(ROOT / "pyproject.toml", "rb") as f:
        data = tomllib.load(f)
    return set(data.get("tool", {}).get("pytest", {}).get("ini_options", {}).get("python_files", []))


def _pytest_covers_import(import_root: str) -> bool:
    """Heuristic: does any whitelisted test file import this root?"""
    for tf in _whitelisted_test_files():
        path = ROOT / "tests" / tf
        if path.exists():
            try:
                tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
            except SyntaxError:
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name.split(".")[0] == import_root:
                            return True
                elif isinstance(node, ast.ImportFrom):
                    if node.level > 0:
                        continue
                    if node.module and node.module.split(".")[0] == import_root:
                        return True
    return False


def _resolve_pkg(import_root: str) -> str:
    return PACKAGE_ALIASES.get(import_root, import_root).lower()


def phantom_deps(declared_all: set[str], imported_pkgs: set[str]) -> list[str]:
    """Imported-but-undeclared pip packages (excluding external-app roots)."""
    freecad_declared = "freecad" in declared_all
    return sorted(
        p for p in imported_pkgs
        if p not in declared_all
        and p not in EXTERNAL_APP_MODULES
        and (p != "freecad" or not freecad_declared)
    )


def main() -> int:
    strict = "--strict" in sys.argv

    installed = _installed()
    declared = _declared()
    declared_all = set().union(*declared.values()) if declared else set()
    imported = _imported()

    # Map import roots to pip package names
    imported_pkgs = {_resolve_pkg(r) for r in imported}

    phantom = phantom_deps(declared_all, imported_pkgs)
    orphan = sorted(p for p in declared_all if p not in installed)
    forgotten = sorted(
        p for p in installed
        if p not in declared_all
        and p not in imported_pkgs
        and p not in {"pip", "setuptools", "wheel", "pytest", "ruff"}
    )

    print("=== TOOL REGISTRY ===")
    print(f"\nInstalled: {len(installed)} | Declared: {len(declared_all)} | Imported: {len(imported_pkgs)}")

    print("\n-- PHANTOM (imported by code, NOT declared in pyproject) --")
    if phantom:
        for p in phantom:
            covered = _pytest_covers_import(p) or any(
                p == _resolve_pkg(r) for r in imported if _pytest_covers_import(r)
            )
            print(f"  {p:28s} {'[tested]' if covered else '[NOT covered by a registered test]'}")
    else:
        print("  (none)")

    print("\n-- ORPHAN (declared in pyproject, NOT installed) --")
    if orphan:
        for p in orphan:
            print(f"  {p}")
    else:
        print("  (none)")

    print("\n-- FORGOTTEN (installed, not declared, imported nowhere) --")
    if forgotten:
        for p in forgotten:
            print(f"  {p}")
    else:
        print("  (none)")

    # Any declared-but-unwired (imported somewhere but no registered test imports it)
    print("\n-- UNWIRED (imported by code, no registered pytest file touches it) --")
    unwired = []
    for r in sorted(imported):
        pkg = _resolve_pkg(r)
        if pkg in declared_all or pkg in imported_pkgs:
            if not _pytest_covers_import(r):
                unwired.append(r)
    for r in unwired:
        print(f"  {r}  -> {_resolve_pkg(r)}")

    print()
    # Strict mode also fails on declared packages that the code imports but are
    # not installed. This prevents merging code that depends on a missing local
    # dependency across machines with different environments.
    active_orphan = sorted(p for p in orphan if p in imported_pkgs)
    problems = list(phantom)
    if strict and active_orphan:
        problems.extend(active_orphan)
    if problems:
        print(f"RESULT: FAIL — {len(problems)} dependency problem(s):")
        for p in problems:
            print(f"  - {p}")
        if strict and active_orphan:
            print("\nRun 'pip install -e \".[dev,cad,test]\"' or the missing extras.")
        return 1
    print("RESULT: PASS — all imported tools are declared in pyproject.")
    if strict:
        if active_orphan:
            print(f"(strict mode: {len(active_orphan)} declared+imported package(s) not installed, listed above)")
        else:
            print("(strict mode: all declared packages used by the code are installed)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
