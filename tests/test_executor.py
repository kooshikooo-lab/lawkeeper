"""Tests for the executor layer (ADR-007).

Covers Task/ExecutorResult semantics and the SubprocessExecutor backend:
  - PASS/FAIL/ERROR mapping (0 -> PASS, non-zero -> FAIL, timeout -> ERROR)
  - timeout handling with a sleeping command
  - OSError handling (nonexistent binary)
  - env/cwd passthrough
  - protocol conformance (a fake backend can stand in for the OpenAI path)
"""
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src'))

import pytest

from guardrail.executor import Executor, ExecutorResult, SubprocessExecutor, Task


class TestExecutorResultStatus:
    def test_exit_zero_is_pass(self):
        assert ExecutorResult(0, "", "", 0.01).status == "PASS"

    def test_exit_nonzero_is_fail(self):
        assert ExecutorResult(1, "", "boom", 0.01).status == "FAIL"

    def test_timeout_is_error(self):
        assert ExecutorResult(-1, "", "", 5.0, timed_out=True).status == "ERROR"

    def test_combined_output_joins_streams(self):
        r = ExecutorResult(0, "out", "err", 0.01)
        assert r.combined_output == "out\nerr"


class TestSubprocessExecutor:
    @pytest.fixture
    def exe(self):
        return SubprocessExecutor(shell=True)

    def test_success(self, exe):
        r = exe.execute(Task(id="ok", command="echo hi", timeout_s=5))
        assert r.status == "PASS"
        assert "hi" in r.stdout

    def test_failure(self, exe):
        r = exe.execute(Task(id="fail", command="exit 3", timeout_s=5))
        assert r.status == "FAIL"
        assert r.exit_code == 3

    def test_timeout(self):
        py = sys.executable
        exe = SubprocessExecutor(shell=False)
        r = exe.execute(Task(id="slow", command=[py, "-c", "import time; time.sleep(5)"],
                             timeout_s=0.3))
        assert r.timed_out is True
        assert r.status == "ERROR"

    def test_env_passthrough(self):
        py = sys.executable
        exe = SubprocessExecutor(shell=False)
        r = exe.execute(Task(id="env",
                             command=[py, "-c", "import os; print(os.environ['FOO'])"],
                             env={"FOO": "bar"}, timeout_s=5))
        assert r.status == "PASS"
        assert "bar" in r.stdout

    def test_cwd(self):
        exe = SubprocessExecutor(shell=True)
        here = Path(__file__).resolve().parent
        r = exe.execute(Task(id="cwd", command="cd && pwd" if os.name != "nt" else "cd", cwd=here, timeout_s=5))
        assert r.status == "PASS"

    def test_nonexistent_binary_oserror(self):
        exe = SubprocessExecutor(shell=False)
        r = exe.execute(Task(id="nope", command="definitely-not-a-real-binary-xyz", timeout_s=5))
        assert r.exit_code == -2
        assert r.status == "FAIL"


class TestExecutorProtocol:
    """A stand-in backend must satisfy the Executor protocol (the OpenAI
    executor will implement the same interface)."""

    class FakeExecutor:
        def execute(self, task: Task, context: str = "") -> ExecutorResult:
            return ExecutorResult(0, f"ran:{task.id}:{context}", "", 0.01)

    def test_fake_backend_conforms(self):
        exe: Executor = self.FakeExecutor()
        r = exe.execute(Task(id="t1", command="echo hi"), context="ctx")
        assert r.stdout == "ran:t1:ctx"
