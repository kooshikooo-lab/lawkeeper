#!/usr/bin/env python3
"""Claude Code PreToolUse hook: a live, per-tool-call gate on Bash commands
that would force-push over or delete a canonical branch (Law 15/16).

Why this exists: guard_branch.py's pre-push hook is real enforcement, but
it only sees the push after `git push` has already run against the
network -- structurally too late for "the agent misread an instruction
and force-pushed over main mid-session." A PreToolUse hook sees the exact
shell command Claude Code is about to run, before it executes at all.
Confirmed against Anthropic's own current docs
(code.claude.com/docs/en/hooks): a PreToolUse hook receives
{"tool_name": ..., "tool_input": {"command": ...}} on stdin and can
return {"hookSpecificOutput": {"permissionDecision": "allow"|"deny"|"ask",
...}} on stdout, evaluated before the tool call executes.

See docs/RESEARCH_harness_governance_survey.md and
docs/RESEARCH_harness_hook_mechanisms_survey.md for the prior-art survey
this design is built on -- five independent systems (Claude Code,
Omnigent, deepseek-harness, hermes-agent, goose) all converge on
deny > ask > allow as the tool-call gating precedence.

Two tiers, deliberately built as physically separate code paths rather
than "the same decision type, we just always pick deny by convention"
(the governance survey's own recommendation, backed by two more shipped
precedents -- Hermes' HARDLINE_PATTERNS, goose's deny-always-wins merge):

- HARDLINE: a force-push over, or deletion of, a canonical branch that
  this script could confidently identify from the command text.
  `_inspect_git_push`/`_inspect_git_branch` have no code path that
  returns anything but a hardline Risk for these shapes -- there is no
  "ask" branch to accidentally reach for this tier, not a convention
  never to invoke one. The only way past a hardline verdict is the same
  pre-set override guard_branch.py's own pre-push hook already honors
  (GUARD_BRANCH_ALLOW_FORCE/_DELETE=<branch>, set before the session
  starts -- a deliberate, out-of-band decision, not an in-session
  approval prompt that can be rubber-stamped).
- ASK: a command that looks like it might be attempting the same thing,
  but the branch name couldn't be confidently resolved (a shell
  variable, command substitution, or an unresolvable "current branch"
  lookup). Genuine uncertainty, not confirmed danger -- routed to a
  human instead of either silently allowed or wrongly hardline-blocked.

Real, known limitations, stated rather than hidden (same heuristic
status as orphan_scan.py's basename matching, same honesty standard):
this is word-level shell tokenization (shlex), not a real shell parser.
Command substitution, indirection through a script/alias/function, or
obscure quoting can evade it. This is a defense-in-depth layer, not a
sandbox -- exactly the caveat given when this build was proposed.

Failure handling, deliberately asymmetric:
- Can't even parse the stdin JSON (this hook is broken) -> fail OPEN
  (exit 0, no verdict), matching this repo's existing convention
  (claude_stop_hook.py) and every harness this survey read: a
  misbehaving hook must not hold every future tool call hostage.
- Stdin parses fine but an internal exception happens while classifying
  the command (this hook has a bug, but we DID receive a real command)
  -> fail to ASK, not silently allow and not hardline-deny. We didn't
  actually confirm this is dangerous, so claiming hardline certainty
  would overclaim; but silently allowing defeats the point of having
  this hook at all when it breaks.

Usage (wired via .claude/settings.json's PreToolUse hook list):
    echo '{"tool_name": "Bash", "tool_input": {"command": "..."}}' \
        | python scripts/gate_pretooluse.py
"""
from __future__ import annotations

import json
import os
import shlex
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import guard_branch  # noqa: E402


_FORCE_FLAGS = {"-f", "--force", "--force-with-lease", "--force-if-includes"}
_DELETE_FLAGS_PUSH = {"-d", "--delete"}
_DELETE_FLAGS_BRANCH = {"-D", "--delete", "-d"}
_SHELL_OPERATORS = {"&&", "||", ";", "|"}


class Risk:
    """One detected risk signal. level is "hardline" or "ask" -- never
    constructed with anything else, by construction of the two inspect
    functions below (see module docstring)."""

    def __init__(self, level: str, branch: str | None, reason: str):
        self.level = level
        self.branch = branch
        self.reason = reason


def _split_commands(command: str) -> list[list[str]]:
    """Tokenize a shell command line into separate sub-commands, split on
    &&/||/;/|. Real word-level tokenization (shlex), not a naive
    substring regex -- but not a real shell parser either (documented
    limitation above): subshells, command substitution, and unbalanced
    quoting can produce an empty or wrong split, so an unparseable
    command yields no sub-commands (treated as "nothing to inspect"
    here, not as a signal on its own -- most unbalanced-quote commands
    have nothing to do with git and shouldn't ask on every one)."""
    try:
        tokens = shlex.split(command, posix=True)
    except ValueError:
        return []
    commands: list[list[str]] = [[]]
    for tok in tokens:
        if tok in _SHELL_OPERATORS:
            commands.append([])
        else:
            commands[-1].append(tok)
    return [c for c in commands if c]


def _basename(tok: str) -> str:
    return tok.replace("\\", "/").rsplit("/", 1)[-1]


def _looks_unresolvable(tok: str) -> bool:
    # `in`, not `startswith`: a variable can end up embedded mid-token
    # after refspec normalization (e.g. "refs/heads/$BRANCH" strips down
    # to "$BRANCH", but "+HEAD:pre-$BRANCH" strips down to "pre-$BRANCH",
    # which never starts with "$"). Copilot review, PR #19.
    return "$" in tok or "`" in tok


def _normalize_ref(name: str) -> str:
    """Strip a `refs/heads/` prefix so a fully-qualified ref compares
    correctly against guard_branch.is_canonical()'s bare-name check.
    Copilot review, PR #19: `git push origin :refs/heads/main` (delete)
    and `git branch -D refs/heads/main` are both real, valid git
    invocations this scanner previously never normalized, silently
    missing a canonical-branch match spelled out fully-qualified."""
    prefix = "refs/heads/"
    return name[len(prefix):] if name.startswith(prefix) else name


def _parse_push_refspec(token: str) -> tuple[str | None, bool]:
    """Parse one `git push` positional as a refspec.

    Returns (destination_branch_or_None, is_force_or_delete_marked).
    Handles the general push refspec grammar this scanner previously
    missed (Copilot review, PR #19): an optional leading `+` (force),
    an optional `<src>:<dst>` split where the DESTINATION -- not the
    whole token -- is what actually gets updated/deleted on the
    remote (`+main:main` naively became the literal string
    `"main:main"`, which never matches a bare branch name), and a
    `refs/heads/<name>` destination normalized so it compares
    correctly. A bare token with neither marker is returned as its own
    target with no marker of its own -- force/delete then comes from
    the command's own --force/--delete flags, checked by the caller.
    """
    forced = token.startswith("+")
    rest = token[1:] if forced else token
    if ":" in rest:
        src, _, dst = rest.partition(":")
        target = dst
        is_delete = src == ""
    else:
        target = rest
        is_delete = False
    target = _normalize_ref(target)
    return (target or None), (forced or is_delete)


def _current_branch() -> str | None:
    out, code = guard_branch.run_git(["rev-parse", "--abbrev-ref", "HEAD"])
    if code == 0 and out and out != "HEAD":
        return out
    return None


_DRY_RUN_FLAGS = {"-n", "--dry-run"}


def _inspect_git_push(args: list[str]) -> Risk | None:
    # `--dry-run`/`-n` is git's own documented guarantee that this push
    # computes and reports what would happen without mutating the remote
    # at all -- it structurally cannot cause the harm this tier exists to
    # prevent, so flagging it is a pure false positive, not extra safety.
    # This is not a bypass: a chained real push without the flag
    # (`git push --dry-run origin main && git push --force origin main`)
    # is still inspected on its own, independently, by _split_commands.
    # Found live: a real dry-run test of this exact hook got blocked by
    # this exact function before this exemption existed.
    if any(a in _DRY_RUN_FLAGS for a in args):
        return None

    cmd_force = any(a in _FORCE_FLAGS for a in args)
    cmd_delete = any(a in _DELETE_FLAGS_PUSH for a in args)
    positionals = [a for a in args if not a.startswith("-")]

    # A positional is "refspec-shaped" (leading + or contains :) and is
    # therefore an explicit branch target regardless of position. A
    # "bare" positional (neither) is ambiguous between "the remote
    # name" and "a branch name" -- git's own convention is that the
    # FIRST bare positional is the remote (`git push origin`), so only
    # bare positionals AFTER the first are explicit branch targets.
    #
    # Getting this distinction wrong is exactly the regression a second
    # Copilot review round caught: treating every positional uniformly
    # as a target meant `git push --force origin` (one bare positional,
    # the remote, no refspec) never fell through to resolving the
    # current branch -- it checked is_canonical("origin") instead,
    # which is never true, silently allowing a real force-push to the
    # current branch through undetected. (Copilot review, PR #19 round 2.)
    refspec_shaped = [p for p in positionals if p.startswith("+") or ":" in p]
    bare = [p for p in positionals if p not in refspec_shaped]

    explicit_targets: list[str] = []
    any_marked = False
    for p in refspec_shaped:
        target, marked = _parse_push_refspec(p)
        if target:
            explicit_targets.append(target)
        any_marked = any_marked or marked
    # Bare tokens after the first (conventionally the remote) are
    # explicit branch names too -- normalized the same way a refspec's
    # destination is, so `git push origin refs/heads/main` (valid,
    # equivalent to `git push origin main`) still matches.
    explicit_targets.extend(_normalize_ref(b) for b in bare[1:])

    any_risky_shape = cmd_force or cmd_delete or any_marked
    if not any_risky_shape:
        return None  # an ordinary push -- not a dangerous shape at all

    if not explicit_targets:
        # No explicit branch given at all (`git push --force`, or
        # `git push --force origin` with only the remote) -- pushes/
        # deletes whatever the current branch is under the remote's
        # config. Can't be fully certain from static text, but ignoring
        # it would silently miss the plainest form of `git push -f`.
        if any(_looks_unresolvable(p) for p in positionals):
            return Risk("ask", None,
                        "a force/delete push with no explicit branch and an unresolvable "
                        "(shell variable/substitution) component")
        branch = _current_branch()
        if branch is None:
            return Risk("ask", None,
                         "a force/delete push with no explicit branch, and the current branch "
                         "could not be resolved")
        if guard_branch.is_canonical(branch):
            return Risk("hardline", branch,
                         f"a force/delete push with no explicit refspec, on canonical branch '{branch}'")
        return None

    # Hardline outranks ask (deny > ask, per the hook-mechanisms survey):
    # scan every target for a confirmed canonical match FIRST, across
    # the whole command, before falling back to ask for an unresolvable
    # one -- a command with both an unresolvable target and a
    # separately-confirmed canonical target must still deny, not ask.
    for target in explicit_targets:
        if not _looks_unresolvable(target) and guard_branch.is_canonical(target):
            return Risk("hardline", target, f"a force/delete push targeting canonical branch '{target}'")
    for target in explicit_targets:
        if _looks_unresolvable(target):
            return Risk("ask", None,
                         f"a force/delete push whose target '{target}' could not be resolved "
                         "(shell variable/substitution)")
    return None


def _inspect_git_branch(args: list[str]) -> Risk | None:
    if not any(a in _DELETE_FLAGS_BRANCH for a in args):
        return None
    # Same refs/heads/ normalization as the push path (Copilot review,
    # PR #19): `git branch -D refs/heads/main` is a real, valid git
    # invocation, and without this it never matched a bare canonical name.
    targets = [_normalize_ref(p) for p in (a for a in args if not a.startswith("-"))]
    # Hardline outranks ask, same reasoning as _inspect_git_push.
    for target in targets:
        if not _looks_unresolvable(target) and guard_branch.is_canonical(target):
            return Risk("hardline", target, f"a branch delete targeting canonical branch '{target}'")
    for target in targets:
        if _looks_unresolvable(target):
            return Risk("ask", None,
                         f"a branch delete whose target '{target}' could not be resolved "
                         "(shell variable/substitution)")
    return None


def inspect_command(command: str) -> Risk | None:
    """Return the highest-severity Risk found across every chained
    sub-command (split on &&/||/;/|), or None if nothing matched a
    known dangerous shape. A hardline finding returns immediately --
    nothing outranks it (deny > ask > allow, per the survey)."""
    best: Risk | None = None
    for tokens in _split_commands(command):
        if not tokens or _basename(tokens[0]) != "git" or len(tokens) < 2:
            continue
        sub, args = tokens[1], tokens[2:]
        if sub == "push":
            risk = _inspect_git_push(args)
        elif sub == "branch":
            risk = _inspect_git_branch(args)
        else:
            risk = None
        if risk is None:
            continue
        if risk.level == "hardline":
            return risk
        if best is None:
            best = risk
    return best


def _overridden(branch: str | None) -> bool:
    """The same pre-set, out-of-band override guard_branch.py's own
    pre-push hook already honors -- deliberately the only way past a
    hardline verdict, and deliberately not an in-session prompt (see
    module docstring's HARDLINE explanation)."""
    if not branch:
        return False
    return (
        os.environ.get("GUARD_BRANCH_ALLOW_FORCE") == branch
        or os.environ.get("GUARD_BRANCH_ALLOW_DELETE") == branch
    )


def decide(tool_name: str, tool_input: dict) -> tuple[str, str] | None:
    """Return (permissionDecision, reason), or None for "no opinion"
    (Claude Code's normal permission rules and any other hook decide
    instead)."""
    if tool_name != "Bash":
        return None
    command = tool_input.get("command", "") or ""
    risk = inspect_command(command)
    if risk is None:
        return None

    if risk.level == "hardline":
        if _overridden(risk.branch):
            return None
        return (
            "deny",
            f"lawkeeper hardline guard: {risk.reason}. No in-session override exists for this tier -- "
            f"if this is genuinely intended, set GUARD_BRANCH_ALLOW_FORCE or GUARD_BRANCH_ALLOW_DELETE="
            f"{risk.branch} before starting the session.",
        )
    return ("ask", f"lawkeeper guard: {risk.reason} -- please confirm this is intended.")


def main() -> int:
    raw = sys.stdin.read()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return 0  # can't see the tool call at all -- fail open (see module docstring)

    tool_name = data.get("tool_name", "")
    tool_input = data.get("tool_input", {}) or {}

    try:
        result = decide(tool_name, tool_input)
    except Exception as exc:  # noqa: BLE001 -- a bug here must not silently allow (see module docstring)
        result = (
            "ask",
            f"lawkeeper guard: internal error evaluating this command "
            f"({type(exc).__name__}: {exc}) -- please confirm manually.",
        )

    if result is None:
        return 0

    decision, reason = result
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": decision,
            "permissionDecisionReason": reason,
        }
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
