# Distributed Compute — Plan

Real, sequenced plan for the desktop+laptop as the first, deliberately
small step toward compute as shared infrastructure rather than
individually-owned, siloed hardware — the same underlying principle as
[[virtual-nation-cooperative-vision]] (knowledge/automation as commonly
owned capital) applied to the most literal resource: CPU/GPU cycles.
Kept grounded to what two real machines can actually do; the bigger
vision is real context, not something this plan claims to solve.

## Real, immediate to-do (blocked on you, not automatable)

**Enable SVM Mode in BIOS on this desktop (ASUS PRIME X370-PRO, AMD).**
WSL2 genuinely cannot start without it -- confirmed directly via
`systeminfo`: "Virtualization Enabled In Firmware: No" (everything else
the CPU needs -- VM Monitor Mode Extensions, SLAT, DEP -- is already
fine). This is a firmware-level setting, not something fixable from
Windows or remotely.
- Restart -> press `Del` repeatedly during boot -> if EZ Mode, press
  `F7` for Advanced Mode -> Advanced -> CPU Configuration -> SVM Mode
  -> Enabled -> `F10` to save and exit.
- After rebooting into Windows: `wsl --list --verbose` should then
  successfully start WSL2 instead of erroring on virtualization.
- Deferred to whenever next convenient (2026-08-21 was very late/tired
  by this point) -- real, not forgotten, logged here specifically so it
  doesn't join the round-up's own "built then forgotten" pattern.

## Terms, defined plainly (you said you don't know half of them — no
assumption you should)

- **Distributed compute**: using multiple separate physical computers
  together as if they were one bigger one, coordinating work between
  them instead of each machine working alone.
- **Sharding**: splitting one big task (or one big dataset) into
  smaller pieces ("shards") that different machines work on at the
  same time, then combining the results. Example already in this
  project: 90 instrument benchmarks could be split 45/45 across the
  desktop and laptop instead of one machine doing all 90 in sequence.
- **Node / worker**: one machine participating in the distributed
  system. "Node" is the general term; "worker" is Dask's specific term
  for a machine doing computational work (as opposed to the
  "scheduler," which assigns work to workers).
- **SSH (Secure Shell)**: the standard way to securely log into or run
  commands on another computer over a network. This is the missing
  piece right now — without it, I can message the laptop (via
  team_chat) and hope an agent there picks the task up, but I can't
  directly execute anything on it myself.
- **Tailscale SSH**: Tailscale's own built-in SSH feature. Since both
  machines are already on the same Tailscale network, this is the
  natural way to add real SSH access without separately managing SSH
  keys — it reuses the identity/trust the Tailscale network already
  has. Confirmed just now: neither machine has this turned on yet.
- **Dask**: the Python library already used in this project (real,
  existing: `Windwright/scripts/start_scheduler.py`,
  `laptop-ubuntu-dask-setup.sh`) for exactly the sharding idea above —
  one machine runs a "scheduler" that hands out pieces of work to
  "worker" machines. This already exists and has been used tonight
  (the scheduler was restarted at `tcp://100.69.113.41:8786`); what's
  missing is the laptop reliably being online and connected as a
  worker.

## Current real state (checked directly, not assumed)

- **Tailscale**: both machines are on the same tailnet. Real, working
  when both are online — confirmed tonight via `tailscale status`.
  Right now the laptop shows "offline, last seen 5 days ago."
- **SSH**: not set up at all. No SSH config exists on this desktop, and
  Tailscale SSH is off on both nodes (checked via `tailscale status
  --json` — `SSHHostKeys` is empty for both).
- **Dask**: real, existing infrastructure (not hypothetical) — a
  scheduler script, a laptop setup script written specifically for the
  laptop's fresh-Ubuntu state, and a real, working scheduler process
  that was restarted earlier tonight. This is further along than SSH.
- **Task/agent coordination** (a different layer from raw compute):
  `team_chat.py` + `TEAM_PROTOCOL.md`'s claim/release convention
  already exist and work — this handles "which agent works on what,"
  distinct from "how is one computational task split across hardware."
- **Headless remote execution**: doesn't exist yet. Right now I can run
  `opencode run` headlessly *on this desktop*; I cannot trigger
  anything to run on the laptop directly — only ask (via team_chat) for
  a laptop-side agent to do it, which depends on one actually being
  active there.

## The real gap, stated precisely

Distributed compute (Dask) already has real infrastructure. What's
actually missing, and what's blocking "properly connected and
coordinated," is two separate things:
1. **Reliable connectivity** — the laptop needs to actually be online
   on Tailscale when work needs to happen, not intermittently.
2. **Remote execution** — SSH (or Tailscale SSH specifically) needs to
   actually be turned on, so a task can be *triggered* on the laptop
   from here, not just requested and hoped-for.

These are prerequisites Dask itself needs too, not separate from it —
Dask's own worker-connection setup benefits from the same SSH access
(e.g. to remotely start/restart a worker process without a human at
the laptop's keyboard).

## Plan, in order

### Step 1 — Real remote access, corrected after actually trying it

**Real correction, found by running the command, not assumed:**
`tailscale up --ssh` on this desktop returned "The Tailscale SSH server
is not supported on windows" — verified as a genuine, current Tailscale
limitation (checked against Tailscale's own docs and a live GitHub
issue tracking the feature request), not a one-off error. Tailscale SSH
*server* mode is Linux/macOS-only; Windows can only be an SSH *client*
under Tailscale SSH, never a target. Since both this desktop and the
laptop are Windows, Tailscale's own SSH feature doesn't work for either
end of this pair.

**Real fix:** use Windows' own OpenSSH Server (a built-in optional
Windows feature, separate from Tailscale) as the actual SSH server on
each machine, with Tailscale providing the network layer underneath
(Tailscale-as-client works fine on Windows) — i.e. "SSH over Tailscale,"
not "Tailscale SSH." Concretely: enable the Windows OpenSSH Server
feature, then connect via the machine's Tailscale IP (already known:
this desktop `100.69.113.41`, laptop `100.100.66.117`) using standard
SSH key auth.
- **This desktop**: enable OpenSSH Server (Settings > Optional Features,
  or `Add-WindowsCapability -Online -Name OpenSSH.Server`), generate/
  register a key pair.
- **The laptop**: same, needs to be done there directly since it's
  currently offline and unreachable from here.
- **Verify**: `ssh laptop-tailscale-ip "echo ok"` actually returning
  `ok` from this desktop's Bash tool — a real, checkable fact.

### Step 2 — Real remote-execution test
Once both nodes show SSH-enabled and the laptop is online: a real,
minimal test — `ssh laptop-hostname "echo ok"` (or Tailscale's
equivalent invocation) from this desktop's Bash tool, confirming I can
actually execute a command on the laptop directly, not just message it.
This is the real, concrete unlock: after this works, I can run
`opencode run` (or anything else) on the laptop the same way I do
locally, just prefixed with the remote-execution step.

### Step 3 — Make laptop uptime/connectivity itself reliable
A one-off SSH test doesn't solve "the laptop is offline 5 days later."
Real options, not yet decided (a real choice, not mine to make
unilaterally): Tailscale's own always-on/auto-reconnect settings, a
scheduled task on the laptop that reconnects Tailscale on boot, or
simply a stated norm (the laptop stays connected whenever in use). This
needs your input on what's actually practical for how the laptop
actually gets used day to day.

### Step 4 — Wire SSH-based remote execution into the existing
coordination layer
Once Step 2 works reliably, the real integration point is
`team_chat.py`'s claim/release convention (already exists) plus a new,
real capability: instead of *posting* a task and waiting for a
laptop-side agent to notice, actually *dispatch* it via SSH + headless
`opencode run`/`claude -p`, the same pattern already proven to work
locally tonight. This turns "ask and hope" into "trigger and verify" —
directly closing the exact gap Law 11's AI_FAILURE_PATTERNS entry
already named (headless dispatch prompts must be self-contained; this
extends that same discipline across a real network boundary, not just
within one machine).

### Step 5 — Real Dask worker reliability
With SSH in place, the laptop's Dask worker process can be
remotely (re)started as part of a real startup routine, rather than
depending on the laptop already having it running. This is where actual
sharded compute (splitting real work — acoustics benchmarks,
literature-search queries, model training, image rendering — across
both machines) becomes genuinely usable rather than a scheduler
sitting mostly idle.

### Step 6 — Extend to other repos as a shared pattern, not per-repo
reinvention
The user's own framing: "all repos should have distributed compute" as
a standard feature, not something each repo separately reinvents.
Concretely: once Steps 1-5 are proven working for Windwright's Dask
setup specifically, the *pattern* (Tailscale SSH + a documented
worker-startup routine + the team_chat coordination layer) should be
written up once, generically, and referenced from each repo that needs
it — likely a `docs/DISTRIBUTED_COMPUTE.md` template in lawkeeper's own
`src/guardrail/template/`, matching how governance docs already
propagate via `lawkeeper init`, rather than copy-pasted per repo.

## Volunteer compute — what "safely" actually means (real research, not guessed)

The user's real next-step vision, stated directly: eventually let
friends/acquaintances donate compute to a shared network, **and get
compute back when they need it** — a reciprocal exchange, not one-way
charity (closer to the "membership as reciprocal citizenship" idea
already in [[virtual-nation-cooperative-vision]] than to SETI@home-style
pure donation). This is a real, serious escalation in risk profile from
"me and my own laptop" to "code running on strangers' machines, and
strangers' results feeding back into a shared system" — worth being
concrete and honest about, not just reassuring.

**Critical, direct finding, not softened: Dask itself is not safe for
this.** Dask's scheduler sends *arbitrary pickled Python objects* to
workers for execution — this is real, standard Dask behavior, not a
misconfiguration, and it means any Dask worker (or anyone who can talk
to a Dask scheduler) can execute arbitrary code on every other node in
the cluster. This is fine, even good, for two machines you personally
own and trust completely (the desktop+laptop pair this plan starts
with). It is a genuine, serious security hole the moment a third,
untrusted party's machine joins the same cluster. This is not a
reason to avoid the bigger vision — it's a reason the *mechanism* has
to change before volunteers are involved, not just scaled up.

**The real, established answer is BOINC** (Berkeley Open Infrastructure
for Network Computing) — the actual framework SETI@home, Folding@Home,
and Rosetta@home are built on, decades of real-world volunteer-compute
security experience, not something to reinvent from scratch. Its real
security model, in plain terms:

1. **Sandboxing** — volunteer tasks run under a specially-created,
   restricted account with no access to files outside the sandbox
   directory (the lighter-weight option), or inside a real virtual
   machine via a VirtualBox wrapper for untrusted code specifically
   (the stronger option). Translated: a volunteer's task should never
   be able to touch their real files, browser data, or anything outside
   an isolated box — regardless of what the task's own code does,
   buggy or malicious.
2. **Signed executables** — the actual code volunteers run is digitally
   signed using a separate, offline signing machine, so a compromised
   server can't push malicious code to volunteers even if the main
   infrastructure is breached.
3. **Result verification via replication** — because a volunteer's
   machine and results can never be fully trusted (compromised, buggy,
   or actively lying), the same task gets sent to multiple volunteers
   independently; results are only accepted once independent replicas
   agree. This is also the real, direct answer to the reciprocal-
   exchange question: it's the same mechanism that would need to
   prevent someone falsely claiming they contributed more compute than
   they did ("credit falsification" is BOINC's own documented term for
   exactly this).
4. **Never trust a worker's claimed resource usage** — the same
   replication/verification principle applies to "how much compute did
   this volunteer actually contribute," which matters specifically
   *because* this is reciprocal, not pure donation — fair accounting is
   a real requirement here that pure-donation projects don't have to
   solve as carefully.

**What this means concretely for the plan:** Dask stays the right tool
for Step 5 (you + the laptop, fully trusted). A real volunteer network
is a different, later, separate architecture — most realistically
either adopting BOINC directly (mature, real, already solves this) or
building a much narrower custom system with the same real properties
(sandboxed/containerized execution, signed task code, redundant
verification) rather than extending Dask's trust model outward. Not
attempting to design that system in this pass — flagging it as a real,
separate, substantial piece of work with a real, existing answer to
start from, not an unsolved problem.

## What this plan deliberately does not claim

This is two machines on a home network, not the "compute as public
utility" vision in full — that's real context for *why* this matters,
not a claim that Steps 1-6 build it. The honest, bounded goal here is:
two machines, reliably connected, with real remote execution and real
task sharding — a genuine, working small-scale instance of the
underlying idea, not a rhetorical stand-in for the larger one.

## Immediate next action
Step 1 on this desktop is safe and reversible — can be done right now.
Step 1 on the laptop needs either you or a laptop-side agent session,
since it's currently offline and unreachable from here.
