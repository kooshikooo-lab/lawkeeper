"""Branch-safety guard — enforces Law 15 (Branch governance) at the git layer.

Mechanical enforcement: a git push that would delete or force-push a canonical
branch, or merge blindly, is BLOCKED. The guard never depends on the agent being
well-behaved — it reads the push refspecs from stdin and exits non-zero.

Config (repo root `.guardrail.json`, written by `lawkeeper init`):
  { "machines": ["desktop","laptop"], "canonical_branches": ["main"] }

CLI:
  guard_branch.py --check-push            read push refspecs from stdin (pre-push hook)
  guard_branch.py --check-delete NAME     check a single local branch deletion
  guard_branch.py --audit                 report Law 15 topology violations (read-only)

Human approval overrides (explicit, scoped, per-branch):
  GUARD_BRANCH_ALLOW_DELETE=<branch>      permit deleting one canonical branch
  GUARD_BRANCH_ALLOW_FORCE=<branch>      permit force-pushing one canonical branch

Exit codes: 0 = OK, 1 = blocked.
"""

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(subprocess.run(
    ["git", "rev-parse", "--show-toplevel"],
    capture_output=True, text=True, encoding="utf-8", errors="replace"
).stdout.strip() or Path.cwd())


def load_config():
    try:
        from guardrail.config import Config  # packaged install path
    except Exception:
        try:
            sys.path.insert(0, str(REPO_ROOT / "src"))
            from guardrail.config import Config
        except Exception:
            class _Fallback:
                machines = ["desktop", "laptop"]
                canonical_branches = ["main"]
                placement_rules = {}
                # 2026-09-04: kept in sync with guardrail/config.py's real
                # default -- both the new tool-agnostic "agent/..." prefix
                # and the legacy "opencode/..." prefix are accepted here
                # too, so this fallback path (used only when the guardrail
                # package itself can't be imported) doesn't silently regress
                # to pre-fix behavior.
                feature_regexes = lambda self: [
                    re.compile(r"^agent/[a-z0-9-]+/(?:desktop|laptop)$"),
                    re.compile(r"^opencode/[a-z0-9-]+/(?:desktop|laptop)$"),
                ]
                canonical_branch_names = lambda self: {"main", "opencode/main/desktop", "opencode/main/laptop"}
            return _Fallback()
    return Config.load(REPO_ROOT)


CONFIG = load_config()


def canonical_branches() -> set[str]:
    return CONFIG.canonical_branch_names()


def classify(name: str) -> str | None:
    """Return the Law 15 namespace of a branch, or None if it is an orphan."""
    name = name.strip()
    if name == "main" or (name in canonical_branches()):
        return "canonical" if name.startswith("opencode/main/") else "trunk"
    if any(re.match(r, name) for r in CONFIG.feature_regexes()):
        return "feature"
    if re.match(r"^merge/[a-z0-9-]+$", name):
        return "merge_staging"
    return None


def is_canonical(name: str) -> bool:
    ns = classify(name)
    return ns in ("canonical", "trunk")


def run_git(args):
    try:
        result = subprocess.run(["git"] + args, capture_output=True, text=True,
                                encoding="utf-8", errors="replace")
        return result.stdout.strip(), result.returncode
    except OSError:
        return "", 1


def content_preserved(sha: str) -> bool:
    """Law 15.5: is `sha` an ancestor of a canonical branch or main?"""
    for ref in sorted(canonical_branches()) | {"main", "origin/main"}:
        out, code = run_git(["merge-base", "--is-ancestor", sha, ref])
        if code == 0:
            return True
    return False


def origin_head_points_at_main() -> bool:
    """Law 15.6: the remote's default branch should be main.

    Three layers, cheapest/most-local first, each only tried when the
    previous one couldn't answer - found by actually hitting each gap in
    practice across two separate real failures, not by inspection:

    1. Local origin/HEAD symref, when git has set it (a real `git clone`
       always does). No network call.
    2. refs/remotes/origin/main existing locally. Still no network call -
       covers a normal fetch that didn't run `git remote set-head`. This
       was tried alone first and was NOT enough: a `pull_request`-event
       checkout via actions/checkout@v4 checks out a synthetic merge ref
       directly and never creates refs/remotes/origin/main locally at
       all, even though the remote's real default branch is main.
    3. `git ls-remote --symref origin HEAD` - asks the remote directly.
       Needs network + a reachable `origin` URL, which is exactly the
       situation CI is always in. Kept as the last resort, not the first
       check, so normal local dev usage of this law never needs network
       access for something a local ref can already answer.

    If a remote is configured but every layer still can't determine an
    answer (offline, unreachable, all local refs missing), or no remote
    is configured at all (a brand-new local-only project - the originally
    documented case), returns True: nothing here indicates a real
    violation, and this check must not manufacture a false FAIL out of
    "I couldn't determine the answer."
    """
    out, code = run_git(["symbolic-ref", "refs/remotes/origin/HEAD"])
    if code == 0:
        return out.rstrip("/") in ("refs/remotes/origin/main", "refs/remotes/origin/main/")

    _, remote_code = run_git(["remote", "get-url", "origin"])
    if remote_code != 0:
        return True  # no remote configured yet - nothing to violate this against

    _, main_code = run_git(["rev-parse", "--verify", "refs/remotes/origin/main"])
    if main_code == 0:
        return True

    ls_out, ls_code = run_git(["ls-remote", "--symref", "origin", "HEAD"])
    if ls_code != 0:
        return True  # remote unreachable - can't determine, don't false-fail
    for line in ls_out.splitlines():
        if line.startswith("ref:"):
            parts = line.split()
            return len(parts) >= 2 and parts[1] == "refs/heads/main"
    return True  # no symref line in the response - can't determine


NAMESPACED_ZERO = "0" * 40


def parse_push_lines(lines):
    pushes = []
    for line in lines:
        parts = line.strip().split()
        if len(parts) != 4:
            continue
        local_ref, local_sha, remote_ref, remote_sha = parts
        pushes.append({
            "local_ref": local_ref,
            "local_sha": local_sha,
            "remote_ref": remote_ref,
            "remote_sha": remote_sha,
            "branch": remote_ref.replace("refs/heads/", ""),
            "deletion": set(local_sha) == {"0"},
            "forced": local_sha not in ("", NAMESPACED_ZERO)
                      and remote_sha not in ("", NAMESPACED_ZERO)
                      and local_sha != remote_sha,
        })
    return pushes


def check_push(lines, human_delete=None, human_force=None):
    human_delete = human_delete or set()
    human_force = human_force or set()
    violations = []
    for push in parse_push_lines(lines):
        name = push["branch"]
        ns = classify(name)
        if ns is None:
            violations.append(
                f"PUSH {name}: orphan branch — not in a Law 15 namespace "
                f"(main / opencode/main/<machine> / opencode/<topic>/<machine> / merge/<topic>)."
            )
        if push["deletion"]:
            if is_canonical(name) and name not in human_delete:
                violations.append(
                    f"PUSH {name}: deletion of a canonical branch requires explicit "
                    f"human approval (GUARD_BRANCH_ALLOW_DELETE={name}). Law 15.8."
                )
            elif not push["local_sha"] or set(push["local_sha"]) == {"0"}:
                continue  # nothing to prove for a branch that never existed locally
            elif not content_preserved(push["local_sha"]):
                violations.append(
                    f"PUSH {name}: deletion would lose content not proven present "
                    f"on a canonical branch or main. Law 15.5."
                )
        elif is_canonical(name) and name not in human_force:
            out, code = run_git(["merge-base", "--is-ancestor",
                                 push["remote_sha"], push["local_sha"]])
            if code != 0:
                violations.append(
                    f"PUSH {name}: force/non-fast-forward push to a canonical branch "
                    f"requires explicit human approval (GUARD_BRANCH_ALLOW_FORCE={name}). "
                    f"Law 15.8."
                )
    return violations


def check_delete(name: str) -> list[str]:
    if classify(name) is None:
        return [f"DELETE {name}: orphan branch — not in a Law 15 namespace."]
    if is_canonical(name):
        allowed = os.environ.get("GUARD_BRANCH_ALLOW_DELETE", "").split(",")
        if name in allowed:
            return []
        return [
            f"DELETE {name}: deletion of a canonical branch requires explicit human "
            f"approval (set GUARD_BRANCH_ALLOW_DELETE={name}). Law 15.8."
        ]
    sha, code = run_git(["rev-parse", name])
    if code != 0 or not sha:
        # git couldn't resolve the branch at all (bad ref, not a git repo,
        # transient failure, whatever). The old code treated "I don't know"
        # as "no violation" and let the deletion through unchecked. A guard
        # that can't verify safety should refuse, not shrug.
        return [
            f"DELETE {name}: could not resolve this branch with `git rev-parse` "
            f"(exit {code}) — refusing to approve deletion of something that "
            f"can't be verified. If you're sure this is safe, delete it manually "
            f"outside lawkeeper."
        ]
    if not content_preserved(sha):
        return [f"DELETE {name}: content not provably present on a canonical branch or main. Law 15.5."]
    return []


def audit_branches() -> list[str]:
    out, _ = run_git(["for-each-ref", "--format=%(refname)", "refs/heads"])
    findings = []
    for ref in out.splitlines():
        name = ref.replace("refs/heads/", "")
        if classify(name) is None:
            findings.append(f"AUDIT branch {name}: orphan — not in a Law 15 namespace.")
    if not origin_head_points_at_main():
        findings.append("AUDIT origin/HEAD: does not point at main (Law 15.6).")
    return findings


def main():
    parser = argparse.ArgumentParser(description="Branch-safety guard (Law 15)")
    parser.add_argument("--check-push", action="store_true")
    parser.add_argument("--check-delete", metavar="BRANCH")
    parser.add_argument("--audit", action="store_true")
    args = parser.parse_args()

    if args.audit:
        for f in audit_branches():
            print(f)
        return 1 if audit_branches() else 0

    if args.check_delete:
        vs = check_delete(args.check_delete)
        for v in vs:
            print(v, file=sys.stderr)
        return 1 if vs else 0

    if args.check_push:
        lines = sys.stdin.read().splitlines()
        hd = {n.strip() for n in os.environ.get("GUARD_BRANCH_ALLOW_DELETE", "").split(",") if n.strip()}
        hf = {n.strip() for n in os.environ.get("GUARD_BRANCH_ALLOW_FORCE", "").split(",") if n.strip()}
        violations = check_push(lines, hd, hf)
        for v in violations:
            print(v, file=sys.stderr)
        return 1 if violations else 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
