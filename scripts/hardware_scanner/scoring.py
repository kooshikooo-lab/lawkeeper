"""Real scoring, built on tonight's actual findings rather than generic
heuristics. Highest-leverage rule: a Pascal-architecture card is
penalized hard regardless of its VRAM/price ratio -- a Tesla P40's 24GB
for ~$239 *looks* like the best deal on paper and is a real, confirmed
trap (same CUDA-13 deprecation wall as this machine's own GTX 1060).
"""
from __future__ import annotations

from .gpu_knowledge import match_gpu
from .models import Listing

# Sweden/Gothenburg-specific shipping estimate when a listing doesn't
# state its own shipping cost -- same rough figures used in the earlier
# Duck.ai draft, kept since they're a reasonable default, not because
# they were independently re-verified tonight.
_SHIPPING_GUESS_SEK = 80.0
_LOCAL_PICKUP_DISCOUNT_SEK = 60.0  # bonus for Gothenburg/pickup listings


def score(listing: Listing) -> Listing:
    """Mutates and returns the listing with score/score_reasons/
    shipping/total_cost filled in."""
    reasons: list[str] = []
    s = 0.0

    fact = match_gpu(listing.title)
    if fact is not None:
        s += fact.vram_gb * 2.0
        reasons.append(f"{fact.architecture}, {fact.vram_gb}GB VRAM (+{fact.vram_gb * 2.0:.0f})")
        if fact.cuda_deprecated:
            s -= 60.0
            reasons.append(
                f"CUDA-deprecated architecture ({fact.architecture}) -- "
                f"real risk, not just older hardware (-60)"
            )
        else:
            s += 10.0
            reasons.append("CUDA-supported architecture (+10)")

    text = f"{listing.title} {listing.condition_note}".lower()
    if "göteborg" in text or "gothenburg" in text or "gbg" in text:
        s += 15.0
        reasons.append("Gothenburg-local listing (+15)")
    if "pickup" in text or "avhämtning" in text:
        s += 5.0
        reasons.append("pickup available (+5)")

    if listing.original_price_sek and listing.original_price_sek > listing.raw_price_sek:
        discount_pct = 100.0 * (1 - listing.raw_price_sek / listing.original_price_sek)
        s += min(discount_pct, 40.0) * 0.5
        reasons.append(f"{discount_pct:.0f}% off stated original price")

    listing.shipping_sek = _SHIPPING_GUESS_SEK
    listing.total_cost_sek = round(listing.raw_price_sek + listing.shipping_sek, 2)
    listing.score = round(s, 2)
    listing.score_reasons = reasons
    return listing
