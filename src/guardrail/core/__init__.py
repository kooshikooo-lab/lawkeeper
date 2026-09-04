"""guardrail.core — law primitives, registry, and runner.

    from guardrail.core import CheckResult, Law, Status

"""
from __future__ import annotations

from .primitives import CheckResult, Law, Status
from .registry import load_law_classes, load_laws
from .runner import GuardrailRunner, Report

__all__ = [
    "CheckResult",
    "Law",
    "Status",
    "load_law_classes",
    "load_laws",
    "GuardrailRunner",
    "Report",
]
