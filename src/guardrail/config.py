"""Configuration for the guardrail enforcement system.

Guard scripts are project-agnostic: they read `.guardrail.json` (created by
`guardrail init`) for machine names, canonical branches, placement rules, and
artifact policies. Defaults work for a two-machine team with a clean `main`
trunk, so non-coders can adopt it with zero configuration.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

DEFAULTS: dict = {
    "project_name": "my-project",
    "machines": ["desktop", "laptop"],
    "canonical_branches": ["main"],
    # Changed 2026-09-04 from "opencode/{topic}/{machine}": that prefix
    # named the tool (OpenCode) that was the primary agent when this
    # convention was set, not a generic namespace -- and now misattributes
    # work done by whatever tool replaced it (an OpenCode subscription
    # ending is what surfaced this). "agent/" is tool-agnostic on purpose
    # so this doesn't need to change again next time the primary tool
    # does. feature_regexes() below always additionally accepts the
    # legacy "opencode/{topic}/{machine}" pattern too, so branches already
    # created under the old convention are never retroactively flagged as
    # orphans -- this changes what NEW branches should be named, not what
    # already exists. Canonical/main-mirror branches (opencode/main/<machine>)
    # are deliberately NOT renamed by this change -- see canonical_branch_names()
    # below, and Windwright's AI_CONSTITUTION.md Law 15, which treats those
    # as permanent and requiring explicit human approval to ever rename.
    "feature_prefix": "agent/{topic}/{machine}",
    "merge_prefix": "merge/{topic}",
    "placement_rules": {
        "backend/": {".py"},
        "tests/": {".py"},
        "scripts/": {".py", ".ps1", ".sh", ".bat"},
        "docs/": {".md", ".txt"},
    },
    "regenerable_suffixes": [
        ".stl", ".step", ".stp", ".obj", ".ply", ".3mf",
        ".json", ".jsonl", ".dat", ".log", ".txt",
        ".png", ".jpg", ".jpeg", ".svg",
    ],
    "regenerable_paths": ["test_output/", "designs/", "chat-logs/", "wiki/"],
    "governance_files": [
        "docs/AI_CONSTITUTION.md",
        "docs/CONSTRAINTS_AND_PREFERENCES.md",
        "docs/COMPLIANCE_CHECK.md",
        "docs/ARCHITECTURE_DECISIONS.md",
        "docs/AI_FAILURE_PATTERNS.md",
        "docs/REMINDERS.md",
        "docs/TEST_THEORY.md",
        "AGENTS.md",
    ],
    "show_internal_reasoning": False,
    "reasoning_log": "docs/reasoning.log",
}


@dataclass
class Config:
    project_name: str = "my-project"
    machines: list[str] = field(default_factory=lambda: ["desktop", "laptop"])
    canonical_branches: list[str] = field(default_factory=lambda: ["main"])
    feature_prefix: str = "agent/{topic}/{machine}"
    merge_prefix: str = "merge/{topic}"
    placement_rules: dict = field(default_factory=dict)
    regenerable_suffixes: list[str] = field(default_factory=list)
    regenerable_paths: list[str] = field(default_factory=list)
    governance_files: list[str] = field(default_factory=list)
    show_internal_reasoning: bool = False
    reasoning_log: str = "docs/reasoning.log"

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
            project_name=data["project_name"],
            machines=list(data["machines"]),
            canonical_branches=list(data["canonical_branches"]),
            feature_prefix=data["feature_prefix"],
            merge_prefix=data["merge_prefix"],
            placement_rules={k: set(v) for k, v in data["placement_rules"].items()},
            regenerable_suffixes=list(data["regenerable_suffixes"]),
            regenerable_paths=list(data["regenerable_paths"]),
            governance_files=list(data["governance_files"]),
            show_internal_reasoning=bool(data["show_internal_reasoning"]),
            reasoning_log=data["reasoning_log"],
        )

    def canonical_branch_names(self) -> set[str]:
        names = set(self.canonical_branches)
        for m in self.machines:
            names.add(f"opencode/main/{m}")
        return names

    def feature_regexes(self) -> list:
        """Regexes accepted for a feature/topic branch name.

        Real bug found 2026-09-04, not by inspection but while tracing why
        a config-level `feature_prefix` field existed but branch naming
        never actually changed when it was edited: this method hardcoded
        the "opencode/..." pattern directly instead of deriving it from
        `self.feature_prefix` -- the field was decorative, not load-bearing.
        Now genuinely derived from config, with the pre-2026-09-04 default
        ("opencode/{topic}/{machine}") always additionally accepted so
        branches created before this fix are never retroactively flagged
        as orphans.
        """
        import re

        machines_alt = "|".join(re.escape(m) for m in self.machines)

        def _prefix_to_regex(prefix: str) -> "re.Pattern[str]":
            # Escape the whole template first so a config-supplied prefix
            # can't inject regex metacharacters, then swap the two known
            # placeholders back in as their intended patterns.
            pattern = re.escape(prefix)
            pattern = pattern.replace(re.escape("{topic}"), "[a-z0-9-]+")
            pattern = pattern.replace(re.escape("{machine}"), f"(?:{machines_alt})")
            return re.compile(f"^{pattern}$")

        regexes = [_prefix_to_regex(self.feature_prefix)]
        legacy = _prefix_to_regex("opencode/{topic}/{machine}")
        if legacy.pattern not in {r.pattern for r in regexes}:
            regexes.append(legacy)
        return regexes
