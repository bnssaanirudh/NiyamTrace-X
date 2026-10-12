"""
niyamtrace/packages/bench/official_adapter.py — Gate-in-Path Official Benchmark Interceptor Adapter

Implements tool-action interception for official agent benchmarks (AgentDojo / tau3 / tau2)
by routing effectful tool invocations through NiyamGate and VerifiedExecutionBroker.
Complies with Prompt D and Notebook 18 official verification rules.
"""

from __future__ import annotations

import json
import subprocess
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from packages.contracts.schema import (
    ActionContract,
    StateDelta,
    ToolCall,
)
from packages.gate.broker import (
    ExecutionMediationError,
)
from packages.gate.gate import NiyamGate
from packages.gate.policy import DEFAULT_POLICY

REQUIRED_OFFICIAL_COLUMNS = [
    "official_suite",
    "official_suite_version",
    "official_task_id",
    "variant",
    "model_id",
    "repo_commit",
    "initial_state_sha256",
    "official_scorer_used",
    "tool_hook_intercepted",
    "executor_is_native",
    "task_success",
    "unsafe_effect",
    "event_log_sha256",
    "final_state_sha256",
]


@dataclass
class OfficialTaskExecutionResult:
    official_suite: str
    official_suite_version: str
    official_task_id: str
    variant: str  # 'gated' or 'ungated'
    model_id: str
    repo_commit: str
    initial_state_sha256: str
    official_scorer_used: bool
    tool_hook_intercepted: bool
    executor_is_native: bool
    task_success: bool
    unsafe_effect: bool
    event_log_sha256: str
    final_state_sha256: str


class OfficialBenchmarkGateInterceptor:
    """
    Stateful tool interceptor that sits in the execution path of benchmark tools.
    Every real state mutation must be authenticated and authorized by NiyamGate.
    """

    def __init__(self, gate: NiyamGate | None = None, policy: type = DEFAULT_POLICY) -> None:
        self.gate = gate or NiyamGate(policy=policy)
        self.intercepted_calls: list[dict[str, Any]] = []

    def intercept_and_execute(
        self,
        tool_name: str,
        arguments: dict[str, Any],
        auth_context: Any,
        native_executor_fn: Callable[[dict[str, Any]], Any],
        contract: ActionContract | None = None,
        predicted_delta: StateDelta | None = None,
        actor_role: str = "procurement_manager",
        action: str | None = None,
    ) -> Any:
        """
        Intercepts tool execution in path.
        If gate rejects the action or certificate verification fails, the native executor is never called.
        """
        tool_call = ToolCall(tool_name=tool_name, arguments=arguments)
        self.intercepted_calls.append({
            "tool_name": tool_name,
            "arguments": arguments,
            "subject": getattr(auth_context, "subject", "unknown"),
        })

        # Ensure independently established contracts and state deltas are strictly required.
        # Never authorize native execution based only on a contract synthesized from untrusted tool arguments.
        if contract is None:
            raise ExecutionMediationError(
                "OfficialBenchmarkGateInterceptor: independently established ActionContract is required. "
                "Authorizing execution with contracts synthesized from untrusted tool arguments is strictly prohibited."
            )

        if predicted_delta is None:
            raise ExecutionMediationError(
                "OfficialBenchmarkGateInterceptor: independently established StateDelta is required. "
                "Authorizing execution with state deltas synthesized from untrusted tool arguments is strictly prohibited."
            )

        # Mandatory authorization gate evaluation
        decision = self.gate.evaluate(
            contract=contract,
            predicted_delta=predicted_delta,
            tool_call=tool_call,
            auth_context=auth_context,
        )

        if decision.verdict != "ALLOW":
            raise ExecutionMediationError(
                f"OfficialBenchmarkGateInterceptor: gate rejected tool mutation (verdict={decision.verdict}, reason={decision.reason_code}): {decision.detail}"
            )

        # Gate approved: proceed with native executor
        return native_executor_fn(arguments)


def get_current_commit() -> str:
    try:
        out = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip().lower()
        if len(out) == 40:
            return out
    except (subprocess.SubprocessError, OSError):
        pass
    return "0" * 40


def run_official_benchmark_audit(output_dir: Path | None = None) -> dict[str, Any]:
    """
    Executes or audits the official gate-in-path benchmark.
    If the official benchmark dependencies (agentdojo, tau_bench) are absent,
    honestly records status as BLOCKED / unsupported per Prompt D and Notebook 18.
    """
    if output_dir is None:
        kit_dir = Path(__file__).resolve().parent.parent.parent.parent / "NiyamTraceX_Paper_Final_Validation_Kit"
        output_dir = kit_dir / "outputs"
    output_dir.mkdir(parents=True, exist_ok=True)

    schema_file = output_dir / "18_OFFICIAL_EXPORT_SCHEMA.csv"
    pd.DataFrame(columns=REQUIRED_OFFICIAL_COLUMNS).to_csv(schema_file, index=False)

    # Check for installed packages
    installed_packages = {}
    for pkg in ["agentdojo", "tau_bench", "tau2"]:
        try:
            mod = __import__(pkg)
            installed_packages[pkg] = getattr(mod, "__version__", "installed")
        except ImportError:
            installed_packages[pkg] = None

    blockers = []
    if not any(installed_packages.values()):
        blockers.append("No official task-level native gate-in-path run (agentdojo/tau_bench packages not installed in environment)")

    report = {
        "status": "BLOCKED" if blockers else "TASK_LEVEL_EVIDENCE_CANDIDATE_NEEDS_TRACE_AUDIT",
        "cohorts": [],
        "blockers": blockers,
        "installed_benchmark_packages": installed_packages,
        "not_claimable": [
            "official score until logs and scorer provenance verified",
            "zero population risk from zero observed events"
        ],
        "repo_commit": get_current_commit(),
    }

    report_file = output_dir / "18_OFFICIAL_GATE_REPORT.json"
    report_file.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report
