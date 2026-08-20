"""Concrete MemoryProvider wrapping the AI_FAILURE_PATTERNS.md corpus.

Reuses scripts/mine_failure_patterns.py's existing corpus collection and
FailureRecord format (Law 3: never duplicate) rather than re-parsing
AI_FAILURE_PATTERNS.md from scratch. Adds the one thing that script does
not do: relevance-scored retrieval keyed on an incoming query, so a turn
gets only the failure records that are actually relevant to it instead of
requiring a human (or agent) to open and read the whole file.
"""

from __future__ import annotations

import importlib.util
import math
import re
import subprocess
import sys
from pathlib import Path

from .provider import MemoryEntry, MemoryProvider


def _repo_root() -> Path:
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        cwd=Path(__file__).resolve().parent,
    )
    root = result.stdout.strip()
    return Path(root) if root else Path(__file__).resolve().parents[3]


def _load_miner():
    """Import scripts/mine_failure_patterns.py (not a package -- same
    load-by-path technique tests/conftest.py already uses for this repo).

    Registers the module in sys.modules under its own name before
    executing it -- without this, dataclasses.fields()-style introspection
    on FailureRecord fails (Python looks the module up by __module__ via
    sys.modules to resolve string type annotations; a module loaded via
    module_from_spec but never registered isn't found there, so the
    lookup returns None and crashes). Found by actually running the
    tests below, not assumed safe because tests/conftest.py's load_script
    happened to work for scripts without dataclasses.
    """
    path = _repo_root() / "scripts" / "mine_failure_patterns.py"
    spec = importlib.util.spec_from_file_location("guardrail_memory_miner", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _tokenize(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9_]+", text.lower()))


def _compute_idf(record_token_sets: list[set[str]]) -> dict[str, float]:
    """Inverse document frequency per token, over this corpus (one 'document'
    = one failure record). Standard smoothed IDF: log(N / df) + 1, so even a
    word appearing in every record still gets a small positive weight rather
    than zero."""
    n = len(record_token_sets)
    if n == 0:
        return {}
    doc_freq: dict[str, int] = {}
    for tokens in record_token_sets:
        for t in tokens:
            doc_freq[t] = doc_freq.get(t, 0) + 1
    return {t: math.log(n / df) + 1.0 for t, df in doc_freq.items()}


class FailurePatternMemoryProvider(MemoryProvider):
    """Retrieves relevant AI_FAILURE_PATTERNS.md entries for a query.

    Relevance is deliberately simple (token-overlap fraction of the query)
    rather than an embedding model, because this corpus is small (dozens
    of records, not millions) and the entries are short, dense, hand-
    written prose -- keyword overlap on a query like "headless dispatch
    permission wall" already finds the right entry. A different provider
    could swap in real embeddings later without changing this interface.
    """

    def __init__(self) -> None:
        self._corpus: list = []
        self._record_tokens: list[set[str]] = []
        self._idf: dict[str, float] = {}
        self._initialized = False

    def initialize(self) -> None:
        miner = _load_miner()
        self._corpus = miner.collect_corpus()
        self._record_tokens = [
            _tokenize(" ".join([
                r.law_or_theme, r.title, r.problem, r.root_cause, r.fix, r.theme,
            ]))
            for r in self._corpus
        ]
        self._idf = _compute_idf(self._record_tokens)
        self._initialized = True

    def prefetch(self, query: str, limit: int = 5) -> list[MemoryEntry]:
        if not self._initialized:
            self.initialize()
        query_tokens = _tokenize(query)
        if not query_tokens:
            return []
        scored: list[tuple[float, object]] = []
        for record, record_tokens in zip(self._corpus, self._record_tokens):
            overlap = query_tokens & record_tokens
            if not overlap:
                continue
            # TF-IDF-style weighting, not raw overlap count: three scoring
            # schemes were tried and each failed an actual test before
            # this one, not assumed correct in advance.
            # overlap/len(query) favored long records (more vocabulary,
            # more chances to share *any* word); Jaccard (overlap/union)
            # swung the other way and favored thin/near-empty records (a
            # tiny union inflates the ratio); raw overlap count favored
            # long records again, for the same reason as the first case,
            # because it still treats every shared word as equally
            # meaningful. This corpus is entirely about failures/causes/
            # fixes, so generic words like "fix" or "cause" appear in
            # nearly every entry and carry almost no distinguishing
            # information -- while a specific term like
            # "external_directory" appears in one entry and is exactly
            # what should drive the match. Weighting each shared word by
            # its inverse document frequency (rare across the corpus =
            # high weight, common = low weight) fixes this directly.
            scored.append((sum(self._idf[t] for t in overlap), record))
        scored.sort(key=lambda pair: pair[0], reverse=True)
        return [
            MemoryEntry(
                id=f"{record.repo}:{record.id}",
                text=f"[{record.law_or_theme}] {record.problem} "
                     f"/ Root cause: {record.root_cause} / Fix: {record.fix}",
                source=record.repo,
                relevance=relevance,
            )
            for relevance, record in scored[:limit]
        ]
