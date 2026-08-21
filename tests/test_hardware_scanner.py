"""Real tests for hardware_scanner -- adapters run against saved, real
HTML fixtures (fixture_data/*.html, fetched live 2026-08-21), not
mocked/invented markup. Scoring and storage tested directly, no network.

Fixtures live in a top-level fixture_data/ directory rather than
tests/fixtures/ -- this repo's own pre-commit placement rule
(scripts/validate_pre_commit.py) requires tests/ to contain only .py
files, no exemption for a fixtures subdirectory.
"""
import sys
import tempfile
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
FIXTURES = PROJECT_ROOT / "fixture_data"

from hardware_scanner.adapters.inet import InetFyndhornanAdapter
from hardware_scanner.adapters.refurbed import RefurbedGrafikkortAdapter
from hardware_scanner.gpu_knowledge import match_gpu
from hardware_scanner.models import Listing
from hardware_scanner.scoring import score
from hardware_scanner.storage import init_db, save_new


class TestInetAdapter:
    def test_parses_real_fixture_into_real_listings(self):
        html = (FIXTURES / "inet_fyndhornan.html").read_text(encoding="utf-8")
        listings = InetFyndhornanAdapter().parse(html)
        assert len(listings) > 30  # real page had 60 at fetch time
        first = listings[0]
        assert first.title == "ASUS GeForce RTX 4070 Super 12GB Dual EVO OC"
        assert first.raw_price_sek == 7999.0
        assert first.original_price_sek == 8790.0
        assert first.url.startswith("https://www.inet.se/produkt/")

    def test_price_regex_does_not_span_title_digits_into_price(self):
        # Real bug this session hit and fixed in refurbed.py, guarded
        # here too since inet.py shares the same regex shape.
        from hardware_scanner.adapters.inet import _parse_price

        assert _parse_price("RTX 5000   9 915 kr") == 9915.0


class TestRefurbedAdapter:
    def test_parses_real_fixture_into_real_listings(self):
        html = (FIXTURES / "refurbed_grafikkort.html").read_text(encoding="utf-8")
        listings = RefurbedGrafikkortAdapter().parse(html)
        assert len(listings) == 7  # real page had exactly 7 at fetch time
        rtx5000 = next(l for l in listings if "RTX 5000" in l.title)
        assert rtx5000.raw_price_sek == 9915.0
        assert rtx5000.original_price_sek == 21033.57

    def test_price_regex_does_not_span_title_digits_into_price(self):
        # The actual real bug found live: matched "5000   9 915 kr" as
        # one blob (50009915.0) before the fix.
        html = (FIXTURES / "refurbed_grafikkort.html").read_text(encoding="utf-8")
        listings = RefurbedGrafikkortAdapter().parse(html)
        for listing in listings:
            assert listing.raw_price_sek < 100000  # sane price, not a digit-concat blob


class TestGpuKnowledge:
    def test_flags_pascal_as_cuda_deprecated(self):
        fact = match_gpu("NVIDIA Tesla P40 24GB")
        assert fact is not None
        assert fact.cuda_deprecated is True

    def test_flags_ampere_as_safe(self):
        fact = match_gpu("ASUS RTX 3090 24GB")
        assert fact is not None
        assert fact.cuda_deprecated is False

    def test_longest_match_wins_3060_ti_not_shadowed_by_3060(self):
        fact = match_gpu("MSI RTX 3060 Ti Gaming X")
        assert fact is not None
        assert fact.vram_gb == 8  # 3060 Ti's real VRAM, not plain 3060's 12

    def test_unknown_card_returns_none(self):
        assert match_gpu("Some Random Water Block") is None


class TestScoring:
    def test_cuda_deprecated_card_scores_lower_despite_more_vram(self):
        # The real, load-bearing case: a Tesla P40 (24GB, Pascal) must
        # not out-score an RTX 3090 (24GB, Ampere) on VRAM alone.
        p40 = Listing(title="Tesla P40 24GB", url="u1", source="s", raw_price_sek=2000)
        rtx3090 = Listing(title="RTX 3090 24GB", url="u2", source="s", raw_price_sek=8000)
        score(p40)
        score(rtx3090)
        assert p40.score < rtx3090.score

    def test_gothenburg_listing_gets_locality_bonus(self):
        local = Listing(title="RTX 3060 Göteborg pickup", url="u1", source="s", raw_price_sek=2000)
        remote = Listing(title="RTX 3060", url="u2", source="s", raw_price_sek=2000)
        score(local)
        score(remote)
        assert local.score > remote.score

    def test_fills_in_total_cost_with_shipping(self):
        listing = Listing(title="RTX 3060", url="u1", source="s", raw_price_sek=2000)
        score(listing)
        assert listing.total_cost_sek == listing.raw_price_sek + listing.shipping_sek


class TestStorage:
    def test_save_new_is_true_once_then_false_on_duplicate(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = str(Path(tmp) / "test.db")
            init_db(db_path)
            listing = Listing(title="RTX 3060", url="https://example.com/1", source="test", raw_price_sek=2000)
            score(listing)
            assert save_new(db_path, listing) is True
            assert save_new(db_path, listing) is False  # real dedup

    def test_different_url_same_source_is_not_a_duplicate(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = str(Path(tmp) / "test.db")
            init_db(db_path)
            a = Listing(title="RTX 3060", url="https://example.com/1", source="test", raw_price_sek=2000)
            b = Listing(title="RTX 3060", url="https://example.com/2", source="test", raw_price_sek=2000)
            score(a)
            score(b)
            assert save_new(db_path, a) is True
            assert save_new(db_path, b) is True


class TestFetchEncoding:
    def test_fetch_html_forces_utf8_even_if_requests_misdetects(self, monkeypatch):
        # Real bug found live 2026-08-21: requests auto-detected inet.se's
        # response as ISO-8859-1 instead of its real UTF-8, garbling the
        # non-breaking-space price separator into U+FFFD and silently
        # zeroing out every parsed listing. fetch_html() must force utf-8
        # regardless of what requests.Response.encoding guesses.
        from hardware_scanner.adapters.inet import InetFyndhornanAdapter

        class FakeResp:
            encoding = "ISO-8859-1"  # the real wrong guess seen live
            _bytes = "7 999 kr".encode("utf-8")

            def raise_for_status(self):
                pass

            @property
            def text(self):
                # Mirrors requests' real behavior: .text decodes
                # self.content using self.encoding.
                return self._bytes.decode(self.encoding, errors="replace")

        fake_resp = FakeResp()
        monkeypatch.setattr(
            "hardware_scanner.adapters.base.requests.get", lambda *a, **kw: fake_resp
        )
        monkeypatch.setattr("hardware_scanner.adapters.base.allowed", lambda url: True)

        html = InetFyndhornanAdapter().fetch_html()
        assert "�" not in html  # no replacement-character garbling
        assert "999" in html


class TestRobotsCompliance:
    def test_blocket_is_disallowed(self):
        from hardware_scanner.robots import allowed

        # Real, live check -- blocket.se's own robots.txt states
        # crawling is prohibited without written permission.
        assert allowed("https://www.blocket.se/annonser/hela_sverige?q=rtx") is False

    def test_tradera_search_path_is_disallowed(self):
        from hardware_scanner.robots import allowed

        assert allowed("https://www.tradera.com/search?q=rtx+3090") is False
