#!/usr/bin/env python3
"""Phase 0 of ROADMAP.md: a way to actually try the memory-provider work
from the command line, tonight, instead of only importing it in Python.

Usage:
    python scripts/memory_query.py "some question or description"
    python scripts/memory_query.py "some question" --limit 3
"""

import argparse
import sys
from pathlib import Path

# Windows console default codepage (cp1252) can't encode the em-dashes this
# corpus's entries actually contain -- same failure class already logged in
# AI_FAILURE_PATTERNS.md (2026-08-19, LAW 18). Fix applied here before it
# was ever hit, not after -- found by actually running this script on
# Windows, not assumed safe.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

REPO_ROOT = Path(__file__).resolve().parent.parent
SRC = REPO_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from guardrail.memory import FailurePatternMemoryProvider  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("query", help="A question or description to search the failure-pattern corpus for")
    parser.add_argument("--limit", type=int, default=5, help="Max results (default 5)")
    args = parser.parse_args()

    provider = FailurePatternMemoryProvider()
    results = provider.prefetch(args.query, limit=args.limit)

    if not results:
        print(f"No relevant entries found for: {args.query!r}")
        return 0

    print(f"Top {len(results)} relevant entries for: {args.query!r}\n")
    for i, entry in enumerate(results, 1):
        print(f"{i}. [{entry.source}:{entry.id.split(':', 1)[-1]}] (relevance {entry.relevance:.1f})")
        print(f"   {entry.text}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
