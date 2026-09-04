"""Law discovery: auto-load Law subclasses from guardrail.laws."""
from __future__ import annotations

import importlib
import pkgutil

from .primitives import Law

LAWS_PACKAGE = "guardrail.laws"


def load_law_classes() -> dict[int, type[Law]]:
    package = importlib.import_module(LAWS_PACKAGE)
    cls_by_id: dict[int, type[Law]] = {}
    for info in pkgutil.iter_modules(package.__path__):
        if info.name.startswith("_"):
            continue
        module = importlib.import_module(f"{LAWS_PACKAGE}.{info.name}")
        for obj in vars(module).values():
            if (
                isinstance(obj, type)
                and issubclass(obj, Law)
                and obj is not Law
                and getattr(obj, "law_id", None) is not None
            ):
                cls_by_id[int(obj.law_id)] = obj
    return cls_by_id


def load_laws() -> list[Law]:
    classes = load_law_classes()
    return [cls() for cls in sorted(classes.values(), key=lambda c: c.law_id)]
