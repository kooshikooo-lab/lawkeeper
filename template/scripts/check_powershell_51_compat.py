"""PowerShell 5.1 compatibility lint.

Scans all .ps1 files for syntax/operators introduced in PowerShell 6/7 that
would fail on the Windows PowerShell 5.1 runtime. Exit code is non-zero if any
forbidden constructs are found.

Usage:
    python scripts/check_powershell_51_compat.py [path/to/file.ps1 ...]
"""
from __future__ import annotations

import argparse
import fnmatch
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Forbidden constructs and a short explanation.
FORBIDDEN: list[tuple[str, str]] = [
    # Pipeline chain operators
    (r"&&", "pipeline chain operator '&&' (PS7+)"),
    (r"\|\|", "pipeline chain operator '||' (PS7+)"),
    # Null coalescing / conditional operators
    (r"\?\?=", "null-coalescing assignment '??=' (PS7+)"),
    (r"\?\?", "null-coalescing operator '??' (PS7+)"),
    (r"\?\.", "null-conditional member access '?.' (PS7+)"),
    (r"\?\[", "null-conditional index '?[]' (PS7+)"),
    # Ternary operator is hard to distinguish from existing syntax without a
    # real parser, so we only flag the most common pattern: <cond> ? <a> : <b>
    (r"\)\s*\?\s+[^:?]+\s+:\s+", "ternary operator '? :' (PS7+)"),
    (r"\$\w+\s*\?\s+[^:?]+\s+:\s+", "ternary operator '? :' (PS7+)"),
    # Other PS6+ features
    (r"-AsByteStream\b", "parameter '-AsByteStream' (PS6+; use -Encoding Byte in 5.1)"),
    (r"-LeafBase\b", "parameter '-LeafBase' (PS6+)"),
    (r"ForEach-Object\s+-Parallel\b", "ForEach-Object -Parallel (PS7+)"),
    (r"Get-Error\b", "cmdlet 'Get-Error' (PS7+)"),
]


def _strip_powershell_literals(text: str) -> str:
    """Remove comments, strings, and here-strings so we lint code only."""
    out: list[str] = []
    i = 0
    n = len(text)
    while i < n:
        ch = text[i]
        nxt = text[i + 1] if i + 1 < n else ""

        # Block comment <# ... #>
        if ch == "<" and nxt == "#":
            end = text.find("#>", i + 2)
            if end == -1:
                break
            # Preserve line structure so line numbers stay correct.
            block = text[i:end + 2]
            out.append(" " * len(block.replace("\n", " ")))
            i = end + 2
            continue

        # Line comment #...
        if ch == "#":
            line_end = text.find("\n", i)
            if line_end == -1:
                out.append(" " * (n - i))
                break
            out.append(" " * (line_end - i))
            i = line_end
            continue

        # Double-quoted here-string @" ... "@
        if ch == "@" and nxt == '"':
            end = text.find('"@', i + 2)
            if end != -1:
                block = text[i:end + 2]
                out.append(" " * len(block.replace("\n", " ")))
                i = end + 2
                continue

        # Single-quoted here-string @' ... '@
        if ch == "@" and nxt == "'":
            end = text.find("'@", i + 2)
            if end != -1:
                block = text[i:end + 2]
                out.append(" " * len(block.replace("\n", " ")))
                i = end + 2
                continue

        # Double-quoted string "..." (simple handling, no embedded `" tracked)
        if ch == '"':
            j = i + 1
            while j < n:
                if text[j] == '"' and text[j - 1] != "`":
                    break
                j += 1
            block = text[i:j + 1]
            out.append(" " * len(block))
            i = j + 1
            continue

        # Single-quoted string '...'
        if ch == "'":
            j = i + 1
            while j < n:
                if text[j] == "'" and text[j - 1] != "`":
                    break
                j += 1
            block = text[i:j + 1]
            out.append(" " * len(block))
            i = j + 1
            continue

        out.append(ch)
        i += 1

    return "".join(out)


def _find_issues(path: Path) -> list[tuple[int, int, str]]:
    """Return (line, column, message) for each compatibility issue."""
    text = path.read_text(encoding="utf-8-sig")
    stripped = _strip_powershell_literals(text)
    issues: list[tuple[int, int, str]] = []
    for pattern, message in FORBIDDEN:
        for match in re.finditer(pattern, stripped):
            line = stripped[: match.start()].count("\n") + 1
            col = match.start() - stripped.rfind("\n", 0, match.start())
            issues.append((line, col, message))
    return sorted(set(issues))


def _collect_files(args: argparse.Namespace) -> list[Path]:
    if args.files:
        return [Path(f) for f in args.files]
    return sorted(ROOT.rglob("*.ps1"))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Lint PowerShell files for Windows PowerShell 5.1 compatibility."
    )
    parser.add_argument("files", nargs="*", help="Specific .ps1 files to check.")
    parser.add_argument(
        "--exclude",
        action="append",
        default=[],
        help="Glob patterns for files/folders to ignore (may be given multiple times).",
    )
    args = parser.parse_args()

    files = _collect_files(args)
    exclude_patterns = [re.compile(fnmatch.translate(p)) for p in args.exclude] if args.exclude else []

    all_ok = True
    for path in files:
        try:
            display = path.relative_to(ROOT)
        except ValueError:
            display = path
        if any(
            p.match(str(display)) or p.match(str(display.as_posix()))
            for p in exclude_patterns
        ):
            continue
        issues = _find_issues(path)
        if issues:
            all_ok = False
            print(f"{display}")
            for line, col, message in issues:
                print(f"  {line}:{col}: {message}")

    if all_ok:
        print("All PowerShell files are compatible with Windows PowerShell 5.1.")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
