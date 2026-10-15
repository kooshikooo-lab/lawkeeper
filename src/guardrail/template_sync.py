"""Template provenance and `lawkeeper update` (diff-first sync).

Split out of cli.py (500-line module limit). Pure functions of explicit
paths; cli.py supplies the repo root and the installed template locations.
Design: docs/DESIGN_NOTE_mutmut_and_pinned_distribution_2026-10-10.md.
"""
from __future__ import annotations

import difflib
import hashlib
import json
import sys
from pathlib import Path


def render_text(src: Path, project_name: str) -> str:
    text = src.read_text(encoding="utf-8", errors="replace")
    return (text
            .replace("__PROJECT_NAME__", project_name)
            .replace("__PROJECT_NAME_TITLE__", project_name.replace("-", " ").title()))


def _render(src: Path, dst: Path, project_name: str) -> None:
    dst.write_text(render_text(src, project_name), encoding="utf-8", newline="\n")


def sha256(data: bytes) -> str:
    """Hash with line endings normalised, so a checkout that git converted to
    CRLF (core.autocrlf) is not mistaken for a locally customised file."""
    return hashlib.sha256(data.replace(b"\r\n", b"\n")).hexdigest()


def template_entries(template_root: Path, project_name: str) -> dict[str, bytes]:
    """What `init` would write for this template tree: {repo-relative posix
    path: rendered bytes}. Same path rule as _copy_template_tree (.tmpl
    suffix dropped)."""
    entries: dict[str, bytes] = {}
    for src in sorted(template_root.rglob("*")):
        if src.is_dir():
            continue
        rel = src.relative_to(template_root)
        if src.suffix == ".tmpl":
            rel = rel.with_suffix("")
        entries[rel.as_posix()] = render_text(src, project_name).encode("utf-8")
    return entries


def run_update(root: Path, template_root: Path, extras_root: Path,
               apply: bool, version: str) -> int:
    """Compare a scaffolded repo against the installed lawkeeper template.

    Read-only unless --apply. Per file, using the hash recorded at init
    (or last update):
      unchanged locally, upstream changed -> update (written only with --apply)
      changed locally,   upstream changed -> CONFLICT: diff shown, never overwritten
      changed locally,   upstream same    -> kept (local customisation)
      missing locally                     -> reported, never silently recreated
      new upstream file                   -> added with --apply
    Repos scaffolded before provenance was recorded have no hashes; this
    reports that and changes nothing rather than guessing."""
    cfg_path = root / ".guardrail.json"
    if not cfg_path.exists():
        print("lawkeeper: this repo is not governed (no .guardrail.json); use `lawkeeper init`.",
              file=sys.stderr)
        return 1
    try:
        cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        print("lawkeeper: .guardrail.json is unreadable; fix it first.", file=sys.stderr)
        return 1
    recorded = cfg.get("template_files")
    if not isinstance(recorded, dict) or not recorded:
        print("lawkeeper: no provenance in .guardrail.json (scaffolded before template hashes "
              "were recorded). Nothing was compared or changed. Review `lawkeeper init --force` "
              "output in a scratch clone and merge by hand, or re-scaffold once to start tracking.")
        return 1

    project_name = cfg.get("project_name") or root.name
    upstream = template_entries(template_root, project_name)
    if extras_root.exists():
        # Extras are opt-in: only track the ones this repo was scaffolded with.
        for rel, data in template_entries(extras_root, project_name).items():
            if rel in recorded:
                upstream[rel] = data

    updates, conflicts, kept, missing, added = [], [], [], [], []
    for rel, new in upstream.items():
        local_path = root / rel
        if rel not in recorded:
            if not local_path.exists():
                added.append(rel)
            continue
        if not local_path.exists():
            missing.append(rel)
            continue
        local_hash = sha256(local_path.read_bytes())
        changed_locally = local_hash != recorded[rel]
        changed_upstream = sha256(new) != recorded[rel]
        if not changed_upstream:
            if changed_locally:
                kept.append(rel)
        elif not changed_locally:
            updates.append(rel)
        elif local_hash == sha256(new):
            kept.append(rel)  # local already equals upstream; just re-record
        else:
            conflicts.append(rel)

    print(f"lawkeeper update: repo scaffolded from {cfg.get('template_version', '?')}, "
          f"installed template is {version}")
    for label, items in (("update available", updates), ("new upstream file", added),
                         ("kept (local customisation)", kept),
                         ("missing locally", missing), ("CONFLICT", conflicts)):
        for rel in items:
            print(f"  {label}: {rel}")
    for rel in conflicts:
        old = (root / rel).read_text(encoding="utf-8", errors="replace").splitlines(keepends=True)
        new = upstream[rel].decode("utf-8", errors="replace").splitlines(keepends=True)
        sys.stdout.writelines(difflib.unified_diff(old, new, f"local/{rel}", f"upstream/{rel}"))
    if not (updates or added or conflicts or missing):
        print("  up to date")

    if not apply:
        if updates or added:
            print("Dry run. Re-run with --apply to write the 'update available' / 'new' files "
                  "(conflicts are never overwritten).")
        return 1 if conflicts else 0

    for rel in updates + added:
        dst = root / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(upstream[rel])
        if dst.parent.name == "git-hooks":
            dst.chmod(dst.stat().st_mode | 0o111)
        recorded[rel] = sha256(upstream[rel])
    for rel in kept:
        if sha256((root / rel).read_bytes()) == sha256(upstream[rel]):
            recorded[rel] = sha256(upstream[rel])
    cfg["template_files"] = recorded
    cfg["template_version"] = version
    cfg_path.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
    print(f"applied {len(updates) + len(added)} file(s); {len(conflicts)} conflict(s) left for you.")
    return 1 if conflicts else 0
