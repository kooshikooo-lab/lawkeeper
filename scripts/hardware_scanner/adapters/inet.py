"""inet.se's Fyndhornan (bargain corner) -- open-box/return clearance
stock. Real structure, inspected live 2026-08-21 against the actual
page (not guessed): each item is an <li data-test-id="search_product_ID">;
discounted price is a <span data-test-is-discounted-price="true">; the
original price sits in a <s> (strikethrough) tag when discounted.

This is retailer clearance, not peer-to-peer -- won't catch the "seller
doesn't know what it's worth" opportunity separately discussed tonight.
That needs Tradera's official API (see tradera.py) or manual Blocket
browsing, since both are off-limits to scraping (see the package
docstring in __init__.py for why).
"""
from __future__ import annotations

import re

from bs4 import BeautifulSoup

from ..models import Listing
from .base import Adapter

# Bounded-grouping pattern, not [\d\s ]+ -- an unbounded run of digits
# and whitespace can span across unrelated text next to a real price
# (e.g. a title's own trailing digits), confirmed as a real bug in the
# refurbed.py adapter tonight (matched "5000   9 915 kr" as one blob).
# This shape (1-3 digits, then only proper 3-digit groups) can't do that.
_PRICE_RE = re.compile(r"\d{1,3}(?:[\s\xa0]\d{3})*(?:[.,]\d+)?\s*kr")


def _parse_price(text: str) -> float | None:
    m = _PRICE_RE.search(text)
    if not m:
        return None
    raw = m.group().replace("kr", "").strip()
    raw = re.sub(r"[\s\xa0]", "", raw).replace(",", ".")
    try:
        return float(raw) if raw else None
    except ValueError:
        return None


class InetFyndhornanAdapter(Adapter):
    name = "inet.se Fyndhornan"
    url = "https://www.inet.se/fyndhornan"

    def parse(self, html: str) -> list[Listing]:
        soup = BeautifulSoup(html, "html.parser")
        listings: list[Listing] = []
        for li in soup.select('li[data-test-id^="search_product_"]'):
            product_id = li.get("data-test-id", "").removeprefix("search_product_")
            title_el = li.select_one("h3")
            if not title_el:
                continue
            title = title_el.get_text(strip=True)

            link_el = li.select_one('a[href*="/produkt/"]')
            url = "https://www.inet.se" + link_el["href"] if link_el else ""

            condition_el = li.select_one("p")
            condition = condition_el.get_text(strip=True) if condition_el else ""

            discounted_el = li.select_one('[data-test-is-discounted-price="true"]')
            strike_el = li.select_one("s")
            if discounted_el:
                price = _parse_price(discounted_el.get_text())
                original = _parse_price(strike_el.get_text()) if strike_el else None
            else:
                # No discount marker -> find any "kr" price in the card.
                price = _parse_price(li.get_text())
                original = None

            if price is None:
                continue

            listings.append(
                Listing(
                    title=title,
                    url=url,
                    source=self.name,
                    raw_price_sek=price,
                    original_price_sek=original,
                    condition_note=condition,
                    product_id=product_id,
                )
            )
        return listings
