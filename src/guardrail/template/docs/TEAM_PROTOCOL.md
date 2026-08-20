**Before anything else, if this is a same-machine multi-agent situation:**
read the other agent's actual log/state files directly instead of
posting-and-waiting (`AI_CONSTITUTION.md` Law 11.1). Reserve this channel
for genuinely separate machines, or for durable records either way wants
kept.

# Team communication protocol (lawkeeper)

Ported from Windwright's proven `team_chat.py` pattern (2026-08-20
governance parity check) — one deterministic command for "post/check the
team channel," never a prose instruction to interpret.

## The channel

Durable decisions and cross-machine/cross-agent reports live in **GitHub
Discussion #2**: https://github.com/kooshikooo-lab/lawkeeper/discussions/2

## The one tool

`scripts/team_chat.py`, run from the repo root:

```bash
# At the start of every session — read what happened since you last checked:
python scripts/team_chat.py sync

# Post a message (use --file for anything long or with special characters):
python scripts/team_chat.py post "message text"
python scripts/team_chat.py post --file path/to/report.md

# Post something that MUST be read and acknowledged:
python scripts/team_chat.py post --important "message text"

# Wait for the other side to respond instead of polling manually:
python scripts/team_chat.py watch --interval 30
```

No flags needed for this repo's own channel — the script auto-detects the
repo from `git remote get-url origin` and reads the discussion number from
`.guardrail.json`'s `team_discussion` key. Pass `--repo owner/name
--discussion N` only to reach a different repo's channel from here.

## Rules (same as Windwright's Laws 11/12)

1. **Read before you act.** Run `sync` at the start of every session before
   writing any code. Posting is not enough — the other side reading it is
   what makes it count.
2. **Acknowledge what you read.** If a message needs action, reply stating
   what you read and what you'll do about it. Silence is treated as not
   having read it.
3. **No human relay.** If the human passes you a message, that's a
   conversation shortcut, not a substitute — still post/sync through the
   channel so it's durable and the other agent sees it directly.
