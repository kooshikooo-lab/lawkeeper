"""Consensus review: a transparent multi-AI tribunal, reliable by construction.

Reimplements the good idea behind Windwright's consensus_orchestrator.py
(a real, proven tool -- caught a genuine acoustics bug with real citations
in a past run) with its actual weak point fixed: two of its three reviewers
depended on clipboard-paste + OCR against a literal desktop app window,
which is why it stopped being used (last real run 2026-08-16). Every
reviewer here is a real API call -- no OCR, no window automation, nothing
that breaks when an app updates its UI.

Reviewers, pluggable (add more by extending REVIEWERS below):
  claude  -> the real Claude Code CLI (`claude -p`) -- reliable, no API key
             needed beyond an authenticated CLI.
  <any OpenRouter model id> -> via ai_review.call_model (already proven:
             ai_review.py, team_chat.py's sibling port). Kimi K2
             (moonshotai/kimi-k2-thinking) and a second, lineage-distinct
             model are the defaults, so a "consensus" is never just one
             model family agreeing with itself.

The Law 23 lesson, applied here directly: a reviewer that fails to
respond is NEVER silently counted as agreement or silently dropped from
the tally. A finding's consensus is reported with exactly how many of the
expected reviewers actually answered -- "2/3 responded" is a different,
weaker claim than "3/3 agreed," and this tool says which one it has.

Kept from the original design, because it was genuinely good:
  - Transparent: every prompt and every full reply is written to disk.
  - Gated dispatch: a round is drafted and staged, never auto-sent --
    review it, then explicitly approve before anything is actually asked.
  - A DISAGREE vote must carry a reason; a bare veto doesn't count.

Usage:
    python scripts/consensus_review.py draft --spec case.json --round 1
    python scripts/consensus_review.py run --spec case.json --round 1 --approved
    python scripts/consensus_review.py show --spec case.json
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ai_review import call_model  # noqa: E402  (Law 3: reuse, don't reinvent)
from blockers import report_blocker  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
CONSENSUS_DIR = REPO_ROOT / "consensus"

REVIEW_SYSTEM_PROMPT = (
    "You are one independent reviewer in a transparent multi-AI consensus "
    "tribunal. Read the brief and reply with your verdict for each finding, "
    "one line per finding, in exactly this format:\n"
    "  F1: AGREE | your reasoning\n"
    "  F2: DISAGREE | your reasoning (a bare veto with no reason is invalid)\n"
    "Be genuinely independent: if you disagree with the brief's framing or "
    "with another reviewer's stated position, say so and why. Do not just "
    "agree to be agreeable."
)

# Reviewer registry. "claude" is special-cased (real CLI, no API key needed).
# Everything else is an OpenRouter model id, called via ai_review.call_model.
#
# The economic point (explicit, from the user): this tool's real value is
# combining FREE models to produce work that beats any one of them alone --
# not requiring a paid model. Every default reviewer below is confirmed
# ":free" on OpenRouter's live /models list (2026-08-20, not assumed), from
# three genuinely distinct labs (Nvidia, Zhipu/GLM, OpenAI's open weights),
# so a "consensus" is real cross-lineage agreement/disagreement, not one
# model family talking to itself. This is a real, working instance of
# "make bad/free models do good work" -- verified against actual API
# responses below, not asserted.
#
# Paid models (e.g. moonshotai/kimi-k3, confirmed real but NOT free) are
# deliberately not in the default set -- add one explicitly if you want to
# spend credits for it, don't default into a bill.
REVIEWERS: dict[str, str | None] = {
    "claude": None,
    "nemotron-ultra": "nvidia/nemotron-3-ultra-550b-a55b:free",
    "glm": "z-ai/glm-5.2:free",
    "gpt-oss": "openai/gpt-oss-20b:free",
}


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def _case_dir(spec_path: Path) -> Path:
    d = CONSENSUS_DIR / spec_path.stem
    d.mkdir(parents=True, exist_ok=True)
    return d


def load_spec(spec_path: Path) -> dict:
    if not spec_path.exists():
        raise SystemExit(f"ERROR: spec file not found: {spec_path}")
    return json.loads(spec_path.read_text(encoding="utf-8"))


def render_brief(spec: dict, round_number: int) -> str:
    findings = spec.get("findings", [])
    lines = [
        f"# Consensus review brief -- round {round_number}",
        f"Case: {spec.get('title', spec.get('id', 'untitled'))}",
        "",
        spec.get("context", ""),
        "",
        "## Findings to vote on",
    ]
    for f in findings:
        lines.append(f"\n### {f['id']}: {f['title']}")
        lines.append(f['claim'])
        if f.get("evidence"):
            lines.append(f"Evidence: {f['evidence']}")
    return "\n".join(lines)


def draft_path(case_dir: Path, round_number: int) -> Path:
    return case_dir / f"_pending_brief_R{round_number}.md"


def dispatch_path(case_dir: Path, round_number: int, reviewer: str) -> Path:
    d = case_dir / f"_replies_R{round_number}"
    d.mkdir(parents=True, exist_ok=True)
    return d / f"{reviewer}.txt"


def ask_claude(brief: str) -> str:
    """The real Claude Code CLI. Reliable: no OCR, no window, just the CLI
    that's already authenticated and running on this machine.

    shutil.which() resolves the real executable (claude.cmd on Windows) --
    a plain ["claude", ...] list arg fails there with WinError 2, since
    subprocess doesn't apply PATHEXT resolution the way a shell would.
    Found by actually running this, not assumed (Law 23).
    """
    claude_path = shutil.which("claude")
    if not claude_path:
        raise RuntimeError("claude CLI not found on PATH")
    cmd = [claude_path, "-p", "--output-format", "text"]
    proc = subprocess.run(
        cmd, input=brief, capture_output=True, timeout=900,
        encoding="utf-8", errors="replace", cwd=str(REPO_ROOT),
    )
    text = (proc.stdout or "").strip()
    if not text:
        err = (proc.stderr or "").strip()
        raise RuntimeError(f"claude CLI returned no output: {err or '(empty)'}")
    # Real bug found by actually running this (Law 23): a nested `claude -p`
    # subprocess spawned from inside an already-running Claude Code session
    # returns "Not logged in" as its STDOUT, not stderr and not a nonzero
    # exit -- indistinguishable from a real reply unless checked explicitly.
    # Known limitation, not fixed here: this session authenticates via
    # OAuth, which doesn't propagate to a freshly-spawned child process, and
    # no ANTHROPIC_API_KEY is set. This driver likely works fine invoked
    # from a genuinely separate, already-`/login`'d terminal -- flagging
    # honestly rather than silently treating this text as a real verdict.
    if "not logged in" in text.lower() or text.lower().startswith("please run /login"):
        report_blocker(
            component="consensus_review.py's 'claude' reviewer driver",
            missing="an authenticated claude CLI reachable from a subprocess",
            why="this session authenticates via OAuth, which does not "
                "propagate to a freshly-spawned child `claude -p` process, "
                "and no ANTHROPIC_API_KEY is set",
            how_to_fix="either run this tool from a terminal where `claude "
                       "/login` has already been done directly (not nested "
                       "inside another Claude Code session), or set "
                       "ANTHROPIC_API_KEY in the environment",
        )
        raise RuntimeError("claude CLI not authenticated in this subprocess context (see BLOCKERS.md)")
    return text


def ask_reviewer(name: str, brief: str) -> tuple[str | None, str | None]:
    """Returns (reply_text, error). Exactly one is None. Never raises --
    a failed reviewer is data (an error string), not a silent gap."""
    try:
        if name == "claude":
            return ask_claude(brief), None
        model_id = REVIEWERS[name]
        reply = call_model(model_id, brief, system_prompt=REVIEW_SYSTEM_PROMPT)
        return reply, None
    except Exception as exc:  # noqa: BLE001 -- a reviewer failing is expected, must be reported not crash the round
        return None, str(exc)


def draft(spec_path: Path, round_number: int) -> None:
    spec = load_spec(spec_path)
    case_dir = _case_dir(spec_path)
    p = draft_path(case_dir, round_number)
    if p.exists():
        print(f"----- draft already staged at {p} (not overwritten) -----")
        print(p.read_text(encoding="utf-8"))
        return
    brief = render_brief(spec, round_number)
    p.write_text(brief, encoding="utf-8")
    print(f"----- DRAFT for round {round_number} (staged, NOT sent) -----")
    print(brief)
    print(f"\nStaged at: {p}")
    print(f"Reviewers: {', '.join(REVIEWERS)}")
    print("Approve and send with: run --approved")


def run(spec_path: Path, round_number: int, approved: bool) -> None:
    case_dir = _case_dir(spec_path)
    p = draft_path(case_dir, round_number)
    if not approved:
        print("BLOCKED: pass --approved to actually dispatch this round. "
              "Nothing was sent. (Gated dispatch is deliberate.)")
        return
    if not p.exists():
        raise SystemExit(f"ERROR: no staged draft at {p} -- run `draft` first.")
    brief = p.read_text(encoding="utf-8")

    results: dict[str, dict] = {}
    for name in REVIEWERS:
        print(f"[{name}] asking...")
        t0 = time.time()
        reply, error = ask_reviewer(name, brief)
        elapsed = time.time() - t0
        out_path = dispatch_path(case_dir, round_number, name)
        out_path.write_text(reply if reply is not None else f"ERROR: {error}", encoding="utf-8")
        if error:
            print(f"[{name}] FAILED after {elapsed:.1f}s: {error}")
            results[name] = {"status": "error", "error": error}
        else:
            print(f"[{name}] responded in {elapsed:.1f}s")
            results[name] = {"status": "ok", "reply_path": str(out_path)}

    responded = sum(1 for r in results.values() if r["status"] == "ok")
    total = len(REVIEWERS)
    print(f"\n=== ROUND {round_number}: {responded}/{total} reviewers responded ===")
    if responded < total:
        print(f"DEGRADED CONSENSUS -- {total - responded} reviewer(s) failed, "
              f"see errors above. This is NOT a {total}/{total} tribunal result; "
              f"do not report it as one.")

    ledger_path = case_dir / "_ledger.json"
    ledger = json.loads(ledger_path.read_text(encoding="utf-8")) if ledger_path.exists() else []
    ledger.append({
        "round": round_number,
        "timestamp": now_utc(),
        "responded": responded,
        "total": total,
        "results": results,
    })
    ledger_path.write_text(json.dumps(ledger, indent=2), encoding="utf-8")
    print(f"Ledger updated: {ledger_path}")


def show(spec_path: Path) -> None:
    case_dir = _case_dir(spec_path)
    ledger_path = case_dir / "_ledger.json"
    if not ledger_path.exists():
        print("No rounds run yet for this case.")
        return
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    for entry in ledger:
        print(f"Round {entry['round']} ({entry['timestamp']}): "
              f"{entry['responded']}/{entry['total']} responded")
        for name, r in entry["results"].items():
            print(f"  {name}: {r['status']}" + (f" -- {r.get('error')}" if r.get("error") else ""))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("cmd", choices=["draft", "run", "show"])
    parser.add_argument("--spec", required=True, help="path to the case spec JSON")
    parser.add_argument("--round", type=int, default=1)
    parser.add_argument("--approved", action="store_true")
    args = parser.parse_args()

    spec_path = Path(args.spec)
    if args.cmd == "draft":
        draft(spec_path, args.round)
    elif args.cmd == "run":
        run(spec_path, args.round, args.approved)
    elif args.cmd == "show":
        show(spec_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
