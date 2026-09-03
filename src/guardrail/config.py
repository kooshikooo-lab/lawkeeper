"""Configuration for guard_branch.py's branch-governance checks.

Reads `.guardrail.json` (created by `lawkeeper init`) for machine names and
canonical branches. Defaults work for a two-machine team with a clean `main`
trunk, so non-coders can adopt it with zero configuration.

This dataclass used to also declare placement_rules, regenerable_suffixes,
regenerable_paths, governance_files, feature_prefix, and merge_prefix — a
second, unused copy of policy that validate_pre_commit.py, scan_config.py,
and guard_governance.py each already implement (and actually read) on their
own, hardcoded, with no connection to this class. Nothing in this repo ever
read those six fields — not even this class's own methods, which hardcode
their patterns directly rather than using self.feature_prefix/merge_prefix.
A governance tool declaring rules it never enforces is worse than declaring
none: it reads as documentation of real, checked behavior and isn't. Trimmed
to the two fields (machines, canonical_branches) something actually loads
and uses. If placement/regenerable/governance-file policy becomes genuinely
configurable later, it should replace the *hardcoded* copies in those other
files, not add a third parallel one here.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

DEFAULTS: dict = {
    "machines": ["desktop", "laptop"],
    "canonical_branches": ["main"],
}


@dataclass
class Config:
    machines: list[str] = field(default_factory=lambda: ["desktop", "laptop"])
    canonical_branches: list[str] = field(default_factory=lambda: ["main"])

    @classmethod
    def load(cls, repo_root: Path) -> "Config":
        path = repo_root / ".guardrail.json"
        data = DEFAULTS.copy()
        if path.exists():
            try:
                data.update(json.loads(path.read_text(encoding="utf-8")))
            except (OSError, ValueError):
                # Malformed config is itself a compliance failure — fall back
                # to defaults but let the audit flag it.
                pass
        return cls(
            machines=list(data["machines"]),
            canonical_branches=list(data["canonical_branches"]),
        )

    def canonical_branch_names(self) -> set[str]:
        names = set(self.canonical_branches)
        for m in self.machines:
            names.add(f"opencode/main/{m}")
        return names

    def feature_regexes(self) -> list:
        import re
        return [re.compile(rf"^opencode/[a-z0-9-]+/(?:{'|'.join(self.machines)})$")]
