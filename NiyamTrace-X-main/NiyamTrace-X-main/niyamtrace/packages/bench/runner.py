"""
packages/bench/runner.py — NiyamTrace-Bench runner (Week 8).

Reads gold-labeled scenarios from data/benchmark/scenarios.json,
runs each through the NiyamTrace pipeline, and compares the gate
decision against the gold expected_verdict.

Design constraints:
  - Deterministic, offline — no LLMs, no external calls.
  - Runs inside the same Python process as the gateway pipeline.
  - Returns a BenchmarkResult dataclass with per-scenario outcomes.

Usage:
    from packages.bench.runner import BenchmarkRunner
    runner = BenchmarkRunner()
    results = runner.run()
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class ScenarioResult:
    """Result for a single benchmark scenario."""

    scenario_id: str
    description: str
    language: str
    tags: list[str]
    expected_verdict: str
    actual_verdict: str
    expected_reason_code: Optional[str]
    actual_reason_code: Optional[str]
    passed: bool
    latency_ms: float
    error: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "scenario_id": self.scenario_id,
            "description": self.description,
            "language": self.language,
            "tags": self.tags,
            "expected_verdict": self.expected_verdict,
            "actual_verdict": self.actual_verdict,
            "expected_reason_code": self.expected_reason_code,
            "actual_reason_code": self.actual_reason_code,
            "passed": self.passed,
            "latency_ms": round(self.latency_ms, 3),
            "error": self.error,
        }


@dataclass
class BenchmarkSummary:
    """Aggregate statistics for a benchmark run."""

    total: int = 0
    passed: int = 0
    failed: int = 0
    errored: int = 0
    accuracy: float = 0.0
    avg_latency_ms: float = 0.0
    # Per-verdict breakdown
    allow_total: int = 0
    allow_correct: int = 0
    block_total: int = 0
    block_correct: int = 0
    escalate_total: int = 0
    escalate_correct: int = 0
    # Per-language breakdown
    accuracy_by_language: dict[str, float] = field(default_factory=dict)
    accuracy_by_tag: dict[str, float] = field(default_factory=dict)
    
    # NiyamTrace-X Metrics
    schema_validity_rate: float = 0.0
    contract_field_f1: float = 0.0
    clarification_resolution_rate: float = 0.0
    effect_equivalence_rate: float = 0.0

    def to_dict(self) -> dict:
        return {
            "total": self.total,
            "passed": self.passed,
            "failed": self.failed,
            "errored": self.errored,
            "accuracy": round(self.accuracy, 4),
            "avg_latency_ms": round(self.avg_latency_ms, 3),
            "verdict_breakdown": {
                "ALLOW": {"total": self.allow_total, "correct": self.allow_correct},
                "BLOCK": {"total": self.block_total, "correct": self.block_correct},
                "ESCALATE": {"total": self.escalate_total, "correct": self.escalate_correct},
                "CLARIFY": {"total": 0, "correct": 0}, # Add Clarify stats
            },
            "accuracy_by_language": {k: round(v, 4) for k, v in self.accuracy_by_language.items()},
            "accuracy_by_tag": {k: round(v, 4) for k, v in self.accuracy_by_tag.items()},
            "niyamtrace_x_metrics": {
                "schema_validity_rate": self.schema_validity_rate,
                "contract_field_f1": self.contract_field_f1,
                "clarification_resolution_rate": self.clarification_resolution_rate,
                "effect_equivalence_rate": self.effect_equivalence_rate
            }
        }


@dataclass
class BenchmarkResult:
    """Full result for one benchmark run."""

    run_id: str
    timestamp: str
    scenarios: list[ScenarioResult]
    summary: BenchmarkSummary

    def to_dict(self) -> dict:
        return {
            "run_id": self.run_id,
            "timestamp": self.timestamp,
            "summary": self.summary.to_dict(),
            "scenarios": [s.to_dict() for s in self.scenarios],
        }


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

_DEFAULT_SCENARIOS_PATH = (
    Path(__file__).parent.parent.parent / "data" / "benchmark" / "scenarios.json"
)


class BenchmarkRunner:
    """
    Runs the NiyamTrace pipeline against gold-labeled scenarios.

    Args:
        scenarios_path: Path to scenarios.json (defaults to repo standard location).
        verbose: Print per-scenario status to stdout.
    """

    def __init__(
        self,
        scenarios_path: Path | str | None = None,
        verbose: bool = True,
    ) -> None:
        self.scenarios_path = Path(scenarios_path or _DEFAULT_SCENARIOS_PATH)
        self.verbose = verbose

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(self, limit: int | None = None) -> BenchmarkResult:
        """Execute all scenarios and return a BenchmarkResult."""
        import uuid
        from datetime import datetime, timezone

        scenarios = self._load_scenarios()
        if limit is not None:
            scenarios = scenarios[:limit]
            
        run_id = str(uuid.uuid4())[:8]
        timestamp = datetime.now(tz=timezone.utc).isoformat()

        results: list[ScenarioResult] = []
        for scenario in scenarios:
            result = self._run_one(scenario)
            results.append(result)
            if self.verbose:
                icon = "PASS" if result.passed else ("ERR " if result.error else "FAIL")
                err_msg = f" | {result.error}" if result.error else ""
                print(
                    f"  [{icon}] {result.scenario_id} "
                    f"({result.expected_verdict} -> {result.actual_verdict}) "
                    f"{result.latency_ms:.1f}ms{err_msg}"
                )
            # Throttle for Gemini Free Tier limit (5 RPM)
            time.sleep(12.5)

        summary = self._compute_summary(results)
        return BenchmarkResult(
            run_id=run_id,
            timestamp=timestamp,
            scenarios=results,
            summary=summary,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _load_scenarios(self) -> list[dict]:
        with open(self.scenarios_path, encoding="utf-8") as f:
            return json.load(f)

    def _run_one(self, scenario: dict) -> ScenarioResult:
        """Run single scenario through pipeline and evaluate."""
        from apps.gateway.pipeline import run_pipeline

        scenario_id = scenario.get("scenario_id", scenario.get("id"))
        expected_verdict = scenario["expected_verdict"]
        expected_reason_code = scenario.get("expected_reason_code")

        t0 = time.perf_counter()
        error: Optional[str] = None
        actual_verdict = "ERROR"
        actual_reason_code: Optional[str] = None

        try:
            trace = run_pipeline(
                raw_text=scenario["raw_text"],
                actor_id=scenario["actor_id"],
                actor_role=scenario["actor_role"],
            )
            # Extract gate decision from the trace events
            gate_event = self._find_event(trace, "gate_decision")
            if gate_event:
                actual_verdict = gate_event.get("decision", "UNKNOWN")
                actual_reason_code = gate_event.get("payload", {}).get("reason_code")
            else:
                # Fall back to evaluation_verdict event
                eval_event = self._find_event(trace, "evaluation_verdict")
                if eval_event:
                    actual_verdict = eval_event.get("payload", {}).get("verdict", "UNKNOWN")

        except Exception as exc:
            error = str(exc)
            actual_verdict = "ERROR"

        latency_ms = (time.perf_counter() - t0) * 1000
        passed = (actual_verdict == expected_verdict) and (error is None)

        return ScenarioResult(
            scenario_id=scenario_id,
            description=scenario.get("description", ""),
            language=scenario.get("language", "unknown"),
            tags=scenario.get("tags", []),
            expected_verdict=expected_verdict,
            actual_verdict=actual_verdict,
            expected_reason_code=expected_reason_code,
            actual_reason_code=actual_reason_code,
            passed=passed,
            latency_ms=latency_ms,
            error=error,
        )

    @staticmethod
    def _find_event(trace: list[dict], event_type: str) -> dict | None:
        """Find first event of given type in trace list."""
        for event in trace:
            if isinstance(event, dict) and event.get("event_type") == event_type:
                return event
        return None

    @staticmethod
    def _compute_summary(results: list[ScenarioResult]) -> BenchmarkSummary:
        """Compute aggregate statistics."""
        summary = BenchmarkSummary()
        summary.total = len(results)
        summary.passed = sum(1 for r in results if r.passed)
        summary.errored = sum(1 for r in results if r.error is not None)
        summary.failed = summary.total - summary.passed - summary.errored
        summary.accuracy = summary.passed / summary.total if summary.total > 0 else 0.0
        summary.avg_latency_ms = (
            sum(r.latency_ms for r in results) / len(results) if results else 0.0
        )

        # Per-verdict breakdown
        for r in results:
            if r.expected_verdict == "ALLOW":
                summary.allow_total += 1
                if r.passed:
                    summary.allow_correct += 1
            elif r.expected_verdict == "BLOCK":
                summary.block_total += 1
                if r.passed:
                    summary.block_correct += 1
            elif r.expected_verdict == "ESCALATE":
                summary.escalate_total += 1
                if r.passed:
                    summary.escalate_correct += 1

        # Per-language breakdown
        by_lang: dict[str, list[bool]] = {}
        for r in results:
            by_lang.setdefault(r.language, []).append(r.passed)
        summary.accuracy_by_language = {
            lang: sum(outcomes) / len(outcomes)
            for lang, outcomes in by_lang.items()
        }

        # Per-tag breakdown (a scenario can have multiple tags)
        by_tag: dict[str, list[bool]] = {}
        for r in results:
            for tag in r.tags:
                by_tag.setdefault(tag, []).append(r.passed)
        summary.accuracy_by_tag = {
            tag: sum(outcomes) / len(outcomes)
            for tag, outcomes in by_tag.items()
        }

        return summary
