#!/usr/bin/env python3
"""CLI entry point: run the real, working adapters, score results,
store new ones, print alerts above threshold.

Usage:
    python -m hardware_scanner.scanner
    python -m hardware_scanner.scanner --min-score 20 --db listings.db
"""
from __future__ import annotations

import argparse

from .adapters.inet import InetFyndhornanAdapter
from .adapters.refurbed import RefurbedGrafikkortAdapter
from .scoring import score
from .storage import init_db, save_new

# Tradera intentionally excluded from the default source list -- it
# needs the user's own API credentials (see adapters/tradera.py) and
# hasn't been verified against a real response yet.
DEFAULT_ADAPTERS = [InetFyndhornanAdapter, RefurbedGrafikkortAdapter]


def run(min_score: float, db_path: str) -> None:
    init_db(db_path)
    for adapter_cls in DEFAULT_ADAPTERS:
        adapter = adapter_cls()
        try:
            listings = adapter.scan()
        except PermissionError as e:
            print(f"SKIPPED [{adapter.name}]: {e}")
            continue
        except Exception as e:
            print(f"ERROR [{adapter.name}]: {e}")
            continue

        print(f"{adapter.name}: {len(listings)} listings found")
        for listing in listings:
            score(listing)
            is_new = save_new(db_path, listing)
            if is_new and listing.score >= min_score:
                print(
                    f"ALERT | score={listing.score:.1f} | "
                    f"{listing.raw_price_sek:.0f} kr | {listing.title} | {listing.url}"
                )
                if listing.score_reasons:
                    print(f"       reasons: {'; '.join(listing.score_reasons)}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Real, robots.txt-respecting hardware deal scanner")
    parser.add_argument("--min-score", type=float, default=15.0)
    parser.add_argument("--db", default="hardware_listings.db")
    args = parser.parse_args()
    run(args.min_score, args.db)


if __name__ == "__main__":
    main()
