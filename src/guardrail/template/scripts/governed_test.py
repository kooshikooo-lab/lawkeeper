"""Governed test runner — the enforcement layer for test governance.

An agent must NEVER invoke pytest directly. It runs tests through this wrapper,
which:

1. loads the test's machine-readable theory card (test_governance/cards/*.yaml),
2. REFUSES to run if the card is missing or malformed (missing card =
   infrastructure failure, not permission to proceed),
3. prints the theory / oracle / acceptance criterion BEFORE running,
4. runs pytest,
5. classifies the result CRASH / RAN-BUT-FAILED / PASS,
6. assigns a trust level (T0-T5) from the card,
7. emits a structured report (JSON) so the agent cannot hand-wave a bare "pass".

Usage:
    python scripts/governed_test.py tests/test_analytical_pipes.py
    python scripts/governed_test.py tests/test_analytical_pipes.py --json
    python scripts/governed_test.py tests/test_analytical_pipes.py --mutate

``--mutate`` runs the discrimination check (T4): it asks the test's own card for a
deliberately-broken variant of the code and asserts the test FAILS against it. A
test that passes even with the known-broken variant has no discriminating power.

Trust levels (from the test-governance design):
    T0 smoke/execution only, T1 assertion exists, T2 independent oracle,
    T3 adversarially reviewed, T4 mutation/discrimination verified,
    T5 validated against independent physics/reference.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
CARDS_DIR = ROOT / "test_governance" / "cards"
sys.path.insert(0, str(ROOT))

REQUIRED_FIELDS = ("test_id", "theory", "oracle", "acceptance", "blind_spot", "trust_level")
ORACLE_TYPES = frozenset({"analytic", "reference_data", "metamorphic", "differential", "invariant", "fixture", "none"})
INDEPENDENCE = frozenset({"independent", "partially_independent", "self_referential"})
TRUST_LEVELS = frozenset({"T0", "T1", "T2", "T3", "T4", "T5"})


def card_path_for(test_file: str) -> Path:
    """Map tests/test_x.py -> test_governance/cards/test_x.yaml"""
    name = Path(test_file).stem
    return CARDS_DIR / f"{name}.yaml"


def load_card(test_file: str) -> dict:
    path = card_path_for(test_file)
    if not path.exists():
        print(f"GOVERNED TEST: BLOCKED - no theory card for {test_file}", file=sys.stderr)
        print(f"  expected at: {path}", file=sys.stderr)
        print(f"  A missing theory card is an infrastructure failure. Do not run", file=sys.stderr)
        print(f"  the test or report a result until the card exists.", file=sys.stderr)
        sys.exit(2)
    with open(path, "r", encoding="utf-8") as f:
        card = yaml.safe_load(f)
    errors = validate_card(card, path)
    if errors:
        print(f"GOVERNED TEST: BLOCKED - malformed theory card {path}:", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        sys.exit(2)
    return card


def validate_card(card: dict, path: Path) -> list[str]:
    errors = []
    if not isinstance(card, dict):
        return ["card is not a mapping"]
    for f in REQUIRED_FIELDS:
        if f not in card:
            errors.append(f"missing required field '{f}'")
    o = card.get("oracle", {})
    if o.get("type") not in ORACLE_TYPES:
        errors.append(f"oracle.type must be one of {sorted(ORACLE_TYPES)}, got {o.get('type')!r}")
    if o.get("independence") not in INDEPENDENCE:
        errors.append(f"oracle.independence must be one of {sorted(INDEPENDENCE)}, got {o.get('independence')!r}")
    if card.get("trust_level") not in TRUST_LEVELS:
        errors.append(f"trust_level must be one of {sorted(TRUST_LEVELS)}, got {card.get('trust_level')!r}")
    # Cross-field consistency: a self-referential oracle cannot claim T2+.
    if o.get("independence") == "self_referential":
        if card.get("trust_level") in ("T2", "T3", "T4", "T5"):
            errors.append("trust_level >= T2 requires an independent (not self_referential) oracle")
        else:
            errors.append("oracle.independence == 'self_referential': this test is worthless; "
                          "fix it, do not run it (see docs/TEST_THEORY.md)")
    # T3+ requires an adversarial review to be declared.
    if card.get("trust_level") in ("T3", "T4", "T5") and card.get("adversarial_review") != "reviewed":
        errors.append(f"trust_level {card['trust_level']} requires adversarial_review: reviewed "
                      f"(got {card.get('adversarial_review')!r})")
    if not card.get("blind_spot", "").strip():
        errors.append("blind_spot must state what class of wrong code this test would NOT catch")
    return errors


def print_theory(card: dict) -> None:
    print("=" * 70)
    print(f"THEORY CARD: {card['test_id']}")
    print(f"  theory:     {card['theory']}")
    o = card["oracle"]
    print(f"  oracle:     type={o.get('type')} independence={o.get('independence')}")
    if o.get("expression"):
        print(f"              {o['expression']}")
    a = card["acceptance"]
    print(f"  acceptance: {a}")
    print(f"  blind_spot: {card.get('blind_spot', '')}")
    print(f"  trust:      {card['trust_level']}")
    if card.get("known_bad_fixture") and card["known_bad_fixture"] != "none":
        print(f"  known-bad:  {card['known_bad_fixture']} (this test MUST fail it)")
    print("=" * 70)


def print_failure_history(test_file: str) -> None:
    """Grep the failure-pattern log for entries matching this test/module so the
    agent cannot avoid seeing past failures of the exact class it is about to
    touch. Turns the passive log into something unavoidable."""
    log = ROOT / "docs" / "AI_FAILURE_PATTERNS.md"
    if not log.exists():
        return
    text = log.read_text(encoding="utf-8", errors="replace")
    stem = Path(test_file).stem
    hits = [ln for ln in text.splitlines() if stem in ln or test_file in ln]
    if hits:
        print(f"  (related failure-pattern entries: {len(hits)} — see docs/AI_FAILURE_PATTERNS.md)")


def classify(returncode: int, card: dict) -> str:
    if returncode == 0:
        return "PASS"
    # pytest uses 1 = tests failed, 2 = test collection/usage error, 4 = usage, 5 = no tests
    if returncode == 2 or returncode == 4 or returncode == 5:
        return "CRASH"
    return "RAN-BUT-FAILED"


def run_mutation(test_file: str, card: dict, as_json: bool) -> int:
    """Discrimination check (T4): real mutation testing.

    Rather than monkeypatch (which bypasses pytest fixtures and only works for
    fixture-free tests), this EDITS the target source file to the mutated value,
    runs the real pytest (fixtures, parametrization and all), then restores the
    file. A test that still passes under the mutation has no discriminating power.

    Safety: the file is restored in a ``finally`` block. If the process is killed
    mid-run, the only residue is a tracked file left modified — visible via
    ``git diff`` and reversible via ``git checkout``. No state is mutated in the
    running process.
    """
    mutation = card.get("mutation")
    if not mutation:
        print(f"MUTATION CHECK: no mutation declared for {card['test_id']}. "
              f"Trust level {card['trust_level']} cannot be T4 without one.",
              file=sys.stderr)
        return 1
    target = mutation.get("file")
    attr = mutation.get("attr")
    new_value = mutation.get("new_value")
    if not (target and attr and new_value is not None):
        print(f"MUTATION CHECK: malformed mutation block for {card['test_id']} "
              f"(needs file/attr/new_value)", file=sys.stderr)
        return 1

    path = ROOT / target
    if not path.exists():
        print(f"MUTATION CHECK: mutation target not found: {target}", file=sys.stderr)
        return 1
    original = path.read_text(encoding="utf-8")

    # Replace the module-level ``attr = <value>`` assignment, whole line.
    import re
    pattern = re.compile(rf"^(\s*{re.escape(attr)}\s*=\s*).*$", re.MULTILINE)
    mutated = pattern.sub(lambda m: f"{m.group(1)}{new_value!r}", original, count=1)
    if mutated == original:
        print(f"MUTATION CHECK: could not find `{attr} = ...` in {target}", file=sys.stderr)
        return 1

    try:
        path.write_text(mutated, encoding="utf-8")
        cmd = [sys.executable, "-m", "pytest", "-q", "--tb=line", test_file]
        proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True,
                              encoding="utf-8", errors="replace")
    finally:
        path.write_text(original, encoding="utf-8")

    if proc.returncode == 0:
        print(f"MUTATION CHECK FAILED: {test_file} still PASSES after mutating "
              f"{target}:{attr} = {new_value}. The test does not discriminate. (T4 not earned.)",
              file=sys.stderr)
        if as_json:
            print(json.dumps({"test_id": card["test_id"], "discriminates": False,
                              "mutation": mutation}, indent=2))
        return 1
    print(f"MUTATION CHECK PASSED: {test_file} FAILS when {target}:{attr} is mutated "
          f"to {new_value}. The test discriminates.")
    if as_json:
        print(json.dumps({"test_id": card["test_id"], "discriminates": True,
                          "mutation": mutation}, indent=2))
    return 0


VALID_CLASSIFICATIONS = ("CODE BUG", "TEST BUG", "KNOWN LIMITATION")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("test_file", help="path to the test file (tests/test_x.py)")
    ap.add_argument("--json", action="store_true", help="emit machine-readable report")
    ap.add_argument("--pytest-args", default="", help="extra args passed to pytest")
    ap.add_argument("--mutate", action="store_true",
                    help="run the discrimination check: does the test FAIL a deliberately-broken variant?")
    ap.add_argument("--classify", choices=VALID_CLASSIFICATIONS,
                    help="ON FAILURE: required classification (CODE BUG | TEST BUG | KNOWN LIMITATION)")
    ap.add_argument("--justification", default="",
                    help="ON FAILURE: must reference the printed oracle/threshold, not just assert")
    args = ap.parse_args()

    card = load_card(args.test_file)
    if not args.json:
        print_theory(card)
        print_failure_history(args.test_file)

    if args.mutate:
        return run_mutation(args.test_file, card, args.json)

    cmd = [sys.executable, "-m", "pytest", "-q", "--tb=short", args.test_file]
    if args.pytest_args:
        cmd += args.pytest_args.split()
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True,
                          encoding="utf-8", errors="replace")
    status = classify(proc.returncode, card)

    report = {
        "test_id": card["test_id"],
        "test_file": args.test_file,
        "status": status,
        "returncode": proc.returncode,
        "trust_level": card["trust_level"],
        "oracle": card["oracle"],
        "acceptance": card["acceptance"],
        "interpretation": card.get("failure_meaning", {}).get(status.lower(), ""),
        # A result is UNTRUSTED until adversarially reviewed. The card declares
        # whether that review exists; without it the trust level is capped at T2.
        "adversarial_review": card.get("adversarial_review", "none"),
        "trusted": card.get("adversarial_review") == "reviewed",
    }

    if status == "PASS":
        print(f"\nGOVERNED RESULT: PASS  (trust {card['trust_level']})")
    else:
        # Enforcement: a failing run does NOT resolve until it is classified.
        # A bare "it failed" without a classification is NOT a completed triage.
        if args.classify is None:
            print(f"\nGOVERNED RESULT: {status}  (trust {card['trust_level']})")
            print(f"  UNCLASSIFIED — run is NOT resolved.", file=sys.stderr)
            print(f"  Re-run with a classification and justification:", file=sys.stderr)
            print(f"    --classify 'CODE BUG|TEST BUG|KNOWN LIMITATION' \\", file=sys.stderr)
            print(f"    --justification '<must reference the oracle/threshold above>'", file=sys.stderr)
            print(f"  Debug steps from the card:", file=sys.stderr)
            for step in card.get("debug", []):
                print(f"    - {step}", file=sys.stderr)
            report["resolved"] = False
            if args.json:
                print(json.dumps(report, indent=2))
            return 1
        if not args.justification.strip():
            print(f"  --classify requires --justification referencing the oracle/threshold.",
                  file=sys.stderr)
            return 1
        report["classification"] = args.classify
        report["justification"] = args.justification
        report["resolved"] = True
        print(f"\nGOVERNED RESULT: {status}  (trust {card['trust_level']})")
        print(f"  classified: {args.classify}")
        print(f"  justification: {args.justification}")

    if args.json:
        print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
