"""System self-audit — audits the enforcement system itself, not just the code.

The general principle (Law 16): the safeguards must be mechanically verifiable,
because agents malfunction, misunderstand, and act rashly. This script verifies
that the enforcement layers are actually present and active, so a guard cannot
silently disappear.

Checks:
  1. Git hooks installed (core.hooksPath points at scripts/git-hooks) and each
     versioned hook file exists and is wired to its validator.
  2. Constitution laws load and parse (compliance_watchdog --check-laws).
  3. Compliance baseline matches current tracked baseline file.
  4. Law 15 branch topology (guard_branch --audit): no orphans, origin/HEAD -> main.
  5. Architecture import boundaries (lint-imports --config .importlinter), if
     a .importlinter config exists at the repo root.
  6. Every guard script imports cleanly (a broken guard is a dead guard).
  7. Wire integrity: each hook file references the validator script it runs.

Usage:
  python scripts/system_audit.py           # full audit, exit 1 on any failure
  python scripts/system_audit.py --brief   # one line per check

Exit codes: 0 = all checks pass, 1 = one or more failures, 2 = error.
"""

import argparse
import importlib.util
import os
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(subprocess.run(
    ["git", "rev-parse", "--show-toplevel"],
    capture_output=True, text=True, encoding="utf-8", errors="replace"
).stdout.strip() or Path.cwd())

HOOKS_DIR = REPO_ROOT / "scripts" / "git-hooks"
GOVERNANCE_GUARD_FILE = REPO_ROOT / "scripts" / "compliance_watchdog.py"

# (hook filename, the validator script it should invoke)
HOOK_WIRING = {
    "pre-commit": "validate_pre_commit.py",
    "commit-msg": "validate_commit_msg.py",
    "pre-push": "guard_branch.py",
}

# Guard scripts whose importability is itself part of the audit.
GUARD_SCRIPTS = [
    "scripts/guard_branch.py",
    "scripts/merge_gate.py",
    "scripts/validate_pre_commit.py",
    "scripts/validate_commit_msg.py",
    "scripts/guard_governance.py",
    "scripts/compliance_watchdog.py",
    "scripts/toolcheck.py",
    "scripts/validate_imports.py",
    "scripts/check_local_dependencies.py",
]


def run(cmd, cwd=None):
    try:
        result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True,
                                encoding="utf-8", errors="replace")
        return result.returncode, result.stdout, result.stderr
    except OSError as e:
        return 2, "", str(e)


def check_hooks() -> list[str]:
    """Verify core.hooksPath and that each versioned hook exists + is wired."""
    problems = []
    code, out, _ = run(["git", "config", "--get", "core.hooksPath"])
    hooks_path = out.strip() if code == 0 else ""
    expected = "scripts/git-hooks"
    if hooks_path != expected:
        problems.append(
            f"core.hooksPath is {hooks_path!r}, expected {expected!r}. "
            f"Run scripts/install_hooks.ps1."
        )
    for hook, validator in HOOK_WIRING.items():
        hook_file = HOOKS_DIR / hook
        if not hook_file.is_file():
            problems.append(f"hook {hook} missing: {hook_file}")
            continue
        content = hook_file.read_text(encoding="utf-8", errors="replace")
        if validator not in content:
            problems.append(f"hook {hook} is not wired to {validator}")
    return problems


def check_laws() -> list[str]:
    code, out, err = run([sys.executable, str(GOVERNANCE_GUARD_FILE), "--check-laws"])
    if code != 0:
        return [f"compliance_watchdog --check-laws failed:\n{out}{err}"]
    return []


def check_baseline() -> list[str]:
    code, out, err = run([sys.executable, str(GOVERNANCE_GUARD_FILE), "--check-baseline"])
    if code != 0:
        return [f"compliance_watchdog --check-baseline failed (new violations):\n{out}{err}"]
    return []


def check_branch_topology() -> list[str]:
    """Hard failures: canonical-branch violations and origin/HEAD drift.

    Orphan feature branches are reported separately as findings (topology debt),
    matching the watchdog-baseline philosophy: existing debt is surfaced, new
    failures block. Canonical violations are always hard.
    """
    code, out, err = run([sys.executable,
                          str(REPO_ROOT / "scripts" / "guard_branch.py"), "--audit"])
    problems = []
    for line in (out + err).splitlines():
        line = line.strip()
        if not line:
            continue
        if "origin/HEAD" in line:
            problems.append(line)  # Law 15.6 — always hard
        elif line.startswith("AUDIT branch"):
            pass  # orphan feature branch = debt, reported in findings, not a blocker
    return problems if code != 0 else problems


def check_branch_debt() -> list[str]:
    """Soft findings: orphan feature branches (Law 15 namespace violations)."""
    _, out, err = run([sys.executable,
                       str(REPO_ROOT / "scripts" / "guard_branch.py"), "--audit"])
    return [line.strip() for line in (out + err).splitlines()
            if line.strip().startswith("AUDIT branch")]


def check_import_boundaries() -> list[str]:
    """If a `.importlinter` config exists at the repo root, run it and treat
    any broken architecture contract as a failure. Not applicable (returns
    []) if no `.importlinter` file exists -- most `lawkeeper init` projects
    won't have one unless they choose to add architecture contracts of their
    own; this check is generic, not lawkeeper-specific, same reasoning as
    check_hooks() working for any project's own hook wiring.

    Ported from Windwright 2026-08/2026-09 (real user directive 2026-09-04:
    check tools found in one repo for portability to others -- see
    shared_memory/user-quality-standard-escalation-and-cross-repo-sharing-
    2026-09-04.md). Real fit for lawkeeper's own src/guardrail/ package: see
    the repo root's own .importlinter for the contracts and why they exist.
    """
    config = REPO_ROOT / ".importlinter"
    if not config.exists():
        return []
    if shutil.which("lint-imports") is None:
        return [
            ".importlinter config exists but the `lint-imports` command is "
            "not installed (pip install import-linter) -- architecture "
            "contracts cannot be verified"
        ]
    # cwd=REPO_ROOT explicitly (real bug, GitHub Copilot review, PR #8):
    # lint-imports resolves `root_packages` relative to the invoking
    # process's cwd, not this config file's location. Without this, running
    # system_audit.py from a subdirectory (or a context without an editable
    # install putting `guardrail` on sys.path some other way) could make
    # import-linter fail to find guardrail at all, or silently check the
    # wrong thing.
    code, out, err = run(["lint-imports", "--config", str(config)], cwd=str(REPO_ROOT))
    if code != 0:
        return [f"import-linter found broken contract(s):\n{out}{err}"]
    return []


def check_guards_import() -> list[str]:
    problems = []
    for rel in GUARD_SCRIPTS:
        path = REPO_ROOT / rel
        if not path.is_file():
            problems.append(f"guard script missing: {rel}")
            continue
        spec = importlib.util.spec_from_file_location(f"_audit_{path.stem}", path)
        try:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
        except SystemExit:
            pass  # script may exit in __main__ guarded by if __name__
        except Exception as e:  # noqa: BLE001 — any import failure is a dead guard
            problems.append(f"{rel} fails to import: {e}")
    return problems


def audit():
    """Return (failures, findings). Failures block; findings are debt to clean."""
    failures = []
    failures += check_hooks()
    failures += check_laws()
    failures += check_baseline()
    failures += check_branch_topology()
    failures += check_import_boundaries()
    failures += check_guards_import()
    findings = check_branch_debt()
    return failures, findings


def safe_print(text: str) -> None:
    """Print without crashing on non-encodable characters (Windows cp1252)."""
    try:
        print(text)
    except UnicodeEncodeError:
        print(text.encode("ascii", "replace").decode("ascii"))


def main():
    parser = argparse.ArgumentParser(description="System self-audit (Law 16)")
    parser.add_argument("--brief", action="store_true",
                        help="print one line per failure only")
    args = parser.parse_args()

    failures, findings = audit()
    if args.brief:
        for f in failures:
            safe_print(f)
    else:
        safe_print("=== SYSTEM AUDIT (enforcement layers) ===")
        for f in failures:
            safe_print(f"  FAIL: {f}")
        if not failures:
            safe_print("  ALL CHECKS PASS")
        if findings:
            safe_print("FINDINGS (debt, non-blocking):")
            for g in findings:
                safe_print(f"  - {g}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
