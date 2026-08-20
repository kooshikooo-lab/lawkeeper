# Blockers — things that need setup, not things that failed

Every entry here is a real, checked prerequisite gap (a missing key, a missing install, unavailable hardware) with exactly what would unblock it. Nothing here means "impossible" — it means "needs this specific thing."

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
