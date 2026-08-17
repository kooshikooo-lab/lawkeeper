"""Check that the local environment can run the imported declared dependencies.

Run this before merging branches from another machine (especially cross-OS or
when one machine has installed optional extras the other has not). It flags
packages that are:
  - declared in pyproject.toml (any extra), and
  - imported by the live code (backend/, scripts/, woodwind_designer/), but
  - NOT installed in the current interpreter.

Usage:
    python scripts/check_local_dependencies.py
    python scripts/check_local_dependencies.py --warn  # non-zero exit on missing

Exit:
    0 = all imported declared dependencies are installed
    1 = one or more imported declared dependencies are missing
"""
from __future__ import annotations

import argparse
import sys
import tomllib
from importlib import metadata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _installed() -> set[str]:
    pkgs = set()
    for dist in metadata.distributions():
        name = (dist.metadata.get("Name") or "").strip().lower().replace("_", "-")
        if name:
            pkgs.add(name)
    return pkgs


def _declared() -> set[str]:
    with open(ROOT / "pyproject.toml", "rb") as f:
        data = tomllib.load(f)
    declared = set()
    for dep in data.get("project", {}).get("dependencies", []):
        declared.add(_strip(dep))
    for extra, deps in data.get("project", {}).get("optional-dependencies", {}).items():
        for dep in deps:
            declared.add(_strip(dep))
    return declared


def _strip(dep: str) -> str:
    dep = dep.strip()
    dep = dep.split("[", 1)[0]
    dep = dep.split("<", 1)[0].split(">", 1)[0].split("=", 1)[0].split("~", 1)[0]
    dep = dep.split("!", 1)[0]
    return dep.strip().lower().replace("_", "-")


def _imported_roots() -> set[str]:
    import ast

    stdlibish = {
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
        "configparser", "email", "html", "http", "tarfile", "bz2", "gzip",
        "zlib", "lzma", "fnmatch", "pprint", "tokenize", "keyword", "linecache",
        "dis", "code", "codecs", "reprlib", "stringprep", "html.parser", "ftplib",
        "smtplib", "mimetypes", "binascii", "array", "asyncio", "select", "selectors",
        "ssl", "curses", "ctypes", "calendar", "locale", "gettext", "getpass",
        "pty", "pwd", "grp", "spwd", "resource", "mmap", "msvcrt", "winreg",
        "winsound", "venv", "ensurepip", "this", "antigravity", "turtle",
        "tkinter", "webbrowser", "zipimport",
    }
    local_roots = {"backend", "woodwind_designer", "tests", "scripts", "conftest", "blender_addon"}
    imported = set()

    def _is_local(root: str) -> bool:
        if root in local_roots:
            return True
        for base in local_roots:
            base_dir = ROOT / base
            if not base_dir.exists():
                continue
            candidate = base_dir / root
            if candidate.is_dir() or candidate.with_suffix(".py").is_file():
                return True
            if any(p.name == root + ".py" or p.name == root for p in base_dir.rglob("*")):
                return True
        return False

    def _scan_file(path: Path):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
        except SyntaxError:
            return
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    root = alias.name.split(".")[0]
                    if not _is_local(root) and root not in stdlibish:
                        imported.add(root)
            elif isinstance(node, ast.ImportFrom):
                if node.level > 0:
                    continue
                if node.module:
                    root = node.module.split(".")[0]
                    if not _is_local(root) and root not in stdlibish:
                        imported.add(root)

    for d in ["backend", "scripts", "woodwind_designer"]:
        base = ROOT / d
        if base.exists():
            for path in base.rglob("*.py"):
                if "__pycache__" in str(path):
                    continue
                _scan_file(path)
    return imported


def _resolve(pkg: str) -> str:
    aliases = {
        "sklearn": "scikit-learn",
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
        "bpy": "bpy",  # external, not on PyPI
    }
    return aliases.get(pkg, pkg).lower().replace("_", "-")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--warn", action="store_true", help="Non-zero exit if missing")
    args = parser.parse_args()

    installed = _installed()
    declared = _declared()
    imported = {_resolve(r) for r in _imported_roots()}

    missing = sorted(declared & imported - installed)

    print("=== Local dependency check ===")
    print(f"Declared packages: {len(declared)}")
    print(f"Imported packages: {len(imported)}")
    print(f"Installed packages: {len(installed)}")
    print()
    if missing:
        print(f"Missing imported declared dependencies ({len(missing)}):")
        for p in missing:
            print(f"  - {p}")
        print("\nInstall with: pip install -e \".[dev,cad,test]\"")
        if args.warn:
            return 1
        return 0
    print("All imported declared dependencies are installed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
