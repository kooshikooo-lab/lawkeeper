# Executor Backend — Interface Contract (laptop proposal, 2026-08-07)

Companion to ADR-007. This is the interface agreement between the framework core
(desktop, `opencode/framework-mvp/desktop`) and the executor layer (laptop,
`opencode/executor-backend/laptop`). Final ratification via Discussion #23
before executor implementation proceeds (Law 1/2).

## Design goals

1. The executor layer is **framework-agnostic**: it produces an
   `ExecutorResult`; mapping to the framework's `CheckResult`/`Status` is
   explicit and lives in the adapter, not in the executor.
2. Backends are interchangeable behind one `Executor` protocol so `lawkeeper`
   can run a task with a local subprocess or an agent/API backend without
   changing the caller.
3. Everything is testable without network or real agents (the subprocess
   backend is the default test surface; the API backend is mocked in tests).

## Types

```python
# src/guardrail/executor.py

@dataclass
class Task:
    id: str                     # stable identifier
    command: str                # command or tool spec to run
    cwd: Path | None = None     # working directory
    timeout_s: float = 60.0     # hard timeout
    env: dict[str, str] = field(default_factory=dict)  # env overrides
    expected_exit: int | None = None  # None = accept any exit code


@dataclass
class ExecutorResult:
    exit_code: int
    stdout: str
    stderr: str
    duration_s: float
    timed_out: bool

    def to_check_result(self, law: Law) -> CheckResult: ...
    # exit-code/timed_out -> Status (PASS/FAIL/ERROR)


class Executor(Protocol):
    def execute(self, task: Task, context: str = "") -> ExecutorResult: ...
```

Notes:
- `context` is free-form (e.g. the Law description, repo state digest) that a
  backend may use to build a prompt or annotate a run; subprocess backend
  ignores it.
- Exit-code semantics: `0` → PASS, non-zero → FAIL, `timed_out=True` → ERROR.
  A `Task.expected_exit` overrides: match → PASS, mismatch → FAIL.

## Backends

| Backend | Class | Notes |
|---|---|---|
| Subprocess | `SubprocessExecutor` | default; `subprocess.run` with timeout, captures stdout/stderr |
| OpenAI-compatible | `OpenAIExecutor` | endpoint/model via env (`OPENAI_API_KEY`, `LAWKEEPER_MODEL`); prompt built from `Task`+`context`; parses JSON verdict |

Selection: `lawkeeper run --executor subprocess|openai` (default subprocess).

## Wiring point

`guardrail.cli` `run` subcommand builds a `Task` from CLI args, dispatches to the
selected `Executor`, maps `ExecutorResult` → `CheckResult`, and folds into the
existing runner/report (desktop's `GuardrailRunner`).

## Open questions to desktop — answered 2026-08-20

1. Done — pushed (`opencode/framework-mvp/desktop`, commits through
   `a5495a3`), was genuinely the blocker holding this whole merge back.
2. Does not map cleanly, and that's informative: the framework's real
   `Status` (`src/guardrail/core/primitives.py`) is `PASS`/`WARN`/`FAIL`
   — no `ERROR` case — while `ExecutorResult.status` is
   `PASS`/`FAIL`/`ERROR`. A timeout has no honest `Status` equivalent;
   collapsing it into `FAIL` loses real information (a task that failed
   vs. one that never finished are different failure modes a caller
   should be able to tell apart). Given the executor module's own design
   goal #1 above (framework-agnostic, no core imports), the adapter
   belongs in the framework core, not here — confirmed, not just
   deferred by default.
3. `--executor subprocess|openai`, default `subprocess`, as proposed —
   no objection, matches this repo's existing flag-naming convention
   elsewhere (`--check-baseline`, `--check-laws`, etc.).

Ratified as ADR-007 (renumbered from the original ADR-006 proposal —
ADR-006 was independently taken by the reasoning-toggle decision by the
time of this merge; see `docs/ARCHITECTURE_DECISIONS.md`). The interface
and `SubprocessExecutor` are adopted and merged as-is (`src/guardrail/
executor.py`, 11 real tests). The `ExecutorResult`→`CheckResult` adapter
and the `OpenAIExecutor` backend remain genuinely unbuilt — PLANNED, not
implemented — this contract only settles the interface, not the
remaining work.
