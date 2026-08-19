"""Self-tests for code_compliance_checker.py.

Written 2026-08-19 -- same encoding-crash class and same missing-self-tests
gap as adversarial_review_checker.py (see that file's test module for the
full rationale).
"""
import subprocess
import sys
from pathlib import Path

import pytest

from conftest import REPO_ROOT, load_script

code_compliance_checker = load_script("code_compliance_checker.py")
CodeComplianceChecker = code_compliance_checker.CodeComplianceChecker


# ── Regression test for the real crash bug ────────────────────────────

def test_report_generation_does_not_crash_on_windows_encoding(tmp_path):
    """report() embeds unicode markers (checkmark for a clean pass, cross/
    warning/info for violations) directly in its output and previously
    wrote them with platform-default encoding (cp1252 on Windows).
    Exercise both the clean-pass path (checkmark) and the violations path
    (cross/warning/info) so both unicode branches actually run."""
    clean_file = tmp_path / "clean.py"
    clean_file.write_text("x = 1\n", encoding="utf-8")
    checker = CodeComplianceChecker(str(clean_file))
    checker.check_all()
    report = checker.report(str(tmp_path / "clean_report.md"))
    assert "✓" in report
    assert (tmp_path / "clean_report.md").read_text(encoding="utf-8") == report

    violating_file = tmp_path / "violating.py"
    violating_file.write_text(
        "GAMMA = 1.4\n"  # Law 2 violation: hardcoded constant, not imported
        "def unflanged_thing():\n"
        "    real_part = 1.0  # should be (ka)**2/4\n",
        encoding="utf-8",
    )
    checker2 = CodeComplianceChecker(str(violating_file))
    violations = checker2.check_all()
    assert violations, "test fixture must actually trigger at least one violation"
    report2 = checker2.report(str(tmp_path / "violations_report.md"))
    assert "✗" in report2 or "⚠" in report2
    out = tmp_path / "violations_report.md"
    assert out.exists()


def test_cli_end_to_end_does_not_crash(tmp_path):
    """Full subprocess run through main(), exactly how a human/CI invokes it."""
    target = tmp_path / "target.py"
    target.write_text("GAMMA = 1.4\n", encoding="utf-8")
    script = REPO_ROOT / "scripts" / "code_compliance_checker.py"
    result = subprocess.run(
        [sys.executable, str(script), str(target),
         "--output", str(tmp_path / "out.md")],
        capture_output=True, text=True, cwd=tmp_path,
    )
    assert result.returncode == 0, f"stderr:\n{result.stderr}"
    assert "UnicodeEncodeError" not in result.stderr
    assert (tmp_path / "out.md").exists()


# ── Basic sanity on the actual checks ──────────────────────────────────

def test_check_constant_drift_flags_hardcoded_constant(tmp_path):
    f = tmp_path / "t.py"
    f.write_text("GAMMA = 1.4\n", encoding="utf-8")
    checker = CodeComplianceChecker(str(f))
    checker.check_constant_drift()
    assert any(v.law.startswith("Law 2") for v in checker.violations)


def test_check_constant_drift_allows_explicit_override(tmp_path):
    """An explicitly-commented OVERRIDE should not be flagged -- this is
    the escape hatch the checker itself defines (line: 'OVERRIDE' in line)."""
    f = tmp_path / "t.py"
    f.write_text("GAMMA = 1.4  # OVERRIDE: local test fixture value\n", encoding="utf-8")
    checker = CodeComplianceChecker(str(f))
    checker.check_constant_drift()
    assert not any(v.law.startswith("Law 2") for v in checker.violations)


def test_check_constant_drift_allows_proper_import(tmp_path):
    f = tmp_path / "t.py"
    f.write_text(
        "from backend.physics.constants import GAMMA\nGAMMA = 1.4\n",
        encoding="utf-8",
    )
    checker = CodeComplianceChecker(str(f))
    checker.check_constant_drift()
    assert not any(v.law.startswith("Law 2") for v in checker.violations)


def test_check_algorithm_naming_flags_missing_implementation(tmp_path):
    """Claims 'NSGA-II' by name but the code has none of the required
    keywords -- should be flagged as a naming/implementation mismatch."""
    f = tmp_path / "t.py"
    f.write_text("# This uses NSGA-II for optimization\ndef optimize(): pass\n",
                 encoding="utf-8")
    checker = CodeComplianceChecker(str(f))
    checker.check_algorithm_naming()
    assert any("NSGA-II" in v.issue for v in checker.violations)


def test_check_algorithm_naming_passes_when_keywords_present(tmp_path):
    f = tmp_path / "t.py"
    f.write_text(
        "# Uses NSGA-II\n"
        "def optimize():\n"
        "    crossover()\n    mutation()\n    offspring()\n    nondominated()\n",
        encoding="utf-8",
    )
    checker = CodeComplianceChecker(str(f))
    checker.check_algorithm_naming()
    assert not any("NSGA-II" in v.issue for v in checker.violations)


def test_check_imports_flags_nonexistent_function_import(tmp_path):
    f = tmp_path / "t.py"
    f.write_text("from backend.tmm import tmm_instrument_from_radii\n", encoding="utf-8")
    checker = CodeComplianceChecker(str(f))
    checker.check_imports()
    assert any(v.law.startswith("Law 5") for v in checker.violations)


def test_missing_file_raises_filenotfounderror(tmp_path):
    with pytest.raises(FileNotFoundError):
        CodeComplianceChecker(str(tmp_path / "does_not_exist.py"))


def test_clean_report_still_writes_output_file(tmp_path):
    """Regression test for a real, separate bug found while writing these
    tests (not the encoding crash): report() used to `return` on the
    all-clean path BEFORE reaching the write_text() call further down --
    so passing output_file and getting a clean result meant the file was
    silently never written at all, even though the caller explicitly
    asked for it."""
    clean_file = tmp_path / "clean.py"
    clean_file.write_text("x = 1\n", encoding="utf-8")
    checker = CodeComplianceChecker(str(clean_file))
    checker.check_all()
    out_path = tmp_path / "should_exist.md"
    checker.report(str(out_path))
    assert out_path.exists(), "clean-pass report() must still write output_file when given one"
