"""Real data model for a hardware listing -- shared by every adapter."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Listing:
    """One real listing from one real source.

    `raw_price_sek` is the price as the source states it, before any
    shipping/locality adjustment. `condition_note` carries whatever the
    source itself says about condition (e.g. inet.se's "Fyndvara: ..."
    text) -- not inferred, just carried through.
    """
    title: str
    url: str
    source: str
    raw_price_sek: float
    condition_note: str = ""
    original_price_sek: float | None = None
    product_id: str = ""

    # Filled in by scoring.py, not the adapter -- an adapter only knows
    # what the page says, not how good a deal it is.
    shipping_sek: float = 0.0
    total_cost_sek: float = 0.0
    score: float = 0.0
    score_reasons: list[str] = field(default_factory=list)
