"""Tradera's official REST v4 API (SearchService) -- the legitimate path
to peer-to-peer listings, since scraping tradera.com's /search page is
explicitly disallowed by its own robots.txt.

**Honest status, not glossed over: this is a scaffold, not a verified
adapter.** Tradera's developer docs at api.tradera.com require a
registered account to view in full, and this session doesn't have
credentials to register one or test a real request/response. The shape
below (endpoint path, auth headers, query params) follows the publicly
documented facts (REST v4, SearchService, TRADERA_APP_ID/TRADERA_APP_KEY
auth) but has NOT been exercised against a real response. Treat
`parse()`'s field names as a best guess to correct once real JSON is in
hand -- don't trust this the way inet.py/refurbed.py (both tested
against real, saved responses) can be trusted.

To activate: register at https://api.tradera.com/, set
TRADERA_APP_ID and TRADERA_APP_KEY in the environment, then run this
adapter once against a real query and fix parse() against the real
response shape before relying on its output.
"""
from __future__ import annotations

import os

import requests

from ..models import Listing
from .base import Adapter


class TraderaSearchAdapter(Adapter):
    """Not a scraper -- calls Tradera's own API. fetch_html() is
    overridden entirely; the base class's robots.txt gate doesn't apply
    here since this never touches tradera.com's HTML pages."""

    name = "Tradera (official API)"
    url = "https://api.tradera.com/v4/search"  # unverified path, see docstring

    def __init__(self, query: str):
        self.query = query
        self.app_id = os.environ.get("TRADERA_APP_ID")
        self.app_key = os.environ.get("TRADERA_APP_KEY")

    def fetch_html(self) -> str:
        raise NotImplementedError(
            "TraderaSearchAdapter uses fetch_json(), not fetch_html() -- "
            "it's an API client, not a page scraper."
        )

    def fetch_json(self) -> dict:
        if not self.app_id or not self.app_key:
            raise RuntimeError(
                "TRADERA_APP_ID / TRADERA_APP_KEY not set -- register at "
                "https://api.tradera.com/ and set both before using this adapter."
            )
        resp = requests.get(
            self.url,
            params={"query": self.query},
            headers={
                "X-Tradera-AppId": self.app_id,
                "X-Tradera-AppKey": self.app_key,
            },
            timeout=20,
        )
        resp.raise_for_status()
        return resp.json()

    def parse(self, html: str) -> list[Listing]:
        raise NotImplementedError("Use parse_json(), not parse() -- see fetch_json().")

    def parse_json(self, data: dict) -> list[Listing]:
        """Best-guess field names, unverified -- fix against a real
        response before trusting this output."""
        listings: list[Listing] = []
        for item in data.get("items", []):
            title = item.get("shortDescription") or item.get("title", "")
            price = item.get("buyItNowPrice") or item.get("currentBid")
            if not title or price is None:
                continue
            listings.append(
                Listing(
                    title=title,
                    url=item.get("itemUrl") or item.get("url", ""),
                    source=self.name,
                    raw_price_sek=float(price),
                    product_id=str(item.get("id", "")),
                )
            )
        return listings

    def scan(self) -> list[Listing]:  # override: uses JSON, not HTML
        return self.parse_json(self.fetch_json())
