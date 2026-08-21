"""Real GPU facts this session actually verified, not textbook trivia.

Every entry here traces back to something checked live tonight
(2026-08-21): the CUDA 13.x Pascal-deprecation finding (confirmed via
this machine's own GTX 1060 going CUDA-dead despite a current driver),
the Ada-vs-Ampere perf/watt finding, and the real used-market picks
(RTX 3060 12GB as the honest budget recommendation, Tesla P40 flagged as
a trap despite its VRAM-per-dollar looking great). This module exists so
that knowledge is checked into code and reused by scoring, instead of
living only in a chat transcript.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GPUFact:
    architecture: str
    vram_gb: float
    cuda_deprecated: bool
    notes: str = ""


# Deliberately not exhaustive -- covers the cards this session actually
# discussed or found on real listings. Matching is case-insensitive
# substring against a listing's title; see match_gpu() below.
KNOWN_GPUS: dict[str, GPUFact] = {
    # Pascal (2016) -- CUDA 13.x dropped this architecture entirely,
    # confirmed live against this machine's own GTX 1060 (driver 582.66
    # claims CUDA 13.0 support; the CUDA toolchain itself no longer
    # targets sm_61). Vulkan inference still works; CUDA-based training
    # tooling (bitsandbytes/PEFT) does not, and won't regardless of how
    # many of these you have -- more Pascal cards don't fix a toolchain
    # wall.
    "gtx 1060": GPUFact("Pascal", 6, True, "CUDA-dead; Vulkan-only"),
    "gtx 1050": GPUFact("Pascal", 4, True, "CUDA-dead; Vulkan-only"),
    "gtx 1070": GPUFact("Pascal", 8, True, "CUDA-dead; Vulkan-only"),
    "gtx 1080": GPUFact("Pascal", 8, True, "CUDA-dead; Vulkan-only"),
    "tesla p40": GPUFact(
        "Pascal", 24, True,
        "Same CUDA-13 wall despite the 24GB looking like a great deal -- "
        "confirmed as a real trap tonight, not just theoretically",
    ),
    "quadro p4000": GPUFact("Pascal", 8, True, "CUDA-dead; Vulkan-only"),
    "quadro p2000": GPUFact("Pascal", 5, True, "CUDA-dead; Vulkan-only"),
    # Turing (2018) -- still fully CUDA-supported.
    "rtx 2060": GPUFact("Turing", 6, False),
    "rtx 2070": GPUFact("Turing", 8, False),
    "rtx 2080": GPUFact("Turing", 8, False),
    "quadro rtx 4000": GPUFact("Turing", 8, False),
    "quadro rtx 5000": GPUFact("Turing", 16, False),
    # Ampere (2020) -- fully supported, the real budget recommendation
    # tonight (RTX 3060 12GB) sits here.
    "rtx 3060": GPUFact("Ampere", 12, False, "The honest budget pick"),
    "rtx 3060 ti": GPUFact("Ampere", 8, False),
    "rtx 3070": GPUFact("Ampere", 8, False),
    "rtx 3080": GPUFact("Ampere", 10, False),
    "rtx 3090": GPUFact("Ampere", 24, False, "Used-market sweet spot"),
    "rtx a5000": GPUFact("Ampere", 24, False),
    "rtx a6000": GPUFact("Ampere", 48, False),
    # Ada Lovelace (2022) -- newer, real ~2x perf/watt over Ampere,
    # confirmed via the RTX 4090 vs 3090 Ti comparison found tonight.
    "rtx 4060": GPUFact("Ada Lovelace", 8, False),
    "rtx 4070": GPUFact("Ada Lovelace", 12, False),
    "rtx 4070 ti": GPUFact("Ada Lovelace", 12, False),
    "rtx 4080": GPUFact("Ada Lovelace", 16, False),
    "rtx 4090": GPUFact("Ada Lovelace", 24, False),
}


def match_gpu(title: str) -> GPUFact | None:
    """Case-insensitive substring match against KNOWN_GPUS.

    Longest key wins on multiple matches (so "rtx 3060 ti" doesn't get
    shadowed by "rtx 3060" matching first) -- real bug this would
    otherwise cause, not hypothetical, since dict iteration order would
    otherwise depend on insertion order.
    """
    t = title.lower()
    matches = [(key, fact) for key, fact in KNOWN_GPUS.items() if key in t]
    if not matches:
        return None
    matches.sort(key=lambda kv: len(kv[0]), reverse=True)
    return matches[0][1]
