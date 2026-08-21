"""Adapter contract. Each real source implements fetch_html() (network,
thin) and parse(html) (pure function, real unit-testable against a saved
fixture -- this split is what makes the tests offline and fast instead
of hitting the live network every run)."""
from __future__ import annotations

from abc import ABC, abstractmethod

import requests

from ..models import Listing
from ..robots import allowed

_USER_AGENT = "Mozilla/5.0 (compatible; hardware-scanner/1.0; personal use)"


class Adapter(ABC):
    name: str
    url: str

    @abstractmethod
    def parse(self, html: str) -> list[Listing]:
        """Pure function: HTML in, listings out. No network. This is
        what tests exercise directly against saved fixtures."""

    def fetch_html(self) -> str:
        """Real robots.txt check happens here, every call -- not
        optional, not something a caller can forget."""
        if not allowed(self.url):
            raise PermissionError(
                f"{self.name}: robots.txt disallows {self.url} -- not fetching"
            )
        resp = requests.get(self.url, headers={"User-Agent": _USER_AGENT}, timeout=20)
        resp.raise_for_status()
        # Real bug found live 2026-08-21: `requests` auto-detects encoding
        # from headers when the server doesn't send an explicit charset,
        # and inet.se's response got misdetected as ISO-8859-1 instead of
        # its real UTF-8 -- resp.text then decoded a non-breaking-space
        # price separator into a garbled replacement character (U+FFFD),
        # silently breaking every price parse (confirmed: text came back
        # as '7�\xa0999�\xa0kr' instead of a clean '7\xa0999 kr').
        # requests' own apparent_encoding (chardet-based) got it right;
        # forcing utf-8 here is even more direct, since every real source
        # this tool targets (Swedish retailers, real åäö content) is
        # UTF-8 in practice.
        resp.encoding = "utf-8"
        return resp.text

    def scan(self) -> list[Listing]:
        return self.parse(self.fetch_html())
