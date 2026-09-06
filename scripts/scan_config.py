"""Shared scan-path resolution for Lawkeeper's own guard scripts
(compliance_watchdog.py, check_local_dependencies.py).

Fixes a real bug: both scripts used to hardcode `backend/` and
`woodwind_designer/` - directories from the Windwright project this
repo was originally extracted from. Lawkeeper's own compliance tools
never scanned Lawkeeper's own src/guardrail/ as a result - a governance
tool that couldn't see itself. One shared resolver instead of two
separately-hardcoded (and separately buggy) copies.
"""
from __future__ import annotations

import json
from pathlib import Path


def get_scan_paths(repo_root: Path) -> list[Path]:
    """Directories to scan for compliance/dependency checks, in priority order:

    1. `.guardrail.json`'s "scan_paths" (explicit project config - what
       `lawkeeper init` lets a project tell its own tooling to scan,
       written by the project owner, not guessed).
    2. Auto-detected package directories under `src/`, for projects using
       the common src-layout (this repo included). Deliberately does NOT
       guess the package name from pyproject.toml's [project].name - this
       repo is the reason why: its distribution name is "lawkeeper" but
       the actual package directory is `src/guardrail/` (a documented,
       deliberate rename - see pyproject.toml's package-data comment).
       Guessing `src/<project.name>` would have missed it entirely, the
       same "governance tool that can't see itself" bug all over again.
       Instead, every direct subdirectory of `src/` containing an
       `__init__.py` is treated as a real package and scanned.
    3. `scripts/` and `tests/` at the repo root, since those exist in most
       Lawkeeper-governed projects regardless of source layout.

    Never falls back to another, unrelated project's directories - that
    was the actual bug being fixed here.
    """
    guardrail_json = repo_root / ".guardrail.json"
    if guardrail_json.exists():
        try:
            cfg = json.loads(guardrail_json.read_text(encoding="utf-8"))
            configured = cfg.get("scan_paths")
            if configured:
                return [repo_root / p for p in configured]
        except (OSError, ValueError):
            pass

    paths: list[Path] = []
    src_dir = repo_root / "src"
    if src_dir.is_dir():
        for entry in sorted(src_dir.iterdir()):
            if entry.is_dir() and (entry / "__init__.py").exists():
                paths.append(entry)

    for extra in ("scripts", "tests"):
        p = repo_root / extra
        if p.exists() and p not in paths:
            paths.append(p)

    return paths


DEFAULT_GOVERNANCE_FILES = [
    "docs/AI_CONSTITUTION.md",
    "docs/CONSTRAINTS_AND_PREFERENCES.md",
    "docs/COMPLIANCE_CHECK.md",
    "docs/ARCHITECTURE_DECISIONS.md",
    "docs/AI_FAILURE_PATTERNS.md",
    "docs/TEST_THEORY.md",
    "AGENTS.md",
]


def get_governance_files(repo_root: Path) -> list[str]:
    """Repo-root-relative paths of protected governance files -- editing
    one without 'GOVERNANCE-UPDATE' in the commit message is blocked.

    Real bug found 2026-09-06 (guardrail fit investigation): three
    separate hardcoded copies of this list existed --
    guard_governance.py (1 file), validate_commit_msg.py (8 files), and
    guardrail.config.Config.DEFAULTS (8 files) -- and none of them
    agreed. validate_commit_msg.py's own copy protected
    docs/ARCHITECTURE_CHECKLIST.md and docs/REMINDERS.md, neither of
    which exists in this repo (protecting nothing), while leaving
    docs/TEST_THEORY.md -- a real, existing, Law-18-critical file --
    completely unprotected. DEFAULT_GOVERNANCE_FILES above is the
    corrected list, verified against what actually exists on disk, not
    copied from either stale version. Configurable via
    `.guardrail.json`'s "governance_files" for a project that needs a
    different set; falls back to the corrected default otherwise.
    """
    guardrail_json = repo_root / ".guardrail.json"
    if guardrail_json.exists():
        try:
            cfg = json.loads(guardrail_json.read_text(encoding="utf-8"))
            configured = cfg.get("governance_files")
            # Real bug found (GitHub Copilot review, PR #15): `if configured:
            # return list(configured)` trusted ANY truthy JSON value -- a
            # string is truthy and iterable, so `"docs/x.md"` would silently
            # become `["d", "o", "c", "s", ...]` instead of a config error.
            # Fail safe to the default instead of trusting the shape.
            if (isinstance(configured, list) and configured
                    and all(isinstance(f, str) for f in configured)):
                return list(configured)
        except (OSError, ValueError):
            pass
    return list(DEFAULT_GOVERNANCE_FILES)


DEFAULT_REGENERABLE_SUFFIXES = [
    ".stl", ".step", ".stp", ".obj", ".ply", ".3mf",
    ".json", ".jsonl", ".dat", ".log", ".txt",
    ".png", ".jpg", ".jpeg", ".svg",
]
DEFAULT_REGENERABLE_PATHS = ["test_output/", "designs/", "chat-logs/", "wiki/"]


def get_regenerable_suffixes(repo_root: Path) -> set[str]:
    """File suffixes treated as regenerable artifacts that should never
    be committed. Unlike governance_files, this one was already
    consistent between validate_pre_commit.py's hardcoded copy and
    Config.DEFAULTS (verified 2026-09-06, guardrail fit investigation) --
    no drift to fix, just genuinely wiring up the configurability both
    already claimed to offer via `.guardrail.json`. Falls back to
    DEFAULT_REGENERABLE_SUFFIXES if absent/malformed."""
    guardrail_json = repo_root / ".guardrail.json"
    if guardrail_json.exists():
        try:
            cfg = json.loads(guardrail_json.read_text(encoding="utf-8"))
            configured = cfg.get("regenerable_suffixes")
            if (isinstance(configured, list) and configured
                    and all(isinstance(s, str) for s in configured)):
                return set(configured)
        except (OSError, ValueError):
            pass
    return set(DEFAULT_REGENERABLE_SUFFIXES)


def get_regenerable_paths(repo_root: Path) -> set[str]:
    """Path prefixes whose contents are always treated as regenerable
    (see get_regenerable_suffixes' docstring for the same "already
    consistent, just not wired up" note). Falls back to
    DEFAULT_REGENERABLE_PATHS if absent/malformed."""
    guardrail_json = repo_root / ".guardrail.json"
    if guardrail_json.exists():
        try:
            cfg = json.loads(guardrail_json.read_text(encoding="utf-8"))
            configured = cfg.get("regenerable_paths")
            if (isinstance(configured, list) and configured
                    and all(isinstance(p, str) for p in configured)):
                return set(configured)
        except (OSError, ValueError):
            pass
    return set(DEFAULT_REGENERABLE_PATHS)


# Real bug found 2026-09-06 (guardrail fit investigation): unlike
# regenerable_suffixes/paths above, this one WAS drifted --
# Config.DEFAULTS["placement_rules"] used a simpler shape (prefix ->
# set of allowed extensions, no message) than validate_pre_commit.py's
# own PLACEMENT_RULES (prefix -> {"allowed": ..., "message": ...}), AND
# was missing the "src/" entry entirely -- so lawkeeper's own src/
# layout had no placement rule in Config's version, only in
# validate_pre_commit.py's separate hardcoded copy. This is the real,
# richer shape (with messages); Config.DEFAULTS was corrected to add
# "src/" and use the same simple extension-list shape a project would
# actually write in `.guardrail.json` (get_placement_rules below expands
# a configured extension list into this richer shape automatically).
DEFAULT_PLACEMENT_RULES = {
    "backend/": {
        "allowed": {".py"},
        "message": "backend/ root must contain ONLY core source modules (.py)",
    },
    "src/": {
        "allowed": {".py"},
        "message": "src/ root must contain ONLY package source modules (.py)",
    },
    "tests/": {
        "allowed": {".py"},
        "message": "tests/ must contain ONLY test files (.py)",
    },
    "scripts/": {
        "allowed": {".py", ".ps1", ".sh", ".bat"},
        "message": "scripts/ must contain ONLY utility/debug/benchmark scripts",
    },
    "docs/": {
        "allowed": {".md", ".txt", ".docx", ".pdf"},
        "message": "docs/ must contain ONLY documentation",
    },
}


def get_placement_rules(repo_root: Path) -> dict:
    """Path-prefix -> {"allowed": set of extensions, "message": str}
    placement rules, enforced by validate_pre_commit.py's check_placement().

    `.guardrail.json`'s "placement_rules" uses a simpler shape than this
    function's return value -- a plain {prefix: [".ext", ...]} mapping,
    matching what a project would actually want to write (no message
    authoring required). A configured prefix gets an auto-generated
    message; falls back to DEFAULT_PLACEMENT_RULES (with its existing,
    specific messages) entirely if unconfigured or malformed -- a partial
    override isn't supported, same all-or-nothing fallback philosophy as
    get_governance_files() etc.
    """
    guardrail_json = repo_root / ".guardrail.json"
    if guardrail_json.exists():
        try:
            cfg = json.loads(guardrail_json.read_text(encoding="utf-8"))
            configured = cfg.get("placement_rules")
            if isinstance(configured, dict) and configured:
                rules = {}
                for prefix, exts in configured.items():
                    if not (isinstance(prefix, str) and isinstance(exts, list)
                            and exts and all(isinstance(e, str) for e in exts)):
                        rules = None
                        break
                    rules[prefix] = {
                        "allowed": set(exts),
                        "message": f"{prefix} must contain ONLY {', '.join(sorted(exts))} files",
                    }
                if rules:
                    return rules
        except (OSError, ValueError):
            pass
    return {k: {"allowed": set(v["allowed"]), "message": v["message"]}
            for k, v in DEFAULT_PLACEMENT_RULES.items()}


def get_oversized_allowlist(repo_root: Path) -> set[str]:
    """Files allowed to exceed the module-size check without failing.

    Was hardcoded to a list of Windwright ('backend/', 'woodwind_designer/')
    file paths that can never match anything under this repo's own scan
    paths - a dead allowlist protecting nothing. Configurable via
    `.guardrail.json`'s "oversized_allowlist" (repo-root-relative paths);
    empty by default.
    """
    guardrail_json = repo_root / ".guardrail.json"
    if guardrail_json.exists():
        try:
            cfg = json.loads(guardrail_json.read_text(encoding="utf-8"))
            return set(cfg.get("oversized_allowlist", []))
        except (OSError, ValueError):
            pass
    return set()
