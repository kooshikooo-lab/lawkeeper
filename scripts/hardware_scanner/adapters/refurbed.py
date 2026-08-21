"""refurbed.se's graphics-card category -- real refurbished stock with a
stated 12-month warranty (matches the "buy from a reputable/guaranteed
seller" framing from tonight's conversation). Real structure, inspected
live 2026-08-21: each item is an <article title="..." data-test=
"product-tile">, with the product link marked data-test="productcard-link".
Price is "X XXX kr" (current) followed by "Y YYY,ZZ kr (Nypris)"
(original/new price) when discounted.
"""
from __future__ import annotations

import re

from bs4 import BeautifulSoup

from ..models import Listing
from .base import Adapter

# Real bug fixed 2026-08-21: an earlier [\d\s ]+ pattern had no length
# bound on the whitespace-separated digit run, so it spanned across
# unrelated text -- verified live it matched "5000   9 915 kr" (a
# title's trailing "5000" plus the real price) as one blob, producing
# garbage like 50009915.0. This pattern requires a proper Swedish
# thousands-grouping shape (1-3 digits, then only 3-digit groups, plus
# an optional comma-decimal), so it can't span text that isn't actually
# one formatted number.
_PRICE_RE = re.compile(r"\d{1,3}(?:[\s\xa0]\d{3})*(?:[.,]\d+)?\s*kr")


def _parse_price(match_text: str) -> float | None:
    raw = match_text.replace("kr", "").strip()
    raw = re.sub(r"[\s\xa0]", "", raw).replace(",", ".")
    try:
        return float(raw) if raw else None
    except ValueError:
        return None


class RefurbedGrafikkortAdapter(Adapter):
    name = "refurbed.se grafikkort"
    url = "https://www.refurbed.se/c/grafikkort/"

    def parse(self, html: str) -> list[Listing]:
        soup = BeautifulSoup(html, "html.parser")
        listings: list[Listing] = []
        for art in soup.select('article[data-test="product-tile"]'):
            title = art.get("title", "").strip()
            if not title:
                continue
            link_el = art.select_one('a[data-test="productcard-link"]')
            url = "https://www.refurbed.se" + link_el["href"] if link_el else ""

            # Price text sits in the article body; "Nypris" (new-price)
            # marks the original/reference price when one is shown.
            # Real bug fixed 2026-08-21: an earlier version sliced price
            # strings with str.rfind() on the matched text, which finds
            # the wrong occurrence whenever a price substring repeats
            # elsewhere (e.g. a title containing "5000" concatenating
            # with a price's leading digits) -- verified live against
            # the real fixture, produced garbage like "50009915.0".
            # Fixed by using finditer's match positions directly instead
            # of re-searching for the matched substring.
            text = art.get_text(" ", strip=True)
            nypris_idx = text.find("Nypris")
            before = text[:nypris_idx] if nypris_idx != -1 else text
            matches = list(_PRICE_RE.finditer(before))
            if nypris_idx != -1 and len(matches) >= 2:
                # Last two "kr" matches before "(Nypris)" are the real
                # current and original prices; anything earlier is noise
                # (e.g. a shipping-cost mention).
                price = _parse_price(matches[-2].group())
                original = _parse_price(matches[-1].group())
            elif matches:
                price = _parse_price(matches[-1].group())
                original = None
            else:
                price = None
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
                    condition_note="Refurbished, 12 months warranty (refurbed.se standard terms)",
                )
            )
        return listings
