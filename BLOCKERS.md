# Blockers — things that need setup, not things that failed

Every entry here is a real, checked prerequisite gap (a missing key, a missing install, unavailable hardware) with exactly what would unblock it. Nothing here means "impossible" — it means "needs this specific thing."

## consensus_review.py's 'claude' reviewer driver (2026-08-21T00:47:27.336922+00:00)
- **Missing:** an authenticated claude CLI reachable from a subprocess
- **Why:** this session authenticates via OAuth, which does not propagate to a freshly-spawned child `claude -p` process, and no ANTHROPIC_API_KEY is set
- **To fix:** either run this tool from a terminal where `claude /login` has already been done directly (not nested inside another Claude Code session), or set ANTHROPIC_API_KEY in the environment

## consensus_review.py's 'claude' reviewer driver (2026-08-21T00:46:23.663913+00:00)
- **Missing:** an authenticated claude CLI reachable from a subprocess
- **Why:** this session authenticates via OAuth, which does not propagate to a freshly-spawned child `claude -p` process, and no ANTHROPIC_API_KEY is set
- **To fix:** either run this tool from a terminal where `claude /login` has already been done directly (not nested inside another Claude Code session), or set ANTHROPIC_API_KEY in the environment

## src/guardrail/agent.py Stage 1 live verification (2026-08-21T00:42:19.952269+00:00)
- **Missing:** a real ANTHROPIC_API_KEY in this session environment
- **Why:** this Claude Code session authenticates via OAuth/subscription, not a raw API key -- the Agent SDK specifically requires ANTHROPIC_API_KEY to make real calls, confirmed via env check (only ANTHROPIC_BASE_URL is set, no key)
- **To fix:** set ANTHROPIC_API_KEY in the environment (the user's own key, matching the whole point of this prototype), or run this verification from a context where one is already available

## consensus_review.py's 'claude' reviewer driver (2026-08-21T00:41:18.135822+00:00)
- **Missing:** an authenticated claude CLI reachable from a subprocess
- **Why:** this session authenticates via OAuth, which does not propagate to a freshly-spawned child `claude -p` process, and no ANTHROPIC_API_KEY is set
- **To fix:** either run this tool from a terminal where `claude /login` has already been done directly (not nested inside another Claude Code session), or set ANTHROPIC_API_KEY in the environment

## consensus_review.py's 'claude' reviewer driver (2026-08-21T00:39:41.795198+00:00)
- **Missing:** an authenticated claude CLI reachable from a subprocess
- **Why:** this session authenticates via OAuth, which does not propagate to a freshly-spawned child `claude -p` process, and no ANTHROPIC_API_KEY is set
- **To fix:** either run this tool from a terminal where `claude /login` has already been done directly (not nested inside another Claude Code session), or set ANTHROPIC_API_KEY in the environment

## consensus_review.py's 'claude' reviewer driver (2026-08-21T00:35:05.753893+00:00)
- **Missing:** an authenticated claude CLI reachable from a subprocess
- **Why:** this session authenticates via OAuth, which does not propagate to a freshly-spawned child `claude -p` process, and no ANTHROPIC_API_KEY is set
- **To fix:** either run this tool from a terminal where `claude /login` has already been done directly (not nested inside another Claude Code session), or set ANTHROPIC_API_KEY in the environment

## consensus_review.py's 'claude' reviewer driver (2026-08-21T00:28:25.131147+00:00)
- **Missing:** an authenticated claude CLI reachable from a subprocess
- **Why:** this session authenticates via OAuth, which does not propagate to a freshly-spawned child `claude -p` process, and no ANTHROPIC_API_KEY is set
- **To fix:** either run this tool from a terminal where `claude /login` has already been done directly (not nested inside another Claude Code session), or set ANTHROPIC_API_KEY in the environment

## consensus_review.py's 'claude' reviewer driver (2026-08-20T22:52:59.508310+00:00)
- **Missing:** an authenticated claude CLI reachable from a subprocess
- **Why:** this session authenticates via OAuth, which does not propagate to a freshly-spawned child `claude -p` process, and no ANTHROPIC_API_KEY is set
- **To fix:** either run this tool from a terminal where `claude /login` has already been done directly (not nested inside another Claude Code session), or set ANTHROPIC_API_KEY in the environment

## consensus_review.py's 'claude' reviewer driver (2026-08-20T20:59:10.381593+00:00)
- **Missing:** an authenticated claude CLI reachable from a subprocess
- **Why:** this session authenticates via OAuth, which does not propagate to a freshly-spawned child `claude -p` process, and no ANTHROPIC_API_KEY is set
- **To fix:** either run this tool from a terminal where `claude /login` has already been done directly (not nested inside another Claude Code session), or set ANTHROPIC_API_KEY in the environment

## consensus_review.py's 'claude' reviewer driver (2026-08-20T20:58:15.363252+00:00)
- **Missing:** an authenticated claude CLI reachable from a subprocess
- **Why:** this session authenticates via OAuth, which does not propagate to a freshly-spawned child `claude -p` process, and no ANTHROPIC_API_KEY is set
- **To fix:** either run this tool from a terminal where `claude /login` has already been done directly (not nested inside another Claude Code session), or set ANTHROPIC_API_KEY in the environment

## consensus_review.py's 'claude' reviewer driver (2026-08-20T20:26:58.567342+00:00)
- **Missing:** an authenticated claude CLI reachable from a subprocess
- **Why:** this session authenticates via OAuth, which does not propagate to a freshly-spawned child `claude -p` process, and no ANTHROPIC_API_KEY is set
- **To fix:** either run this tool from a terminal where `claude /login` has already been done directly (not nested inside another Claude Code session), or set ANTHROPIC_API_KEY in the environment

## consensus_review.py's 'claude' reviewer driver (2026-08-20T20:25:28.336437+00:00)
- **Missing:** an authenticated claude CLI reachable from a subprocess
- **Why:** this session authenticates via OAuth, which does not propagate to a freshly-spawned child `claude -p` process, and no ANTHROPIC_API_KEY is set
- **To fix:** either run this tool from a terminal where `claude /login` has already been done directly (not nested inside another Claude Code session), or set ANTHROPIC_API_KEY in the environment

## consensus_review.py's 'claude' reviewer driver (2026-08-20T20:07:36.467677+00:00)
- **Missing:** an authenticated claude CLI reachable from a subprocess
- **Why:** this session authenticates via OAuth, which does not propagate to a freshly-spawned child `claude -p` process, and no ANTHROPIC_API_KEY is set
- **To fix:** either run this tool from a terminal where `claude /login` has already been done directly (not nested inside another Claude Code session), or set ANTHROPIC_API_KEY in the environment

## consensus_review.py's 'claude' reviewer driver (2026-08-20T20:04:13.276958+00:00)
- **Missing:** an authenticated claude CLI reachable from a subprocess
- **Why:** this session authenticates via OAuth, which does not propagate to a freshly-spawned child `claude -p` process, and no ANTHROPIC_API_KEY is set
- **To fix:** either run this tool from a terminal where `claude /login` has already been done directly (not nested inside another Claude Code session), or set ANTHROPIC_API_KEY in the environment

## consensus_review.py's 'claude' reviewer driver (2026-08-20T20:02:25.047880+00:00)
- **Missing:** an authenticated claude CLI reachable from a subprocess
- **Why:** this session authenticates via OAuth, which does not propagate to a freshly-spawned child `claude -p` process, and no ANTHROPIC_API_KEY is set
- **To fix:** either run this tool from a terminal where `claude /login` has already been done directly (not nested inside another Claude Code session), or set ANTHROPIC_API_KEY in the environment

## consensus_review.py's 'claude' reviewer driver (2026-08-20T19:51:19.490717+00:00)
- **Missing:** an authenticated claude CLI reachable from a subprocess
- **Why:** this session authenticates via OAuth, which does not propagate to a freshly-spawned child `claude -p` process, and no ANTHROPIC_API_KEY is set
- **To fix:** either run this tool from a terminal where `claude /login` has already been done directly (not nested inside another Claude Code session), or set ANTHROPIC_API_KEY in the environment

## consensus_review.py's 'claude' reviewer driver (2026-08-20T18:17:24.610650+00:00)
- **Missing:** an authenticated claude CLI reachable from a subprocess
- **Why:** this session authenticates via OAuth, which does not propagate to a freshly-spawned child `claude -p` process, and no ANTHROPIC_API_KEY is set
- **To fix:** either run this tool from a terminal where `claude /login` has already been done directly (not nested inside another Claude Code session), or set ANTHROPIC_API_KEY in the environment

## consensus_review.py's 'claude' reviewer driver (2026-08-20T18:16:15.866281+00:00)
- **Missing:** an authenticated claude CLI reachable from a subprocess
- **Why:** this session authenticates via OAuth, which does not propagate to a freshly-spawned child `claude -p` process, and no ANTHROPIC_API_KEY is set
- **To fix:** either run this tool from a terminal where `claude /login` has already been done directly (not nested inside another Claude Code session), or set ANTHROPIC_API_KEY in the environment

## consensus_review.py's 'claude' reviewer driver (2026-08-20T18:14:00.486450+00:00)
- **Missing:** an authenticated claude CLI reachable from a subprocess
- **Why:** this session authenticates via OAuth, which does not propagate to a freshly-spawned child `claude -p` process, and no ANTHROPIC_API_KEY is set
- **To fix:** either run this tool from a terminal where `claude /login` has already been done directly (not nested inside another Claude Code session), or set ANTHROPIC_API_KEY in the environment

## consensus_review.py's 'claude' reviewer driver (2026-08-20T18:13:42.367766+00:00)
- **Missing:** an authenticated claude CLI reachable from a subprocess
- **Why:** this session authenticates via OAuth, which does not propagate to a freshly-spawned child `claude -p` process, and no ANTHROPIC_API_KEY is set
- **To fix:** either run this tool from a terminal where `claude /login` has already been done directly (not nested inside another Claude Code session), or set ANTHROPIC_API_KEY in the environment

## consensus_review.py's 'claude' reviewer driver (2026-08-20T18:13:08.544483+00:00)
- **Missing:** an authenticated claude CLI reachable from a subprocess
- **Why:** this session authenticates via OAuth, which does not propagate to a freshly-spawned child `claude -p` process, and no ANTHROPIC_API_KEY is set
- **To fix:** either run this tool from a terminal where `claude /login` has already been done directly (not nested inside another Claude Code session), or set ANTHROPIC_API_KEY in the environment

## consensus_review.py's 'claude' reviewer driver (2026-08-20T18:06:58.970961+00:00)
- **Missing:** an authenticated claude CLI reachable from a subprocess
- **Why:** this session authenticates via OAuth, which does not propagate to a freshly-spawned child `claude -p` process, and no ANTHROPIC_API_KEY is set
- **To fix:** either run this tool from a terminal where `claude /login` has already been done directly (not nested inside another Claude Code session), or set ANTHROPIC_API_KEY in the environment

## consensus_review.py's 'claude' reviewer driver (2026-08-20T18:05:09.202992+00:00)
- **Missing:** an authenticated claude CLI reachable from a subprocess
- **Why:** this session authenticates via OAuth, which does not propagate to a freshly-spawned child `claude -p` process, and no ANTHROPIC_API_KEY is set
- **To fix:** either run this tool from a terminal where `claude /login` has already been done directly (not nested inside another Claude Code session), or set ANTHROPIC_API_KEY in the environment

## consensus_review.py's 'claude' reviewer driver (2026-08-20T18:04:58.131168+00:00)
- **Missing:** an authenticated claude CLI reachable from a subprocess
- **Why:** this session authenticates via OAuth, which does not propagate to a freshly-spawned child `claude -p` process, and no ANTHROPIC_API_KEY is set
- **To fix:** either run this tool from a terminal where `claude /login` has already been done directly (not nested inside another Claude Code session), or set ANTHROPIC_API_KEY in the environment
