"""hardware_scanner: a real, robots.txt-respecting used/discounted-hardware
price watcher, built 2026-08-21 to replace an earlier Duck.ai-drafted
sketch that claimed principles ("respect robots.txt", "use Playwright for
JS-heavy pages") it never actually implemented.

Real, checked-live source decisions (not assumed):
- Tradera: excluded from scraping -- robots.txt explicitly disallows
  `/search?*`, the exact path this tool needs. A real, official REST API
  (api.tradera.com, SearchService) exists instead -- see
  adapters/tradera.py, which is a scaffold requiring the user's own
  developer credentials, not yet live-verified against real responses.
- Blocket: fully excluded -- robots.txt states in plain language
  "Crawling blocket.se is prohibited unless you have written permission."
  Not a technical rule to route around; a stated policy.
- netonnet.se / elgiganten.se: excluded -- both sit behind bot-challenge
  protection that blocks even a plain robots.txt fetch.
- inet.se, refurbed.se: real, working adapters -- robots.txt permits
  them, both are server-rendered (confirmed via plain HTTP fetch, no
  Playwright needed), and their real DOM structure was inspected live
  before writing any selector.
"""
