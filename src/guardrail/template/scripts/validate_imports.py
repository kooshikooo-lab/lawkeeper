"""Check Python imports for references to deleted modules and unresolved names.

Usage:
    python scripts/validate_imports.py
    python scripts/validate_imports.py --path path/to/file.py

Exit codes:
    0 = all imports resolvable
    1 = deleted/unresolved imports detected
"""

import argparse
import ast
import importlib.util
import os
import subprocess
import sys
from pathlib import Path


# Modules that are known to have been deleted/moved from THIS project. Keep in
# sync with this repo's own history — an import of one gets a clear "you're
# importing something that used to exist and was removed" message instead of
# the generic "cannot be resolved" from resolve_module() below (which still
# catches it either way; this dict only makes the error friendlier).
#
# Used to hardcode entries (backend.archived_optimizers, woodwind_designer,
# ...) inherited from the project this repo was extracted from — modules
# that were never part of lawkeeper's own history and so could never
# usefully match anything a lawkeeper contributor actually imports. Empty
# until this project deletes/moves a module of its own.
DELETED_MODULES: set[str] = set()


REPO_ROOT = Path(__file__).resolve().parent.parent


def staged_files():
    """Return staged Python files (relative to repo root)."""
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR"],
        capture_output=True, text=True, encoding="utf-8", errors="replace"
    )
    if result.returncode != 0:
        return []
    return [line.strip() for line in result.stdout.splitlines() if line.strip().endswith(".py")]


def resolve_module(name):
    """Try to resolve a module/import name. Returns True if resolvable."""
    # Add repo root to sys.path so local packages can be discovered.
    repo_root = str(REPO_ROOT)
    if repo_root not in sys.path:
        sys.path.insert(0, repo_root)
    try:
        spec = importlib.util.find_spec(name)
        return spec is not None
    except (ModuleNotFoundError, ImportError):
        return False


def check_imports(path: Path, rel: str) -> list[str]:
    """Return list of error messages for imports in the given Python file."""
    errors = []
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            source = f.read()
    except OSError as e:
        return [f"{rel}: cannot read file — {e}"]

    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        return [f"{rel}:{e.lineno}: syntax error — {e.msg}"]

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                name = alias.name
                if name in DELETED_MODULES or name.split(".")[0] in DELETED_MODULES:
                    errors.append(f"{rel}:{node.lineno}: import from deleted module '{name}'")
                elif not resolve_module(name):
                    errors.append(f"{rel}:{node.lineno}: import '{name}' cannot be resolved")

        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            level = node.level
            if level > 0:
                # Relative import. Check if the module file exists relative to rel_file.
                parent = (REPO_ROOT / rel).parent
                parts = module.split(".") if module else []
                for _ in range(level - 1):
                    parent = parent.parent
                candidate = parent
                for part in parts:
                    candidate = candidate / part
                # Accept a package directory with __init__.py or a .py module.
                if candidate.with_suffix(".py").is_file() or (candidate.is_dir() and (candidate / "__init__.py").is_file()):
                    continue
                mod_name = "." * level + module
                errors.append(f"{rel}:{node.lineno}: relative import '{mod_name}' cannot be resolved")
            else:
                full = module
                if full in DELETED_MODULES or full.split(".")[0] in DELETED_MODULES:
                    errors.append(f"{rel}:{node.lineno}: import from deleted module '{full}'")
                elif not resolve_module(full):
                    errors.append(f"{rel}:{node.lineno}: import '{full}' cannot be resolved")

    return errors


def main():
    parser = argparse.ArgumentParser(description="Check Python imports for deleted/unresolved references")
    parser.add_argument("--path", type=str, help="check a single file (relative to repo root)")
    args = parser.parse_args()

    if args.path:
        rels = [args.path]
    else:
        rels = staged_files()
        if not rels:
            print("No staged Python files to check.")
            return 0

    all_errors = []
    for rel in rels:
        path = REPO_ROOT / rel
        if not path.is_file():
            continue
        all_errors.extend(check_imports(path, rel))

    if all_errors:
        print("IMPORT ERRORS:")
        for e in all_errors:
            print(f"  - {e}")
        return 1

    print(f"OK: imports resolvable for {len(rels)} Python file(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
