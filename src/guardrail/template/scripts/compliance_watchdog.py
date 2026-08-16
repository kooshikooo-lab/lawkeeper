#!/usr/bin/env python3
"""
AI Boot Sequence Compliance Watchdog.

Reads CONSTRAINTS_AND_PREFERENCES.md, AI_CONSTITUTION.md, COMPLIANCE_CHECK.md,
and ARCHITECTURE_CHECKLIST.md, then runs automated compliance checks at
configurable intervals.

Usage:
    python scripts/compliance_watchdog.py                    # 15-min cycle
    python scripts/compliance_watchdog.py --interval 5       # 5-min cycle
    python scripts/compliance_watchdog.py --once             # single run
    python scripts/compliance_watchdog.py --check-before path/to/file.py
"""

import argparse
import ast
import os
import re
import sys
import time
import json
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

try:
    from scan_config import get_oversized_allowlist, get_scan_paths  # normal `python scripts/x.py` run
except ImportError:
    # Same fallback pattern as guard_branch.py's load_config(): a plain
    # sibling import only works when Python itself put scripts/ on
    # sys.path (running the file directly). tests/test_guard_scripts.py
    # loads this module via importlib.util.spec_from_file_location
    # instead, which does not - insert the directory explicitly.
    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    from scan_config import get_oversized_allowlist, get_scan_paths
DOCS_DIR = REPO_ROOT / "docs"
SCRIPTS_DIR = REPO_ROOT / "scripts"
COMPLIANCE_LOG = SCRIPTS_DIR / "compliance_log.jsonl"
BASELINE_FILE = SCRIPTS_DIR / "compliance_baseline.json"


def load_guardrail_config():
    """Project config written by `lawkeeper init`. Optional; safe to be absent."""
    path = REPO_ROOT / ".guardrail.json"
    try:
        import json
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        pass
    return {}

EXCLUDED_DIRS = [
    "__pycache__",
    ".git",
    "node_modules",
    "web",
]

EXCLUDED_FILES = [
    "__init__.py",
]

# ── Boot sequence knowledge ─────────────────────────────────────────

CONSTITUTION_FILE = DOCS_DIR / "AI_CONSTITUTION.md"


def load_constitution_laws() -> list[str]:
    """Load law titles from AI_CONSTITUTION.md (single source of truth).

    Falls back to the known law list only if the file is missing, so a stale
    hardcoded list can never silently diverge from the constitution (Law 7).
    """
    if CONSTITUTION_FILE.exists():
        try:
            text = CONSTITUTION_FILE.read_text(encoding="utf-8")
        except OSError:
            text = ""
        laws = re.findall(r"^###\s+(Law \d+[^\n]*)", text, re.MULTILINE)
        if laws:
            return laws
        # File exists but no laws parsed: a real defect. A dead guard must fail
        # loudly, never silently fall back to a stale list (Law 16.4).
        raise RuntimeError(
            "AI_CONSTITUTION.md exists but no '### Law N' headings were found — "
            "the law loader cannot verify the constitution. Fix the parser or "
            "the file; do not trust the hardcoded fallback list."
        )
    # Only when the constitution file is genuinely absent do we fall back.
    return [
        "Law 1 - Architecture over features",
        "Law 2 - No architectural invention",
        "Law 3 - Never duplicate code",
        "Law 4 - Geometry is separate from acoustics",
        "Law 5 - Optimization chooses variables, physics computes results",
        "Law 6 - The GUI never contains physics",
        "Law 7 - One source of truth for every physical quantity",
        "Law 8 - One responsibility per module",
        "Law 9 - Document architectural decisions",
        "Law 10 - When uncertain, stop and ask",
        "Law 11 - Mandatory multi-machine communication protocol",
        "Law 12 - Mandatory GitHub reading protocol",
        "Law 13 - Missing dependencies are bugs",
        "Law 14 - Audit before you commit",
    ]


def load_architecture_docs() -> list[str]:
    """Architecture doc names required by the project (Law 9).

    Defaults to none (generic projects). A project may declare them in
    `.guardrail.json` as `required_architecture_docs: ["..."]`.
    """
    cfg = load_guardrail_config()
    return list(cfg.get("required_architecture_docs", []))

SUBSYSTEM_TABLE = {
    "Geometry": ["geometry.py", "spline_bore.py"],
    "Acoustic solver": ["tmm_acoustics.py", "tmm_acoustics_jax.py"],
    "Optimization": ["pareto_optimizer.py", "jax_optimizer.py"],
    "Sound analysis": ["sound_analysis.py"],
    "Pipeline": ["design_from_wav.py", "design_from_unconventional.py", "design_pipeline.py"],
    "Generative agent": ["generative_agent.py", "instrument_knowledge.py"],
    "CAD/Manufacturing": ["cadquery_export.py"],
    "GUI": ["woodwind_designer/", "web/"],
    "Tests": ["tests/"],
}

TRIGGER_TYPES = ["timer", "before-code", "after-tests", "drift-feel"]


# ── Automated checks ────────────────────────────────────────────────


def find_python_files():
    files = []
    for d in get_scan_paths(REPO_ROOT):
        if not d.exists():
            continue
        for root, dirs, names in os.walk(d):
            dirs[:] = [x for x in dirs if x not in EXCLUDED_DIRS]
            for name in names:
                if name.endswith(".py") and name not in EXCLUDED_FILES:
                    files.append(Path(root) / name)
    return sorted(files)


def check_bare_excepts(path: Path) -> list[int]:
    with open(path, encoding="utf-8", errors="replace") as f:
        tree = ast.parse(f.read())
    return [n.lineno for n in ast.walk(tree)
            if isinstance(n, ast.ExceptHandler) and n.type is None]


def check_module_mutables(path: Path) -> list[str]:
    with open(path, encoding="utf-8", errors="replace") as f:
        tree = ast.parse(f.read())
    issues = []
    for n in ast.iter_child_nodes(tree):
        if isinstance(n, ast.Assign):
            for t in n.targets:
                if isinstance(t, ast.Name) and not t.id.startswith("_"):
                    if isinstance(n.value, (ast.List, ast.Dict, ast.Set)):
                        issues.append(f"{t.id} L{n.lineno}")
    return issues


def check_hardcoded_ips(path: Path) -> list[str]:
    with open(path, encoding="utf-8", errors="ignore") as f:
        content = f.read()
    ips = re.findall(r"(?<!\d)\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(?!\d)", content)
    safe = {"0.0.0.0", "127.0.0.1", "255.255.255.255"}
    return [ip for ip in ips if ip not in safe]


def check_module_size(path: Path) -> int | None:
    with open(path, encoding="utf-8", errors="replace") as f:
        lines = f.readlines()
    if len(lines) > 500:
        return len(lines)
    return None


def check_docstring_present(path: Path) -> bool:
    with open(path, encoding="utf-8", errors="replace") as f:
        tree = ast.parse(f.read())
    return isinstance(tree.body[0], ast.Expr) if tree.body else False


def check_no_dunder_assign(path: Path) -> list[str]:
    with open(path, encoding="utf-8", errors="replace") as f:
        tree = ast.parse(f.read())
    issues = []
    for n in ast.iter_child_nodes(tree):
        if isinstance(n, ast.Assign):
            for t in n.targets:
                if isinstance(t, ast.Name) and t.id.startswith("__") and t.id.endswith("__"):
                    pass
    return issues


# ── Baseline / regression support ───────────────────────────────────


def _as_tuple(value):
    if value is None:
        return ()
    if isinstance(value, (list, tuple)):
        flat = []
        for item in value:
            flat.extend(_as_tuple(item))
        return tuple(flat)
    return (value,)


def normalized_violations(results: dict) -> list[tuple]:
    """Reduce violations to (file, check, *items) so they compare across runs."""
    out = []
    for v in results.get("violations", []):
        items = _as_tuple(v.get("items") or v.get("lines") or v.get("ips"))
        out.append((v["file"], v["check"], items))
    return sorted(out)


def _deep_tuple(value):
    if isinstance(value, list):
        return tuple(_deep_tuple(v) for v in value)
    return value


def load_baseline() -> dict:
    if BASELINE_FILE.exists():
        try:
            data = json.loads(BASELINE_FILE.read_text(encoding="utf-8"))
            data["violations"] = [
                tuple(_deep_tuple(v)) for v in data.get("violations", [])
            ]
            return data
        except (OSError, json.JSONDecodeError):
            return {}
    return {}


def save_baseline(results: dict) -> dict:
    baseline = {"violations": normalized_violations(results)}
    BASELINE_FILE.write_text(json.dumps(baseline, indent=2) + "\n", encoding="utf-8")
    return baseline


def run_regression() -> tuple[bool, list, dict]:
    """Compare current violations against the committed baseline.

    Returns (passed, new_violations, current_baseline). Pre-existing debt does
    not fail the check — only violations absent from the baseline do.
    """
    results = run_checks(trigger="regression")
    baseline = load_baseline()
    current = normalized_violations(results)
    known = set(baseline.get("violations", []))
    new = [v for v in current if v not in known]
    passed = not new
    return passed, new, results


# ── Runner ──────────────────────────────────────────────────────────


def run_checks(subsystem: str | None = None, trigger: str = "timer") -> dict:
    results = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "trigger": trigger,
        "subsystem": subsystem or "all",
        "checks": {},
        "violations": [],
        "passed": True,
    }

    files = find_python_files()
    oversized_allowlist = get_oversized_allowlist(REPO_ROOT)

    bare_excepts_total = 0
    mutable_total = 0
    ip_total = 0
    oversized_modules = []

    for f in files:
        rel = f.relative_to(REPO_ROOT)
        try:
            bare = check_bare_excepts(f)
            if bare:
                results["violations"].append({
                    "file": str(rel),
                    "check": "bare_except",
                    "lines": bare,
                })
                bare_excepts_total += len(bare)
        except SyntaxError:
            pass

        try:
            mutables = check_module_mutables(f)
            if mutables:
                results["violations"].append({
                    "file": str(rel),
                    "check": "module_mutable",
                    "items": mutables,
                })
                mutable_total += len(mutables)
        except SyntaxError:
            pass

        try:
            ips = check_hardcoded_ips(f)
            if ips:
                results["violations"].append({
                    "file": str(rel),
                    "check": "hardcoded_ip",
                    "ips": ips,
                })
                ip_total += len(ips)
        except SyntaxError:
            pass

        try:
            rel_str = str(rel)
            size = check_module_size(f)
            if size and rel_str not in oversized_allowlist:
                oversized_modules.append({"file": rel_str, "lines": size})
                results["violations"].append({
                    "file": rel_str,
                    "check": "module_size",
                    "lines": size,
                })
        except SyntaxError:
            pass

    results["checks"] = {
        "files_scanned": len(files),
        "bare_excepts": bare_excepts_total,
        "module_mutables": mutable_total,
        "hardcoded_ips": ip_total,
        "oversized_modules": len(oversized_modules),
        "oversized_list": oversized_modules,
    }

    results["passed"] = (
        bare_excepts_total == 0
        and ip_total == 0
    )

    return results


def print_results(results: dict):
    ts = results["timestamp"][:19]
    trigger = results["trigger"]
    status = "PASS" if results["passed"] else "FAIL"
    c = results["checks"]
    print(f"[{ts}] COMPLIANCE: {status} | trigger: {trigger}")
    print(f"       files: {c['files_scanned']} | bare excepts: {c['bare_excepts']} | "
          f"mutables: {c['module_mutables']} | IPs: {c['hardcoded_ips']} | "
          f"oversized: {c['oversized_modules']}")
    for v in results["violations"]:
        print(f"       VIOLATION: {v['file']} | {v['check']}")


def log_results(results: dict):
    COMPLIANCE_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(COMPLIANCE_LOG, "a") as f:
        f.write(json.dumps(results) + "\n")


def print_boot_sequence():
    laws = load_constitution_laws()
    print("=" * 60)
    print("AI BOOT SEQUENCE")
    print("=" * 60)
    print()
    print("Step 1 - Read the AI Constitution:")
    for law in laws:
        print(f"   {law}")
    print()
    print("Step 2 - Read architecture docs:")
    for d in load_architecture_docs():
        p = DOCS_DIR / d
        status = "EXISTS" if p.exists() else "MISSING"
        print(f"   {d} [{status}]")
    print()
    print("Step 3 - Identify your subsystem:")
    for sub, files in SUBSYSTEM_TABLE.items():
        print(f"   {sub}: {', '.join(files)}")
    print()
    print("Step 4 - Search before building")
    print("Step 5 - Produce an implementation plan")
    print("Step 6 - Implement (run compliance every 15 min)")
    print()
    print("FINAL CHECK before finishing:")
    print("   All tests pass | No duplicated code")
    print("   Architecture preserved | ARCHITECTURE_CHECKLIST.md complete")
    print("   COMPLIANCE_CHECK.md run | Failures logged in AI_FAILURE_PATTERNS.md")
    print("=" * 60)


# ── Pre-file-modification hook ──────────────────────────────────────


def check_before_modify(filepath: str) -> bool:
    path = Path(filepath)
    if not path.exists():
        return True
    print(f"[before-code] Checking {filepath}...")
    results = run_checks(trigger="before-code")
    print_results(results)
    log_results(results)
    if not results["passed"]:
        print(f"[before-code] FAILED - fix violations before modifying {filepath}")
        return False
    return True


# ── Main ────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(
        description="AI Boot Sequence Compliance Watchdog"
    )
    parser.add_argument("--interval", "-i", type=int, default=15,
                        help="Check interval in minutes (default: 15)")
    parser.add_argument("--once", action="store_true",
                        help="Run a single check and exit")
    parser.add_argument("--boot", action="store_true",
                        help="Print boot sequence and exit")
    parser.add_argument("--check-before", type=str, metavar="FILE",
                        help="Run compliance check before modifying a file")
    parser.add_argument("--subsystem", "-s", type=str, default=None,
                        help="Limit checks to a specific subsystem")
    parser.add_argument("--baseline", action="store_true",
                        help="Snapshot current violations as the baseline and exit")
    parser.add_argument("--check-baseline", action="store_true",
                        help="Fail only if NEW violations appear vs the baseline")
    parser.add_argument("--check-laws", action="store_true",
                        help="Verify the watchdog's law list matches AI_CONSTITUTION.md")
    args = parser.parse_args()

    if args.check_laws:
        laws = load_constitution_laws()
        print("CONSTITUTION LAWS (from AI_CONSTITUTION.md):")
        for law in laws:
            print(f"   {law}")
        missing = [d for d in load_architecture_docs()
                   if not (DOCS_DIR / d).exists()]
        if missing:
            print(f"MISSING architecture docs: {', '.join(missing)}", file=sys.stderr)
            sys.exit(1)
        if not laws:
            print("ERROR: no laws found in AI_CONSTITUTION.md", file=sys.stderr)
            sys.exit(1)
        print("OK: constitution laws loaded, architecture docs present.")
        sys.exit(0)

    if args.check_baseline:
        passed, new, results = run_regression()
        print_results(results)
        if new:
            print("NEW VIOLATIONS vs baseline (blocking):", file=sys.stderr)
            for v in new:
                print(f"   {v[0]} | {v[1]} | {v[2]}", file=sys.stderr)
            sys.exit(1)
        print("OK: no new violations vs baseline.")
        sys.exit(0)

    if args.baseline:
        results = run_checks(trigger="baseline")
        baseline = save_baseline(results)
        print_results(results)
        print(f"BASELINE saved: {len(baseline['violations'])} known violations.")
        sys.exit(0)

    if args.boot:
        print_boot_sequence()
        return

    if args.check_before:
        ok = check_before_modify(args.check_before)
        sys.exit(0 if ok else 1)

    if args.once:
        results = run_checks(subsystem=args.subsystem, trigger="manual")
        print_results(results)
        log_results(results)
        sys.exit(0 if results["passed"] else 1)

    print(f"[watchdog] Starting compliance watchdog (interval={args.interval}min)")
    print(f"[watchdog] Log: {COMPLIANCE_LOG}")
    print()
    print_boot_sequence()
    print()

    cycle = 0
    while True:
        cycle += 1
        trigger = "timer"
        results = run_checks(subsystem=args.subsystem, trigger=trigger)
        results["cycle"] = cycle
        print_results(results)
        log_results(results)

        if not results["passed"]:
            print(f"[watchdog] VIOLATIONS DETECTED in cycle {cycle}")
        else:
            print(f"[watchdog] All clean, next check in {args.interval}min")

        print()
        time.sleep(args.interval * 60)


if __name__ == "__main__":
    main()
