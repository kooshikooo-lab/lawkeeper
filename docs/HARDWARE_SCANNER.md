# hardware_scanner

A real, working used/discounted-GPU price watcher, built 2026-08-21.
Replaces an earlier Duck.ai-drafted sketch that named principles
("respect robots.txt", "use Playwright for JS-heavy pages") without
actually implementing them.

## Usage

```bash
pip install -e ".[dev]"   # requests + beautifulsoup4
python -m hardware_scanner.scanner --min-score 20 --db hardware_listings.db
```

## What's real and working

- **inet.se** (Fyndhornan/bargain corner) -- open-box/return clearance.
  Real, tested adapter.
- **refurbed.se** (grafikkort category) -- refurbished stock, 12-month
  warranty. Real, tested adapter.

## What's excluded, and why (checked live, not assumed)

- **Blocket** -- robots.txt states in plain language "Crawling
  blocket.se is prohibited unless you have written permission." Not a
  technical rule to route around.
- **Tradera** -- robots.txt explicitly disallows `/search?*`, the exact
  path needed; the search page is also JS-rendered anyway (Next.js
  SPA), so a simple scraper wouldn't have worked even without the
  policy. A real, official REST API exists instead
  (`adapters/tradera.py`) -- it's a scaffold requiring the user's own
  developer credentials from api.tradera.com, not yet verified against
  a real response.
- **netonnet.se, elgiganten.se** -- both sit behind bot-challenge
  protection that blocks even a plain robots.txt fetch.

## Real bugs found and fixed during build (see AI_FAILURE_PATTERNS.md-style detail in each module's own comments)

1. An unbounded price regex spanned a title's own digits into a price
   match (`"...5000   9 915 kr"` parsed as `50009915.0`). Fixed with a
   proper Swedish thousands-grouping-shaped pattern.
2. Python's stdlib `robotparser` doesn't reliably match wildcard
   `Disallow` rules -- confirmed live it returned `True` for a path
   Tradera's own robots.txt explicitly disallows. Fixed with an
   explicit, manually-verified hardcoded deny-list checked first.
3. `requests` misdetected inet.se's response encoding as ISO-8859-1
   instead of the real UTF-8, silently garbling the price separator and
   zeroing out every parsed listing (60 -> 0). Fixed by forcing UTF-8 in
   `fetch_html()`.

## Known limitation

inet.se and refurbed.se are retailer clearance sections, not
peer-to-peer marketplaces -- they can't catch the "seller doesn't know
what it's worth" opportunity that motivated this tool. That needs
Tradera's API finished (real credentials + response verification) or
manual Blocket browsing.
