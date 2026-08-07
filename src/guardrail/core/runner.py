"""Guardrail runner: execute Laws against a repo, collect a Report."""
from __future__ import annotations

import dataclasses
import json
from pathlib import Path

from .primitives import CheckResult, Status
from .registry import load_laws


@dataclasses.dataclass
class Report:
    results: list[CheckResult]
    repo_root: Path

    @property
    def summary(self) -> dict[str, int]:
        counts = {s.value: 0 for s in Status}
        counts["total"] = 0
        for r in self.results:
            counts[r.status.value] = counts.get(r.status.value, 0) + 1
            counts["total"] += 1
        return counts

    @property
    def exit_code(self) -> int:
        return 1 if any(r.is_failure for r in self.results) else 0

    def failures(self) -> list[CheckResult]:
        return [r for r in self.results if r.is_failure]

    def to_dict(self) -> dict:
        return {
            "repo": str(self.repo_root),
            "summary": self.summary,
            "results": [
                {
                    "law_id": r.law_id,
                    "status": r.status.value,
                    "message": r.message,
                    "details": r.details,
                }
                for r in self.results
            ],
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)


class GuardrailRunner:
    def __init__(self, repo_root: Path | None = None, config=None) -> None:
        self.repo_root = Path(repo_root) if repo_root else Path.cwd()
        self.config = config or self._load_config()

    def _load_config(self):
        from ..config import Config

        return Config.load(self.repo_root)

    def run(self, only: set[int] | None = None) -> Report:
        results: list[CheckResult] = []
        for law in load_laws():
            if only and law.law_id not in only:
                continue
            results.extend(law.run(self.repo_root, self.config))
        return Report(results, self.repo_root)
