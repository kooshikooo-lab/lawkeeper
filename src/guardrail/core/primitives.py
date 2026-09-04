"""Core law primitives: Status, CheckResult, and the Law abstract base class."""
from __future__ import annotations

import enum
from abc import ABC, abstractmethod
from dataclasses import dataclass, field


class Status(str, enum.Enum):
    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"


@dataclass
class CheckResult:
    law_id: int
    status: Status
    message: str
    details: dict = field(default_factory=dict)

    @property
    def is_failure(self) -> bool:
        return self.status == Status.FAIL


class Law(ABC):
    law_id: int
    title: str
    severity: str = "must"

    @property
    @abstractmethod
    def description(self) -> str: ...

    @abstractmethod
    def check(self, repo_root, config) -> list[CheckResult]: ...

    def run(self, repo_root, config) -> list[CheckResult]:
        try:
            return list(self.check(repo_root, config))
        except Exception as exc:
            return [
                CheckResult(
                    self.law_id,
                    Status.FAIL,
                    f"guard error: {type(exc).__name__}: {exc}",
                    {"error": True},
                )
            ]
