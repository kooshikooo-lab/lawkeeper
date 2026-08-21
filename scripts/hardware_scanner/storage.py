"""Real SQLite persistence with dedup by (source, product_id, url) --
so repeated scans don't re-alert on the same listing every run."""
from __future__ import annotations

import sqlite3
import time
from pathlib import Path

from .models import Listing

_SCHEMA = """
CREATE TABLE IF NOT EXISTS listings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL,
    product_id TEXT,
    title TEXT NOT NULL,
    url TEXT NOT NULL,
    raw_price_sek REAL NOT NULL,
    original_price_sek REAL,
    condition_note TEXT,
    shipping_sek REAL,
    total_cost_sek REAL,
    score REAL,
    score_reasons TEXT,
    first_seen_at INTEGER NOT NULL,
    UNIQUE(source, url)
)
"""


def init_db(db_path: str) -> None:
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(_SCHEMA)
        conn.commit()
    finally:
        conn.close()


def save_new(db_path: str, listing: Listing) -> bool:
    """Returns True if this listing is genuinely new (inserted), False
    if it's a duplicate of one already stored -- callers should only
    alert on True."""
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.execute(
            "SELECT 1 FROM listings WHERE source = ? AND url = ?",
            (listing.source, listing.url),
        )
        if cur.fetchone() is not None:
            return False
        conn.execute(
            """INSERT INTO listings
               (source, product_id, title, url, raw_price_sek,
                original_price_sek, condition_note, shipping_sek,
                total_cost_sek, score, score_reasons, first_seen_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                listing.source,
                listing.product_id,
                listing.title,
                listing.url,
                listing.raw_price_sek,
                listing.original_price_sek,
                listing.condition_note,
                listing.shipping_sek,
                listing.total_cost_sek,
                listing.score,
                "; ".join(listing.score_reasons),
                int(time.time()),
            ),
        )
        conn.commit()
        return True
    finally:
        conn.close()
