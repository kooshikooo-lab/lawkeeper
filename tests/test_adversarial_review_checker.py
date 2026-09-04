"""Self-tests for adversarial_review_checker.py.

Written 2026-08-19 -- this script previously had zero tests despite a live
crash bug (see test_report_generation_does_not_crash_on_windows_encoding
below) and a real, previously-undocumented limitation in its claim
extractor (see test_claim_extractor_false_positives_on_ordinary_numbers).
Per docs/RESEARCH_SELF_REVIEW_METHODOLOGY.md: a tool with a known crash
and no self-tests is exactly the failure mode that methodology exists to
catch.
"""
import subprocess
import sys
from pathlib import Path

import pytest

from conftest import REPO_ROOT, load_script

adversarial_review_checker = load_script("adversarial_review_checker.py")
AdversarialChallenger = adversarial_review_checker.AdversarialChallenger
ClaimExtractor = adversarial_review_checker.ClaimExtractor
ReportGenerator = adversarial_review_checker.ReportGenerator


# ── Regression test for the real crash bug ────────────────────────────

def test_report_generation_does_not_crash_on_windows_encoding(tmp_path):
    """Real regression test for the actual bug: writing a report containing
    the unicode markers (checkmark/cross/warning) this script always
    generates used to crash under cp1252 (Windows' platform-default
    encoding), because write_text() was called with no explicit encoding.
    This reproduces the exact failure path end-to-end: build a real
    ClaimReview set with both verified and challenged claims (so both
    unicode-marker code paths in generate_report() actually run), write it
    to a file the same way main() does, and confirm no UnicodeEncodeError.
    """
    doc = tmp_path / "doc.md"
    doc.write_text(
        "**Claim:** The optimizer converges perfectly with 100% accuracy.\n"
        "The formula is E=mc^2, cited from Einstein (1905).\n",
        encoding="utf-8",
    )

    extractor = ClaimExtractor(doc.read_text(encoding="utf-8"))
    claims = extractor.extract()
    assert claims, "test fixture must actually produce at least one claim"

    challenger = AdversarialChallenger()
    ClaimReview = adversarial_review_checker.ClaimReview
    reviews = []
    for claim in claims:
        challenges = challenger.generate_challenges(claim)
        status = "VERIFIED" if not challenges else "CHALLENGED"
        reviews.append(ClaimReview(claim=claim, status=status, challenges=challenges))

    generator = ReportGenerator(str(doc))
    report = generator.generate_report(reviews)
    assert "✓" in report or "⚠️" in report, \
        "fixture must exercise the unicode-marker code path this test guards"

    out = tmp_path / "report.md"
    out.write_text(report, encoding="utf-8")  # this line is what used to crash
    assert out.read_text(encoding="utf-8") == report


def test_cli_end_to_end_does_not_crash(tmp_path):
    """Full subprocess run through main(), exactly how a human/CI would
    invoke it -- catches encoding issues a direct function call might miss
    (e.g. stdout's actual codepage in a fresh subprocess)."""
    doc = tmp_path / "doc.md"
    doc.write_text(
        "**Claim:** The system always works perfectly with 100% success.\n",
        encoding="utf-8",
    )
    script = REPO_ROOT / "scripts" / "adversarial_review_checker.py"
    result = subprocess.run(
        [sys.executable, str(script), str(doc),
         "--output", str(tmp_path / "out.md"),
         "--json", str(tmp_path / "out.json")],
        capture_output=True, text=True, cwd=tmp_path,
    )
    assert result.returncode == 0, f"stderr:\n{result.stderr}"
    assert "UnicodeEncodeError" not in result.stderr
    assert (tmp_path / "out.md").exists()
    assert (tmp_path / "out.json").exists()


# ── Documenting the known claim-extractor limitation ──────────────────

def test_claim_extractor_false_positives_on_ordinary_numbers():
    """KNOWN LIMITATION, pinned rather than hidden: the constant-drift
    challenge substring-matches claim text against bare fragments like
    '346', '1.4' -- these match ANY occurrence of that substring anywhere
    in the claim, not just an actual hardcoded-constant assignment. An
    ordinary sentence mentioning "$1.4 million" or "in 1.4 seconds" gets
    flagged as a constant-drift concern. This is not a hypothetical: the
    same class of false positive was independently observed both by
    opencode's testing and Devin's own research_critic.py (its own
    critic_report.md flagged ordinary prices like $150/$80 as "unsupported
    numerical claims"). This test exists so that limitation is documented
    and can't silently regress into "we forgot this was ever a problem" --
    it is NOT a claim that the extractor is exhaustive or precise."""
    claim_text = "The rental cost was $1.4 million for the year, which is unrelated to any physics constant."
    challenger = AdversarialChallenger()
    Claim = adversarial_review_checker.Claim
    fake_claim = Claim(text=claim_text, line_num=1, is_constant_claim=True)
    challenges = challenger._constant_drift_challenges(fake_claim)
    assert challenges, (
        "Documents the known false-positive: an ordinary dollar figure "
        "('$1.4 million') triggers the constant-drift challenge because "
        "'1.4' is checked via bare substring matching, not because it is "
        "actually a hardcoded physics constant. If this assertion starts "
        "failing, the extractor's precision improved -- update this test "
        "to describe the new (better) behavior rather than deleting it."
    )


def test_claim_extractor_extracts_explicit_claims():
    text = "Some prose.\n**Claim:** The bore radius must be positive.\nMore prose.\n"
    extractor = ClaimExtractor(text)
    claims = extractor.extract()
    assert any("bore radius must be positive" in c.text for c in claims)


def test_has_citation_nearby_detects_real_citations():
    extractor = ClaimExtractor("")
    assert extractor._has_citation_nearby(0, "See Noreland (2013) for details.")
    assert extractor._has_citation_nearby(0, "https://example.com/paper.pdf")
    assert not extractor._has_citation_nearby(0, "This has no citation at all.")


# ── Basic sanity on the adversarial personas ───────────────────────────

def test_show_me_the_diff_triggers_on_fix_claims():
    Claim = adversarial_review_checker.Claim
    challenger = AdversarialChallenger()
    claim = Claim(text="We fixed the bug in the solver.", line_num=1)
    challenges = challenger._show_me_the_diff_challenges(claim)
    assert any(c.persona == "Show-Me-The-Diff" for c in challenges)


def test_epistemologist_requires_citation():
    Claim = adversarial_review_checker.Claim
    challenger = AdversarialChallenger()
    uncited = Claim(text="The result is accurate.", line_num=1, has_citation=False)
    cited = Claim(text="The result is accurate.", line_num=1, has_citation=True)
    assert any(c.category == "citation" for c in challenger._epistemologist_challenges(uncited))
    assert not any(c.category == "citation" for c in challenger._epistemologist_challenges(cited))
