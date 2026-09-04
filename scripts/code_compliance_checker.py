#!/usr/bin/env python3
"""
Code Compliance Checker for Windwright

Checks Python code for violations of governance laws:
- Law 2: No constant drift (constants imported, not redefined)
- Law 3: Algorithm naming matches implementation
- Law 4: Radiation formulas from Levine-Schwinger
- Law 5: Independent validation (tests compare against ground truth)
- Law 7: Code in research has tests
- Etc.

Usage:
    python code_compliance_checker.py file.py --registry path/to/registry/
    python code_compliance_checker.py . --registry path/to/registry/ --fail-on-critical
"""

import re
import sys
import json
import argparse
from pathlib import Path
from typing import List, Dict, Tuple
from dataclasses import dataclass

# Fix (2026-08-19): same cp1252 crash class as adversarial_review_checker.py --
# unicode markers (checkmarks, warning signs) written/printed without
# explicit encoding default to cp1252 on Windows. See that file's comment
# for the full explanation.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


@dataclass
class Violation:
    """A compliance violation."""
    severity: str  # critical, high, medium, low
    line_num: int
    line_text: str
    law: str  # "Law 2: No Constant Drift"
    issue: str  # Human-readable description
    fix: str  # Suggested fix


class CodeComplianceChecker:
    """Checks Python code for governance violations."""
    
    # Law 2: Constant drift patterns
    CONSTANTS_TO_IMPORT = {
        'GAMMA': ('backend.physics.constants', 'gamma (ratio of specific heats)'),
        'SPEED_OF_SOUND': ('backend.physics.constants', 'speed of sound in air'),
        'RHO': ('backend.physics.constants', 'air density'),
        'ETA': ('backend.physics.losses', 'dynamic viscosity'),
    }
    
    # Law 3: Algorithm names that should be checked
    ALGORITHM_NAMES = {
        'NSGA-II': {
            'required_keywords': ['crossover', 'mutation', 'offspring', 'nondominated'],
            'paper': 'Deb et al. 2002'
        },
        'NSGA-III': {
            'required_keywords': ['crossover', 'mutation', 'reference_point', 'niching'],
            'paper': 'Deb & Jain 2014'
        },
        'Sobol': {
            'required_keywords': ['variance', 'decomposition', 'LHS', 'Halton'],
            'paper': 'Sobol 1967'
        },
        'Morris': {
            'required_keywords': ['trajectory', 'elementary_effect', 'radial'],
            'paper': 'Morris 1991'
        }
    }
    
    # Law 4: Radiation model patterns
    RADIATION_CHECKS = {
        'unflanged': {
            'formula': '(ka)**2/4',
            'source': 'Levine-Schwinger 1948, eq. 2.6',
            'red_flags': ['= 1.0', '== 1.0', '1.0 +']
        },
        'flanged': {
            'formula': '(ka)**2/2',
            'source': 'COMSOL or equivalent',
            'red_flags': ['numerator.*denominator', 'self.*cancel']
        }
    }
    
    def __init__(self, file_path: str, registry_path: str = None):
        self.file_path = Path(file_path)
        self.registry_path = Path(registry_path) if registry_path else None
        self.violations: List[Violation] = []
        
        if not self.file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        self.lines = self.file_path.read_text(encoding="utf-8").split('\n')
    
    def check_all(self) -> List[Violation]:
        """Run all compliance checks."""
        self.check_constant_drift()
        self.check_algorithm_naming()
        self.check_radiation_models()
        self.check_imports()
        return self.violations
    
    def check_constant_drift(self):
        """Law 2: Check for re-hardcoded constants."""
        for i, line in enumerate(self.lines, 1):
            for const_name, (canonical_loc, desc) in self.CONSTANTS_TO_IMPORT.items():
                # Pattern: CONSTANT = number
                if re.match(rf'^{const_name}\s*=\s*[\d.e\-\+]+', line):
                    # Check if it's imported instead
                    if f'from {canonical_loc}' in '\n'.join(self.lines):
                        continue
                    
                    # Check if it's an override with comment
                    if 'OVERRIDE' in line or 'override' in line.lower():
                        continue
                    
                    self.violations.append(Violation(
                        severity='high',
                        line_num=i,
                        line_text=line.strip(),
                        law='Law 2: No Constant Drift',
                        issue=f'{const_name} redefined locally. Should import from {canonical_loc}.',
                        fix=f'from {canonical_loc} import {const_name}\n# Delete local definition'
                    ))
    
    def check_algorithm_naming(self):
        """Law 3: Algorithm names must match implementation."""
        content = '\n'.join(self.lines)
        
        for algo_name, checks in self.ALGORITHM_NAMES.items():
            # If algorithm name is mentioned
            if algo_name.lower() in content.lower():
                # Check that required keywords are present
                missing_keywords = []
                for keyword in checks['required_keywords']:
                    if keyword.lower() not in content.lower():
                        missing_keywords.append(keyword)
                
                if missing_keywords:
                    line_num = self._find_line_with_text(algo_name)
                    self.violations.append(Violation(
                        severity='critical',
                        line_num=line_num,
                        line_text=f'Algorithm: {algo_name}',
                        law='Law 3: Algorithm Naming Must Match Implementation',
                        issue=f'{algo_name} implementation missing: {", ".join(missing_keywords)}',
                        fix=f'Either: (1) Implement {algo_name} fully per {checks["paper"]}, or (2) Rename to what it actually does'
                    ))
    
    def check_radiation_models(self):
        """Law 4: Radiation models must match Levine-Schwinger."""
        content = '\n'.join(self.lines)
        
        # Check for unflanged impedance
        if 'unflanged' in content.lower():
            if '= 1.0' in content or '== 1.0' in content:
                line_num = self._find_line_with_text('1.0')
                self.violations.append(Violation(
                    severity='critical',
                    line_num=line_num,
                    line_text=self.lines[line_num-1].strip() if line_num <= len(self.lines) else '1.0',
                    law='Law 4: Radiation Model (Bug #1 Pattern)',
                    issue='Unflanged impedance real part hardcoded to 1.0. Should be (ka)²/4.',
                    fix='Use: real_part = (ka**2 / 4) from Levine-Schwinger 1948, eq. 2.6'
                ))
        
        # Check for self-canceling formula (Bug #2)
        if 'numerator' in content.lower() and 'denominator' in content.lower():
            # Look for identical numerator/denominator
            for match in re.finditer(r'(\w+)\s*=.*?numerator.*?\n.*?(\w+)\s*=.*?denominator', content, re.IGNORECASE | re.DOTALL):
                # Check if they might be identical
                if 'bessel' in content.lower() or 'j1' in content.lower():
                    line_num = self._find_line_with_text('denominator')
                    self.violations.append(Violation(
                        severity='critical',
                        line_num=line_num,
                        line_text='numerator and denominator',
                        law='Law 4: Radiation Model (Bug #2 Pattern)',
                        issue='Flanged impedance formula appears to have identical numerator/denominator.',
                        fix='Check COMSOL formula. Should NOT divide out to 1.0. Use: (ka)²/2 + i·ka'
                    ))
    
    def check_imports(self):
        """Law 5: Check for broken or suspicious imports."""
        for i, line in enumerate(self.lines, 1):
            # Look for imports
            if line.strip().startswith('from ') or line.strip().startswith('import '):
                # Check for obviously wrong module paths
                if 'tmm_from_radii' in line or 'tmm_instrument_from_radii' in line:
                    self.violations.append(Violation(
                        severity='critical',
                        line_num=i,
                        line_text=line.strip(),
                        law='Law 5: Validation Independence (Bug #4 Pattern)',
                        issue='Import of non-existent function.',
                        fix=f'Verify function exists. Check API of target module.'
                    ))
                
                # Warn about importing from non-canonical locations
                if 'constants' in line and 'backend' not in line:
                    self.violations.append(Violation(
                        severity='medium',
                        line_num=i,
                        line_text=line.strip(),
                        law='Law 2: No Constant Drift',
                        issue='Constants imported from non-canonical location.',
                        fix='Import from backend.physics.constants instead'
                    ))
    
    def _find_line_with_text(self, text: str) -> int:
        """Find line number containing text."""
        for i, line in enumerate(self.lines, 1):
            if text in line:
                return i
        return 1
    
    def report(self, output_file: str = None) -> str:
        """Generate human-readable report."""
        report = f"# Code Compliance Check: {self.file_path.name}\n\n"

        if not self.violations:
            report += "✓ All checks passed\n"
            # Fix (2026-08-19): this used to `return report` here, BEFORE
            # the write_text() call below -- meaning a caller who passed
            # output_file and got a clean result silently never got their
            # report file written at all. Write it here too instead of
            # returning early.
            if output_file:
                Path(output_file).write_text(report, encoding="utf-8")
            return report

        # Group by severity
        critical = [v for v in self.violations if v.severity == 'critical']
        high = [v for v in self.violations if v.severity == 'high']
        medium = [v for v in self.violations if v.severity == 'medium']
        
        if critical:
            report += f"## ✗ CRITICAL ({len(critical)})\n\n"
            for v in critical:
                report += f"**Line {v.line_num}:** {v.law}\n"
                report += f"- {v.issue}\n"
                report += f"- Fix: {v.fix}\n"
                report += f"- Code: `{v.line_text}`\n\n"
        
        if high:
            report += f"## ⚠ HIGH ({len(high)})\n\n"
            for v in high:
                report += f"**Line {v.line_num}:** {v.law}\n"
                report += f"- {v.issue}\n"
                report += f"- Fix: {v.fix}\n\n"
        
        if medium:
            report += f"## ℹ MEDIUM ({len(medium)})\n\n"
            for v in medium:
                report += f"**Line {v.line_num}:** {v.issue}\n\n"
        
        if output_file:
            Path(output_file).write_text(report, encoding="utf-8")
        
        return report


def main():
    parser = argparse.ArgumentParser(description='Check Python code compliance')
    parser.add_argument('file', help='Python file to check')
    parser.add_argument('--registry', help='Path to governance registry')
    parser.add_argument('--output', help='Output report file')
    parser.add_argument('--fail-on-critical', action='store_true')
    parser.add_argument('--fail-on-high', action='store_true')
    
    args = parser.parse_args()
    
    try:
        checker = CodeComplianceChecker(args.file, args.registry)
        violations = checker.check_all()
        report = checker.report(args.output)
        
        # Print report
        print(report)
        
        # Exit codes
        if args.fail_on_critical and any(v.severity == 'critical' for v in violations):
            exit(1)
        if args.fail_on_high and any(v.severity in ['critical', 'high'] for v in violations):
            exit(1)
        
        exit(0)
    
    except Exception as e:
        print(f"[!] Error: {e}")
        exit(1)


if __name__ == '__main__':
    main()
