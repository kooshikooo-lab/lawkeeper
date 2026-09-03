"""Pre-commit validation helpers.

Checks staged files for:
  - regenerable artifacts (STL, JSON dumps, logs, test_output/)
  - UTF-16 encoded text files
  - file placement violations (source/tests/scripts/docs boundaries)
  - Python basics for staged .py files (bare excepts, hardcoded IPs, oversized modules)

Used by the pre-commit hook in scripts/git-hooks/pre-commit.
"""

import ast
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

try:
    from scan_config import get_oversized_allowlist  # normal `python scripts/x.py` run
except ImportError:
    # Same fallback as compliance_watchdog.py/toolcheck.py: a plain sibling
    # import only works when Python itself put scripts/ on sys.path (running
    # the file directly). tests/test_guard_scripts.py loads this module via
    # importlib.util.spec_from_file_location instead, which does not.
    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    from scan_config import get_oversized_allowlist

# These are generic project boundaries; a project's own docs/ARCHITECTURE.md
# (if it has one) may describe more. Configurable per project via
# .guardrail.json's "placement_rules" - see config.py's DEFAULTS.
PLACEMENT_RULES = {
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

# Whole subtrees exempted from PLACEMENT_RULES above (unlike
# PLACEMENT_ALLOWLIST below, which exempts individual files). Needed because
# this project's own src/guardrail/template/ is a deliberate multi-format
# project scaffold (docs, YAML, shell hooks with no extension, ...) nested
# under src/ - not a stray non-.py file that src/'s ".py only" rule above is
# meant to catch. Any other project adopting lawkeeper that nests its own
# template/scaffold directory under src/ has the same legitimate need.
PLACEMENT_TREE_ALLOWLIST = {
    "src/guardrail/template/",
}

# Regenerable artifacts that should never be committed.
REGENERABLE_SUFFIXES = {
    ".stl", ".step", ".stp", ".obj", ".ply", ".3mf",
    ".json", ".jsonl", ".dat", ".log", ".txt",
    ".png", ".jpg", ".jpeg", ".svg",
}
REGENERABLE_PATHS = {"test_output/", "designs/", "chat-logs/", "wiki/"}


def staged_files():
    """Return list of staged file paths (relative to repo root)."""
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR"],
        capture_output=True, text=True, encoding="utf-8", errors="replace"
    )
    if result.returncode != 0:
        return []
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def is_binary(path: Path) -> bool:
    """Cheap binary check: read first 8KB and look for null bytes."""
    try:
        with open(path, "rb") as f:
            chunk = f.read(8192)
        return b"\x00" in chunk
    except OSError:
        return True


def check_utf16(path: Path) -> bool:
    """Detect UTF-16 by BOM."""
    try:
        with open(path, "rb") as f:
            bom = f.read(2)
        return bom in (b"\xff\xfe", b"\xfe\xff")
    except OSError:
        return False


def check_regenerable(path: str) -> str | None:
    """Return violation message if path is a regenerable artifact."""
    low = path.lower()
    for suffix in REGENERABLE_SUFFIXES:
        if low.endswith(suffix):
            # JSON logs/reports under test_output/ or designs/ are always regenerable.
            for prefix in REGENERABLE_PATHS:
                if path.startswith(prefix):
                    return f"{path}: regenerable artifact in {prefix} (do not commit)"
            # JSON config files in config/ or specific machine-config files are allowed.
            if path.startswith("config/") and suffix == ".json":
                return None
            if path == "scripts/.tailscale_config.json":
                return None
            # Pinned pip-tools lock files are required to be committed.
            if suffix == ".txt" and re.match(r"^requirements(-\w+)?\.txt$", path):
                return None
            if suffix in {".log", ".txt", ".jsonl"}:
                return f"{path}: log/dump file should not be committed"
    return None


# Specific files that are allowed despite their directory's normal placement rules.
PLACEMENT_ALLOWLIST = {
    "scripts/.tailscale_config.json",
    # Versioned compliance-baseline snapshot (Law 14 watchdog regression gate).
    "scripts/compliance_baseline.json",
}


def check_placement(path: str) -> str | None:
    """Detect violation if path violates directory placement rules."""
    if path in PLACEMENT_ALLOWLIST:
        return None
    if any(path.startswith(tree) for tree in PLACEMENT_TREE_ALLOWLIST):
        return None
    for prefix, rule in PLACEMENT_RULES.items():
        if path.startswith(prefix):
            suffix = Path(path).suffix.lower()
            if suffix and suffix not in rule["allowed"]:
                return f"{path}: {rule['message']}"
    return None



def check_bare_excepts(path: Path) -> list[int]:
    """Return line numbers of bare except handlers in a Python file."""
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            tree = ast.parse(f.read())
    except SyntaxError:
        return []
    return [
        node.lineno for node in ast.walk(tree)
        if isinstance(node, ast.ExceptHandler) and node.type is None
    ]


def _is_tailscale_ip(ip: str) -> bool:
    """Tailscale addresses are in the CGNAT range 100.64.0.0/10."""
    try:
        octets = [int(o) for o in ip.split(".")]
    except ValueError:
        return False
    return len(octets) == 4 and octets[0] == 100 and 64 <= octets[1] <= 127


def check_hardcoded_ips(path: Path) -> list[str]:
    """Return list of hardcoded non-loopback, non-Tailscale IPs."""
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
    except OSError:
        return []
    ips = re.findall(r"(?<!\d)\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(?!\d)", content)
    safe = {"0.0.0.0", "127.0.0.1", "255.255.255.255"}
    return [ip for ip in ips if ip not in safe and not _is_tailscale_ip(ip)]


# Hardcoded speed-of-sound literals outside the canonical source are a common
# source of cross-branch bugs (Law 7: canonical SPEED_OF_SOUND = 346100.0 mm/s).
SPEED_OF_SOUND_LITERAL_RE = re.compile(
    r"(?<![\w.])"
    r"(?:331\.3|343\.42|344\.844|345\.844|346\.1|"
    r"343000(?:\.0*)?|346100(?:\.0*)?)"
    r"(?![\w.])"
)
SPEED_OF_SOUND_CANONICAL_FILE = "backend/tmm_acoustics.py"


def check_hardcoded_speed_of_sound(path: Path, root: Path) -> list[str]:
    """Flag hardcoded speed-of-sound literals outside the canonical module."""
    rel = path.relative_to(root).as_posix()
    # Exempt the canonical physics module and any copy of this validator itself
    # (root + template copies both carry the regex's literal substrings).
    if rel == SPEED_OF_SOUND_CANONICAL_FILE or Path(rel).name == "validate_pre_commit.py":
        return []
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
    except OSError:
        return []
    matches = []
    for m in SPEED_OF_SOUND_LITERAL_RE.finditer(content):
        line = content[:m.start()].count("\n") + 1
        matches.append(f"{rel}:{line}: hardcoded speed-of-sound literal '{m.group()}'")
    return matches


def check_module_size(path: Path, root: Path) -> str | None:
    """Return warning message if .py file exceeds ~500 lines and is not allowlisted.

    The allowlist comes from .guardrail.json's "oversized_allowlist"
    (scan_config.get_oversized_allowlist) - project-specific known debt,
    not a hardcoded list. Used to hardcode 13 backend/woodwind_designer
    paths inherited from the project this repo was extracted from, none of
    which exist here; the one real entry this repo needs
    (scripts/compliance_watchdog.py) now lives in this repo's own
    .guardrail.json, the same place any other project would configure it.
    """
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            lines = len(f.readlines())
    except OSError:
        return None
    if lines <= 500:
        return None
    rel = path.relative_to(root).as_posix()
    if rel in get_oversized_allowlist(root):
        return None
    return f"{rel}: {lines} lines (exceeds 500; add to .guardrail.json's oversized_allowlist or split)"


def find_rust_checker() -> str | None:
    """Locate the lawkeeper-checker binary, if available.

    Checked in order: LAWKEEPER_CHECKER_BIN env var (explicit override),
    then PATH. Returns None — not an error — if not found, since most
    Lawkeeper users won't have Rust installed or this prototype built.
    A missing optional tool must never break the commit hook for everyone
    else; that's the same "fail loud only when it's actually broken, not
    just absent" principle applied to `lawkeeper init`'s template check.
    """
    override = os.environ.get("LAWKEEPER_CHECKER_BIN")
    if override and Path(override).is_file():
        return override
    return shutil.which("lawkeeper-checker")


def check_rust_files(rust_files: list[str], repo_root: Path) -> list[str]:
    """Run the Rust syntax checker on staged .rs files, if it's available.

    Returns violation lines to add to the blocking error list. Returns an
    empty list (never blocks) if the checker binary isn't found — this is
    an optional additional enforcement layer, not a hard requirement, since
    it's a separate prototype tool most Lawkeeper installs won't have.
    """
    checker = find_rust_checker()
    if checker is None:
        print(
            "  (note: lawkeeper-checker not found — skipping edit-time Rust "
            "syntax checks; install it and set LAWKEEPER_CHECKER_BIN or add "
            "it to PATH to enable this layer)"
        )
        return []
    violations = []
    for rel in rust_files:
        result = subprocess.run(
            [checker, str(repo_root / rel)],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
        )
        if result.returncode != 0:
            for line in result.stdout.splitlines():
                if line.strip() and not line.startswith("lawkeeper-checker:"):
                    violations.append(f"[rust] {line}")
    return violations


def main():
    repo_root = Path(subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True, text=True, encoding="utf-8", errors="replace"
    ).stdout.strip())

    files = staged_files()
    if not files:
        print("No staged files to validate.")
        return 0

    errors = []
    warnings = []
    for rel in files:
        path = repo_root / rel
        if not path.is_file():
            continue

        # 1. Regenerable artifacts
        msg = check_regenerable(rel)
        if msg:
            errors.append(msg)

        # 2. UTF-16
        if check_utf16(path):
            errors.append(f"{rel}: UTF-16 encoding detected — save as UTF-8")

        # 3. Placement
        msg = check_placement(rel)
        if msg:
            errors.append(msg)

        # 4. Python-specific checks
        if rel.endswith(".py"):
            bare = check_bare_excepts(path)
            for line in bare:
                errors.append(f"{rel}:{line}: bare except clause")

            ips = check_hardcoded_ips(path)
            if ips:
                errors.append(f"{rel}: hardcoded IP(s) {', '.join(set(ips))}")

            size_msg = check_module_size(path, repo_root)
            if size_msg:
                warnings.append(size_msg)

            sos = check_hardcoded_speed_of_sound(path, repo_root)
            errors.extend(sos)

    # 5. Schema validation for instrument configs
    if any(rel.startswith("config/") and rel.endswith(".json") for rel in files):
        result = subprocess.run(
            [sys.executable, str(repo_root / "scripts" / "validate_instrument_configs.py")],
            capture_output=True, text=True, encoding="utf-8", errors="replace"
        )
        if result.returncode != 0:
            errors.append("config/*.json schema validation failed")
            for line in result.stdout.splitlines() + result.stderr.splitlines():
                errors.append(f"  {line}")

    # 6. Import consistency for staged Python files
    if any(rel.endswith(".py") for rel in files):
        result = subprocess.run(
            [sys.executable, str(repo_root / "scripts" / "validate_imports.py")],
            capture_output=True, text=True, encoding="utf-8", errors="replace"
        )
        if result.returncode != 0:
            errors.append("Python import consistency check failed")
            for line in result.stdout.splitlines() + result.stderr.splitlines():
                errors.append(f"  {line}")

    # 7. PowerShell 5.1 compatibility for staged PowerShell files
    ps1_files = [rel for rel in files if rel.endswith(".ps1")]
    if ps1_files:
        result = subprocess.run(
            [sys.executable, str(repo_root / "scripts" / "check_powershell_51_compat.py")]
            + [str(repo_root / rel) for rel in ps1_files],
            capture_output=True, text=True, encoding="utf-8", errors="replace"
        )
        if result.returncode != 0:
            errors.append("PowerShell 5.1 compatibility check failed")
            for line in result.stdout.splitlines() + result.stderr.splitlines():
                errors.append(f"  {line}")

    # 8. Edit-time Rust syntax constitution (optional — see lawkeeper-checker)
    rust_files = [rel for rel in files if rel.endswith(".rs")]
    if rust_files:
        errors.extend(check_rust_files(rust_files, repo_root))

    if warnings:
        print("WARNINGS (non-blocking):")
        for w in warnings:
            print(f"  - {w}")
        print()

    if errors:
        print("BLOCKED — fix these before committing:")
        for e in errors:
            print(f"  - {e}")
        return 1

    print(f"Pre-commit validation passed for {len(files)} staged file(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
