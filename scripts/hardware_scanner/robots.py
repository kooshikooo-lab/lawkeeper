"""Real robots.txt compliance -- the gap the earlier Duck.ai-drafted
scanner had: it named "respect robots.txt" as a principle but the actual
code never checked it.

**Real, live-tested finding, 2026-08-21: robotparser alone is not
sufficient.** Testing this module against the real sites found two
separate failure modes standard parsing can't catch:
1. Blocket's prohibition ("Crawling blocket.se is prohibited unless you
   have written permission") is stated as a plain-English *comment* in
   robots.txt, not a machine-parseable Disallow rule -- no robots.txt
   parser, including Python's stdlib one, can act on prose.
2. Python's stdlib `urllib.robotparser` does not reliably match wildcard
   Disallow patterns -- confirmed live: `can_fetch()` returned True for
   `tradera.com/search?q=...` despite Tradera's robots.txt explicitly
   stating `Disallow: /search?*`.

Because of both, this module checks a hardcoded, manually-verified
deny-list FIRST -- it cannot be bypassed by a parser limitation the way
relying on robotparser() alone would have been. The robotparser check
still runs as a second, generic layer for sites not on the explicit list.
"""
from __future__ import annotations

import urllib.robotparser
from urllib.parse import urlparse

import requests

_USER_AGENT = "Mozilla/5.0 (compatible; hardware-scanner/1.0; personal use)"

# Manually verified 2026-08-21 by reading the actual robots.txt files,
# not by trusting automated parsing -- see module docstring for why.
_HARD_DENY_DOMAINS = {
    "blocket.se",
    "www.blocket.se",
}
_HARD_DENY_PATH_PREFIXES: dict[str, tuple[str, ...]] = {
    "www.tradera.com": ("/search",),
    "tradera.com": ("/search",),
}

_cache: dict[str, urllib.robotparser.RobotFileParser] = {}


def _parser_for(url: str) -> urllib.robotparser.RobotFileParser:
    """Fetches robots.txt ourselves and feeds it to RobotFileParser.parse()
    rather than calling rp.read(). Real bug found live 2026-08-21:
    RobotFileParser.read() can't be given a custom User-Agent -- it
    always uses urllib's bare default, and inet.se's bot-protection
    returns a plain 403 to that specific UA (confirmed: curl with a real
    UA gets 200 and the real rules; urllib.request's default gets 403).
    RobotFileParser silently treats a 4xx robots.txt fetch as "disallow
    everything," which made this module wrongly block a site that
    actually permits properly-identified fetches. Fetching with the same
    UA the rest of this tool uses, then parsing that content directly,
    avoids the whole failure mode."""
    parsed = urlparse(url)
    origin = f"{parsed.scheme}://{parsed.netloc}"
    if origin not in _cache:
        rp = urllib.robotparser.RobotFileParser()
        try:
            resp = requests.get(
                origin + "/robots.txt", headers={"User-Agent": _USER_AGENT}, timeout=10
            )
            if resp.status_code >= 400:
                rp.disallow_all = True
            else:
                rp.parse(resp.text.splitlines())
        except Exception:
            rp.disallow_all = True  # fail closed on real network errors
        _cache[origin] = rp
    return _cache[origin]


def allowed(url: str) -> bool:
    """True if this URL is permitted to fetch. Fails closed on any
    error or ambiguity, since this fetches other people's sites
    unattended -- the safer default is "don't fetch", not "assume yes"."""
    parsed = urlparse(url)
    host = parsed.netloc.lower()

    if host in _HARD_DENY_DOMAINS:
        return False
    for deny_host, prefixes in _HARD_DENY_PATH_PREFIXES.items():
        if host == deny_host and any(parsed.path.startswith(p) for p in prefixes):
            return False

    try:
        return _parser_for(url).can_fetch(_USER_AGENT, url)
    except Exception:
        return False
