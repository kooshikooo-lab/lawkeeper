"""Interactive checkbox-choice protocol.

Present a list of options with checkboxes; let the user toggle multiple picks;
enforce conflict groups (mutually exclusive options); optionally capture a free-
text "other" answer. Portable to Windows/powershell (line-based, no curses).

Example:
    from guardrail.choices import Choice, ask
    result = ask(
        "Pick models",
        "Select one or more:",
        [Choice("1", "Opus"), Choice("2", "Haiku", conflicts=("1",)),
         Choice("o", "Other", custom=True)],
        input_lines=["1", "done"],
    )
    # -> ChoiceResult(selected=["1"], custom=None, cancelled=False)
"""
from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Choice:
    id: str
    text: str
    conflicts: tuple = ()
    custom: bool = False


@dataclass
class ChoiceResult:
    selected: list[str]
    custom: str | None = None
    cancelled: bool = False


def conflicts_violations(choices: list[Choice], selected) -> list[str]:
    """Return human strings for conflict pairs currently violated."""
    by_id = {c.id: c for c in choices}
    out = []
    seen = set()
    sel = set(selected)
    for cid in sel:
        c = by_id.get(cid)
        if not c:
            continue
        for other in c.conflicts:
            if other not in sel:
                continue
            pair = tuple(sorted((cid, other)))
            if pair in seen:
                continue
            seen.add(pair)
            a = by_id.get(cid, Choice(cid, cid))
            b = by_id.get(other, Choice(other, other))
            out.append(f"'{a.text}' vs '{b.text}'")
    return out


def resolve_token(token: str, choices: list[Choice]) -> str | None:
    """Match a user token: exact id, or 1-based position -> id."""
    token = token.strip()
    if token in {c.id for c in choices}:
        return token
    try:
        idx = int(token)
    except ValueError:
        return None
    if 1 <= idx <= len(choices):
        return choices[idx - 1].id
    return None


def validate(choices: list[Choice], selected=None, custom: str | None = None) -> ChoiceResult:
    """Pure, non-interactive validation. Checks conflicts only."""
    selected = list(dict.fromkeys(selected or []))
    violations = conflicts_violations(choices, selected)
    if violations:
        return ChoiceResult(selected, custom, cancelled=True)
    return ChoiceResult(selected, custom, cancelled=False)


def _render(out, title, body, choices, selected, custom, custom_id, prompt):
    out.write("\n")
    if title:
        out.write(f"{title}\n")
    if body:
        out.write(f"{body}\n")
    by_id = {c.id: c for c in choices}
    for i, c in enumerate(choices, 1):
        mark = "[x]" if c.id in selected else "[ ]"
        line = f"  {mark} {i}) {c.text}"
        if c.conflicts:
            line += f"  (conflicts: {', '.join(c.conflicts)})"
        if c.custom and c.id in selected and custom is not None:
            line += f"  [custom: {custom}]"
        out.write(line + "\n")
    out.write(prompt)
    out.flush()


def ask(title: str,
        body: str = "",
        choices: list[Choice] | None = None,
        input_lines: list[str] | None = None,
        out=None,
        multi: bool = True) -> ChoiceResult:
    """Interactive checkbox menu. `input_lines` drives the loop in tests.

    Tokens: an option id (or its 1-based number) to toggle; `custom: <text>`
    to set the free-text answer; `done`/blank to submit; `cancel` to abort.
    Mutually-exclusive selections block `done` until resolved.
    """
    choices = list(choices or [])
    out = out or sys.stdout
    stream = iter(input_lines) if input_lines is not None else sys.stdin
    selected: set[str] = set()
    custom = None
    custom_id = next((c.id for c in choices if c.custom), None)
    prompt = "Select (id/number), custom: <text>, done, or cancel: "

    while True:
        _render(out, title, body, choices, selected, custom, custom_id, prompt)
        try:
            raw = next(stream) if input_lines is not None else stream.readline()
        except StopIteration:
            return ChoiceResult(sorted(selected), custom, cancelled=True)
        line = raw.strip()
        if line in ("done", "", "enter", "submit"):
            violations = conflicts_violations(choices, selected)
            if violations:
                out.write("CONFLICT: pick only one of: " + "; ".join(violations) + "\n")
                continue
            return ChoiceResult(sorted(selected), custom, cancelled=False)
        if line in ("cancel", "quit", "exit"):
            return ChoiceResult(sorted(selected), custom, cancelled=True)
        if line.startswith("custom:"):
            custom = line.split(":", 1)[1].strip()
            if custom_id and custom_id not in selected:
                selected.add(custom_id)
            out.write(f"set custom = {custom}\n")
            continue
        if line in ("list", "show"):
            continue
        cid = resolve_token(line, choices)
        if cid is None:
            out.write(f"unknown option: {line!r}\n")
            continue
        if cid in selected:
            selected.discard(cid)
            if cid == custom_id:
                custom = None
        else:
            if not multi and selected:
                selected.clear()
            selected.add(cid)


def load_spec(path) -> dict:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return data


def spec_to_choices(spec: dict) -> list[Choice]:
    out = []
    for c in spec.get("choices", []):
        out.append(
            Choice(
                id=str(c["id"]),
                text=str(c.get("text", c["id"])),
                conflicts=tuple(c.get("conflicts", []) or []),
                custom=bool(c.get("custom", False)),
            )
        )
    return out
