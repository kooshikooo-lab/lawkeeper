---
name: same-machine-direct-file-access-not-chat-relay
description: When Claude and opencode are co-located on the same physical machine, read each other's log/state files directly instead of coordinating via team_chat.py's GitHub Discussions relay.
metadata:
  type: feedback
---

When Claude and opencode (and any other agent) are running on the **same
physical machine** with a shared filesystem, neither should post a question
to `team_chat.py` (the GitHub-Discussions-backed relay, see
[[falcun-broader-vision]] and task #75's cross-machine coordination design)
and then sit waiting for a reply. Each agent has direct read access to the
other's actual log/state files on disk — e.g. orbital-study's
`runs/*_console.log`, `runs/team_chat.log`, `runs/overnight.pid` — so a
question like "did your run stall overnight?" should be answered by reading
those files directly, not by asking and waiting.

**Why this matters:** the user flagged this live (2026-08-19) after
watching Claude post a diagnostic question to opencode via team_chat and
wait for a reply, when it could — and, once prompted, did — just read
opencode's own console logs directly and get a definitive answer
immediately (steady 91-131s/generation timing straight through the
incident window, no stalls, clean process exit). The user's framing: "for
a human observer [this] seems really dumb and dysfunctional... you're both
waiting for a reply from the other." They noted this same pattern was
behind an earlier, separate annoyance (Tailscale was tried to fix
*cross-machine* comms and was flaky) — but the current case is worse,
because it's not even a cross-machine problem: both agents are on one box
and still defaulting to the relay.

There's also a real bug compounding this: both agents post to team_chat
under the same GitHub account (`kooshikooo-lab`), so the "new message from
the other machine" self/other detection is unreliable and throws
false-positive echo notifications on the agent's own just-sent posts.

**How to apply:** `team_chat.py` is for genuinely separate machines with no
shared filesystem (desktop + the 2 laptops in task #75's plan). When
confirmed same-machine (check via `tasklist`/process list showing both
agents' processes locally, or just knowing the deployment), read the other
agent's log/state files directly instead of posting a question and waiting.
This applies symmetrically to every agent, not just Claude — if you need to
know something another agent already wrote to disk, check the files
instead of asking and waiting. See `docs/AI_CONSTITUTION.md` Law 11 (the
same-machine exception was added there 2026-08-19, `GOVERNANCE-UPDATE`).
