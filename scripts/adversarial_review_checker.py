#!/usr/bin/env python3
"""
Adversarial Review Checker for Windwright Research

Automatically applies five adversarial personas to research documents:
1. Show-Me-The-Diff Skeptic - demands proof of fixes
2. Devil's-Advocate Re-Deriver - checks derivations from first principles
3. Fix-Broke-Something-Else Adversary - looks for side effects
4. Epistemologist - demands sources and independent validation
5. Incentive-Aware Skeptic - checks for confirmation bias

Usage:
    python adversarial_review_checker.py <document.md> [--output report.md] [--strict]

Output:
    - Fact-Check Report (markdown)
    - VERIFICATION_STATUS.json (machine-readable)
    - Challenged Claims CSV (for tracking)
"""

import re
import sys
import json
import argparse
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from pathlib import Path

# Fix (2026-08-19): this script writes/prints unicode markers (checkmarks,
# warning signs) and previously used platform-default encoding everywhere,
# which is cp1252 on Windows -- UnicodeEncodeError, every run, on this
# platform. Two separate fixes needed: reconfigure stdout for the print()
# calls, AND pass encoding="utf-8" explicitly to every read_text()/
# write_text() call (write_text's platform-default encoding is the more
# fundamental crash -- the report content is GUARANTEED to contain these
# characters, so writing the report file failed unconditionally on
# Windows regardless of console codepage).
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


@dataclass
class Claim:
    """A factual claim extracted from a document."""
    text: str
    line_num: int
    context: str = ""
    has_citation: bool = False
    is_algorithm_claim: bool = False
    is_constant_claim: bool = False
    is_radiation_claim: bool = False
    is_optimization_claim: bool = False


@dataclass
class Challenge:
    """A challenge or question raised against a claim."""
    persona: str  # which adversary raised it
    question: str
    severity: str  # critical, high, medium, low
    category: str  # algorithm, citation, derivation, etc.
    recommended_action: Optional[str] = None


@dataclass
class ClaimReview:
    """Complete review of one claim."""
    claim: Claim
    status: str  # VERIFIED, UNVERIFIED, CHALLENGED, INCORRECT
    challenges: List[Challenge]
    verification_evidence: Optional[str] = None
    confidence: str = "Medium"  # High, Medium, Low


class ClaimExtractor:
    """Extracts claims from markdown documents."""
    
    # Patterns for detecting claims
    EXPLICIT_CLAIM_PATTERN = r'\*\*Claim[:\s]*\*\*\s*(.+?)(?:\n|$)'
    STRONG_ASSERTION_PATTERN = r'(?:^|\s)((?:The|This|We|The code|The formula|The value)\s+.+?(?:is|are|shows|demonstrates|proves|implements)\s+.+?)(?:\.|,|;|\n)'
    ALGORITHM_PATTERN = r'\b(?:NSGA-II|NSGA-III|Sobol|Morris|Latin Hypercube|LHS|Differential Evolution|L-BFGS-B)\b'
    CONSTANT_PATTERN = r'\b(?:speed of sound|SoS|gamma|density|rho|viscosity|eta|SPEED_OF_SOUND|GAMMA|RHO)\b'
    RADIATION_PATTERN = r'\b(?:radiation|end correction|impedance|flanged|unflanged|Levine-Schwinger|COMSOL)\b'
    OPTIMIZATION_PATTERN = r'\b(?:optimization|converge|Pareto|fitness|objective)\b'
    
    def __init__(self, document_text: str):
        self.text = document_text
        self.lines = document_text.split('\n')
        
    def extract(self) -> List[Claim]:
        """Extract all claims from document."""
        claims = []
        
        # Find explicit claims
        for match in re.finditer(self.EXPLICIT_CLAIM_PATTERN, self.text):
            claim_text = match.group(1).strip()
            line_num = self.text[:match.start()].count('\n')
            context = self._get_context(line_num)
            claims.append(Claim(
                text=claim_text,
                line_num=line_num,
                context=context,
                has_citation=self._has_citation_nearby(line_num, context)
            ))
        
        # Find strong assertions
        for match in re.finditer(self.STRONG_ASSERTION_PATTERN, self.text, re.MULTILINE):
            claim_text = match.group(1).strip()
            line_num = self.text[:match.start()].count('\n')
            if len(claim_text) > 20 and claim_text not in [c.text for c in claims]:
                context = self._get_context(line_num)
                claims.append(Claim(
                    text=claim_text,
                    line_num=line_num,
                    context=context,
                    has_citation=self._has_citation_nearby(line_num, context)
                ))
        
        # Mark special claim types
        for claim in claims:
            claim.is_algorithm_claim = bool(re.search(self.ALGORITHM_PATTERN, claim.text, re.IGNORECASE))
            claim.is_constant_claim = bool(re.search(self.CONSTANT_PATTERN, claim.text, re.IGNORECASE))
            claim.is_radiation_claim = bool(re.search(self.RADIATION_PATTERN, claim.text, re.IGNORECASE))
            claim.is_optimization_claim = bool(re.search(self.OPTIMIZATION_PATTERN, claim.text, re.IGNORECASE))
        
        return claims
    
    def _get_context(self, line_num: int, width: int = 2) -> str:
        """Get surrounding lines as context."""
        start = max(0, line_num - width)
        end = min(len(self.lines), line_num + width + 1)
        return '\n'.join(self.lines[start:end])
    
    def _has_citation_nearby(self, line_num: int, context: str) -> bool:
        """Check if claim has citation in nearby context."""
        citation_patterns = [
            r'\[.*?\]',  # [reference]
            r'\(\d{4}\)',  # (year)
            r'eq(?:uation)?\.?\s*\d+',  # equation 5
            r'page\s*\d+',  # page 42
            r'https?://',  # URL
        ]
        for pattern in citation_patterns:
            if re.search(pattern, context):
                return True
        return False


class AdversarialChallenger:
    """Applies adversarial personas to generate challenges."""
    
    # Known good patterns for algorithms
    ALGORITHM_REQUIREMENTS = {
        'NSGA-II': [
            'crossover',
            'mutation', 
            'parent selection',
            'offspring generation',
            'non-dominated sorting'
        ],
        'Sobol': [
            'variance decomposition',
            'Latin Hypercube Sampling',
            'LHS',
            'Halton',
            'low-discrepancy'
        ],
        'Morris': [
            'elementary effect',
            'radial sampling',
            'trajectory-based',
            'one-factor-at-a-time'
        ],
        'Latin Hypercube': [
            'stratification',
            'each dimension divided',
            'one sample per stratum'
        ]
    }
    
    # Known sources for radiation models
    RADIATION_SOURCES = {
        'unflanged_real': '(ka)²/4',
        'flanged_real': '(ka)²/2',
        'unflanged_imag': '0.6133*ka',
        'flanged_imag': 'ka',
        'unflanged_end_correction': '0.6133*a',
        'flanged_end_correction': '0.8216*a'
    }
    
    def generate_challenges(self, claim: Claim) -> List[Challenge]:
        """Generate all relevant challenges for a claim."""
        challenges = []
        
        # Apply universal challenges
        challenges.extend(self._epistemologist_challenges(claim))
        challenges.extend(self._show_me_the_diff_challenges(claim))
        challenges.extend(self._incentive_aware_challenges(claim))
        
        # Apply specific-type challenges
        if claim.is_algorithm_claim:
            challenges.extend(self._algorithm_mislabeling_challenges(claim))
        if claim.is_constant_claim:
            challenges.extend(self._constant_drift_challenges(claim))
        if claim.is_radiation_claim:
            challenges.extend(self._radiation_model_challenges(claim))
        if claim.is_optimization_claim:
            challenges.extend(self._optimization_challenges(claim))
        
        return challenges
    
    def _epistemologist_challenges(self, claim: Claim) -> List[Challenge]:
        """The Epistemologist: "That's Not Evidence" challenges."""
        challenges = []
        
        if not claim.has_citation:
            challenges.append(Challenge(
                persona='Epistemologist',
                question=f"This claim has no source citation. Is it empirical (needs measurement) or theoretical (needs derivation)? Please cite a paper, textbook, or equation number.",
                severity='high',
                category='citation',
                recommended_action='Add full citation with equation number or page reference'
            ))
        
        # Check for self-referential validation
        if 'test' in claim.text.lower() and 'pass' in claim.text.lower():
            if 'independent' not in claim.text.lower() and 'reference' not in claim.text.lower():
                challenges.append(Challenge(
                    persona='Epistemologist',
                    question=f"You say 'test passes' but what's the ground truth? Does your test validate against an independent reference (paper, measurement, analytical solution) or just internal consistency?",
                    severity='high',
                    category='validation',
                    recommended_action='Show test compares against independent ground truth, or relabel as internal consistency check'
                ))
        
        return challenges
    
    def _show_me_the_diff_challenges(self, claim: Claim) -> List[Challenge]:
        """The Show-Me-The-Diff Skeptic challenges."""
        challenges = []
        
        # Detect fix/correction claims
        if any(word in claim.text.lower() for word in ['fix', 'fixed', 'correct', 'corrected', 'wrong', 'error']):
            challenges.append(Challenge(
                persona='Show-Me-The-Diff',
                question=f"You claim to have fixed something. Show the before/after code diff: (1) What was the wrong value? (2) What's the right value? (3) File name and line numbers?",
                severity='critical',
                category='proof',
                recommended_action='Provide actual diff with line numbers and git commit hash'
            ))
        
        return challenges
    
    def _incentive_aware_challenges(self, claim: Claim) -> List[Challenge]:
        """The Incentive-Aware Skeptic challenges."""
        challenges = []
        
        # Detect suspiciously perfect results
        if any(word in claim.text.lower() for word in ['perfect', '100%', 'always', 'all correct', 'completely correct']):
            challenges.append(Challenge(
                persona='Incentive-Aware Skeptic',
                question=f"This result is suspiciously perfect. What would a negative or failing case look like? Can you show at least one case where something didn't work?",
                severity='medium',
                category='bias',
                recommended_action='Show failure cases or edge cases where this approach has limitations'
            ))
        
        # Detect convenient success
        if 'success' in claim.text.lower() or 'works' in claim.text.lower():
            challenges.append(Challenge(
                persona='Incentive-Aware Skeptic',
                question=f"Is this result independent verification or only from the same agent/code? Was it validated by someone/something else?",
                severity='medium',
                category='independence',
                recommended_action='Add independent verification or explicit caveat that it\'s unverified'
            ))
        
        return challenges
    
    def _algorithm_mislabeling_challenges(self, claim: Claim) -> List[Challenge]:
        """Check algorithm implementation claims."""
        challenges = []
        
        # Extract algorithm name
        algo_match = re.search(r'\b(' + '|'.join(self.ALGORITHM_REQUIREMENTS.keys()) + r')\b', claim.text, re.IGNORECASE)
        if algo_match:
            algo_name = algo_match.group(1).upper()
            if algo_name in self.ALGORITHM_REQUIREMENTS:
                requirements = self.ALGORITHM_REQUIREMENTS[algo_name]
                challenges.append(Challenge(
                    persona='Devil\'s-Advocate Re-Deriver',
                    question=f"You claim to implement {algo_name}. This algorithm requires: {', '.join(requirements[:3])}. Show your code implements all of these steps, not just some.",
                    severity='critical',
                    category='algorithm',
                    recommended_action=f'Show implementation has all key steps of {algo_name}, or rename to what it actually does'
                ))
        
        return challenges
    
    def _constant_drift_challenges(self, claim: Claim) -> List[Challenge]:
        """Check for hardcoded constant violations."""
        challenges = []
        
        # Check for hardcoded values
        if any(pattern in claim.text for pattern in ['=', 'hardcoded', '346', '1.4', '1.204', '1.2e-9']):
            challenges.append(Challenge(
                persona='Show-Me-The-Diff',
                question=f"This claim involves a physical constant. (1) Where does this value come from (cite source with equation/page)? (2) Is this constant also defined in the main repo? If yes, why re-hardcode it instead of importing?",
                severity='high',
                category='constant_drift',
                recommended_action='Import constants from canonical location or add comment explaining why local override is needed'
            ))
        
        return challenges
    
    def _radiation_model_challenges(self, claim: Claim) -> List[Challenge]:
        """Check radiation model claims."""
        challenges = []
        
        # Unflanged impedance
        if 'unflanged' in claim.text.lower():
            challenges.append(Challenge(
                persona='Devil\'s-Advocate Re-Deriver',
                question=f"For unflanged pipe radiation, Levine-Schwinger (1948) gives: real part = (ka)²/4, imaginary part = 0.6133·ka. Does your code match? Show the formula.",
                severity='high',
                category='radiation',
                recommended_action='Verify against Levine-Schwinger 1948 eq. (2.6)'
            ))
        
        # Flanged impedance  
        if 'flanged' in claim.text.lower():
            challenges.append(Challenge(
                persona='Devil\'s-Advocate Re-Deriver',
                question=f"For flanged piston radiation, typical model: real part = (ka)²/2, imaginary part = ka. Does your code match? Show the formula (not self-canceling numerator/denominator).",
                severity='high',
                category='radiation',
                recommended_action='Verify COMSOL formula doesn\'t have identical numerator and denominator terms'
            ))
        
        # End correction
        if 'end correction' in claim.text.lower():
            challenges.append(Challenge(
                persona='Devil\'s-Advocate Re-Deriver',
                question=f"End correction values: unflanged ≈ 0.6133a, flanged ≈ 0.8216a (for cylinder). Which case applies? Is there a hardcoded 1.0 anywhere?",
                severity='high',
                category='radiation',
                recommended_action='Use correct end correction for your geometry; search codebase for hardcoded 1.0 in radiation'
            ))
        
        return challenges
    
    def _optimization_challenges(self, claim: Claim) -> List[Challenge]:
        """Check optimization/convergence claims."""
        challenges = []
        
        if any(word in claim.text.lower() for word in ['converge', 'optimized', 'pareto', 'improvement']):
            challenges.append(Challenge(
                persona='Incentive-Aware Skeptic',
                question=f"You claim optimization 'works' or shows improvement. (1) What's the baseline for comparison (random? no optimization?)? (2) How much better (% improvement or actual numbers)? (3) Show the Pareto front plot.",
                severity='high',
                category='optimization',
                recommended_action='Show numerical results with baseline comparison and Pareto front visualization'
            ))
            
            challenges.append(Challenge(
                persona='Show-Me-The-Diff',
                question=f"Can you solve a simple analytical test case (e.g., open-open pipe with known resonance frequencies)? Does optimizer recover the known answer?",
                severity='medium',
                category='validation',
                recommended_action='Add analytical test case to validation suite'
            ))
        
        return challenges


class ReportGenerator:
    """Generates structured fact-check reports."""
    
    def __init__(self, document_path: str):
        self.doc_path = Path(document_path)
        self.doc_text = self.doc_path.read_text(encoding="utf-8")
        self.doc_name = self.doc_path.stem
        self.timestamp = datetime.now().isoformat()
        
    def generate_report(self, reviews: List[ClaimReview]) -> str:
        """Generate markdown fact-check report."""
        
        total_claims = len(reviews)
        verified = len([r for r in reviews if r.status == 'VERIFIED'])
        unverified = len([r for r in reviews if r.status == 'UNVERIFIED'])
        challenged = len([r for r in reviews if r.status == 'CHALLENGED'])
        incorrect = len([r for r in reviews if r.status == 'INCORRECT'])
        
        critical_count = len([c for r in reviews for c in r.challenges if c.severity == 'critical'])
        high_count = len([c for r in reviews for c in r.challenges if c.severity == 'high'])
        
        report = f"""# Fact-Check Report: {self.doc_name}

**Document:** {self.doc_path}  
**Generated:** {self.timestamp}  
**Reviewer:** Adversarial Review Framework (Claude)

## Executive Summary

- Total claims reviewed: {total_claims}
- ✓ Verified claims: {verified} ({100*verified//max(total_claims,1)}%)
- ⏳ Unverified claims: {unverified} ({100*unverified//max(total_claims,1)}%)
- ⚠️ Challenged claims: {challenged} ({100*challenged//max(total_claims,1)}%)
- ✗ Incorrect claims: {incorrect} ({100*incorrect//max(total_claims,1)}%)

**Critical Issues Found:** {critical_count}  
**High-Priority Issues:** {high_count}

---

## Verified Claims

"""
        for review in reviews:
            if review.status == 'VERIFIED':
                report += f"### ✓ {review.claim.text}\n"
                if review.verification_evidence:
                    report += f"**Evidence:** {review.verification_evidence}\n"
                report += f"**Confidence:** {review.confidence}\n\n"
        
        report += "\n---\n\n## Unverified Claims\n\n"
        for review in reviews:
            if review.status == 'UNVERIFIED':
                report += f"### ⏳ {review.claim.text}\n"
                report += f"**Location:** Line {review.claim.line_num}\n"
                if review.challenges:
                    report += f"**Required:** {review.challenges[0].recommended_action}\n\n"
        
        report += "\n---\n\n## Challenged Claims\n\n"
        for review in reviews:
            if review.status == 'CHALLENGED':
                report += f"### ⚠️ {review.claim.text}\n"
                report += f"**Location:** Line {review.claim.line_num}\n\n"
                report += "**Challenges:**\n"
                for i, challenge in enumerate(review.challenges, 1):
                    report += f"{i}. **{challenge.persona}:** {challenge.question}\n"
                    if challenge.recommended_action:
                        report += f"   → *Action:* {challenge.recommended_action}\n"
                report += "\n"
        
        report += "\n---\n\n## Issues by Severity\n\n"
        
        for severity in ['critical', 'high', 'medium', 'low']:
            issues = [c for r in reviews for c in r.challenges if c.severity == severity]
            if issues:
                report += f"### {severity.upper()} ({len(issues)})\n\n"
                for issue in issues[:5]:  # Show top 5
                    report += f"- {issue.persona}: {issue.question}\n"
                if len(issues) > 5:
                    report += f"- ... and {len(issues) - 5} more\n"
                report += "\n"
        
        return report
    
    def generate_json_status(self, reviews: List[ClaimReview]) -> str:
        """Generate machine-readable verification status."""
        status = {
            'document': self.doc_name,
            'timestamp': self.timestamp,
            'summary': {
                'total_claims': len(reviews),
                'verified': len([r for r in reviews if r.status == 'VERIFIED']),
                'unverified': len([r for r in reviews if r.status == 'UNVERIFIED']),
                'challenged': len([r for r in reviews if r.status == 'CHALLENGED']),
                'incorrect': len([r for r in reviews if r.status == 'INCORRECT']),
            },
            'claims': [
                {
                    'text': r.claim.text,
                    'line': r.claim.line_num,
                    'status': r.status,
                    'confidence': r.confidence,
                    'challenges': [
                        {
                            'persona': c.persona,
                            'severity': c.severity,
                            'category': c.category,
                            'question': c.question
                        } for c in r.challenges
                    ]
                } for r in reviews
            ]
        }
        return json.dumps(status, indent=2)


def main():
    parser = argparse.ArgumentParser(description='Adversarial Review Checker for Windwright Research')
    parser.add_argument('document', help='Markdown document to review')
    parser.add_argument('--output', default=None, help='Output report filename')
    parser.add_argument('--json', default=None, help='Output JSON status filename')
    parser.add_argument('--strict', action='store_true', help='Fail on any unverified claims')
    parser.add_argument('--min-confidence', default='Medium', help='Minimum confidence level')
    
    args = parser.parse_args()
    
    # Extract claims
    print(f"[*] Reading {args.document}...")
    doc_text = Path(args.document).read_text(encoding="utf-8")
    extractor = ClaimExtractor(doc_text)
    claims = extractor.extract()
    print(f"[*] Extracted {len(claims)} claims")
    
    # Generate challenges
    print(f"[*] Applying adversarial personas...")
    challenger = AdversarialChallenger()
    reviews = []
    for claim in claims:
        challenges = challenger.generate_challenges(claim)
        
        # Auto-assign status based on challenges
        if not challenges:
            status = 'VERIFIED'
        elif any(c.severity == 'critical' for c in challenges):
            status = 'INCORRECT'
        elif any(c.severity in ['critical', 'high'] for c in challenges):
            status = 'CHALLENGED'
        else:
            status = 'UNVERIFIED'
        
        review = ClaimReview(claim=claim, status=status, challenges=challenges)
        reviews.append(review)
    
    # Generate reports
    print(f"[*] Generating reports...")
    generator = ReportGenerator(args.document)
    
    markdown_report = generator.generate_report(reviews)
    json_status = generator.generate_json_status(reviews)
    
    # Output
    output_path = Path(args.output) if args.output else Path(f"{generator.doc_name}_fact_check.md")
    json_path = Path(args.json) if args.json else Path(f"{generator.doc_name}_status.json")
    
    output_path.write_text(markdown_report, encoding="utf-8")
    json_path.write_text(json_status, encoding="utf-8")
    
    print(f"[✓] Report: {output_path}")
    print(f"[✓] Status: {json_path}")
    
    # Summary
    critical = len([r for r in reviews if any(c.severity == 'critical' for c in r.challenges)])
    high = len([r for r in reviews if any(c.severity == 'high' for c in r.challenges)])
    
    print(f"\n[!] Summary: {critical} critical, {high} high-priority issues found")
    
    if args.strict and (critical > 0 or high > 0):
        print("[✗] FAILED: Unresolved issues found (--strict mode)")
        exit(1)
    else:
        print("[✓] COMPLETE")
        exit(0)


if __name__ == '__main__':
    main()
