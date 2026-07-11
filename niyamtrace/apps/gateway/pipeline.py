"""
apps/gateway/pipeline.py — NiyamTrace Pipeline Orchestrator

Runs one request through the full pipeline in the correct event order:
  input_received → contract_extracted → retrieval_completed →
  policy_evaluated → tool_proposed → tool_simulated → gate_decision →
  tool_executed (if ALLOW) → evaluation_verdict

All 9 events are emitted to the TraceWriter with the full envelope from
Section 5 of the NiyamTrace brief.

Week 3 changes:
  - language_profile now comes from real MultilingualIntake (not hardcoded).
  - normalized_text in the contract is produced by the TextNormalizer.
  - Language/script detection covers en, hi_rom, te, te_rom.

Week 4 changes:
  - Contract extraction uses real NLP SlotParser (XLM-R mock) instead of hardcoded stub.

Week 5 changes:
  - Event 3 (retrieval_completed) calls real EvidenceRetriever + NLIEngine.
  - Evidence verdict is SUPPORT | CONTRADICT | INSUFFICIENT — no longer STUB.
  - Gate Check 5 now receives a real verdict and can block/escalate on evidence.

Remaining stubs:
  - No LLM calls. Entire pipeline is deterministic and offline.

Status: IMPLEMENTED (Week 5) — full pipeline with real evidence grounding.
"""

from __future__ import annotations

import sqlite3
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from packages.contracts.schema import (
    GateDecision,
    ActionContract,
    StateDelta,
    TemporalRange,
    ToolCall,
    TraceEvent,
)
from packages.gate.executor import ERPExecutor
from packages.gate.gate import NiyamGate
from packages.gate.policy import DEFAULT_POLICY, EvidenceVerdict
from packages.gate.simulator import ShadowSimulator
from packages.gate.tool_schemas import schema_hash, validate_tool_call
from packages.lake.writer import TraceWriter, make_event
from packages.nlp.intake import MultilingualIntake
from packages.nlp.compiler import NiyamCompiler
from packages.evidence.retriever import EvidenceRetriever
from packages.evidence.nli import NLIEngine
from data.synthetic.erp import SEED_SNAPSHOT_ID

_INTAKE = MultilingualIntake()  # stateless; safe to share across requests
_COMPILER = NiyamCompiler()
_RETRIEVER = EvidenceRetriever()  # loads policy_docs.json once at startup (Week 5)
_NLI = NLIEngine()                # stateless rule-based NLI (Week 5)

# ---------------------------------------------------------------------------
# Pipeline request / response types
# ---------------------------------------------------------------------------


class PipelineRequest:
    def __init__(
        self,
        raw_text: str,
        actor_id: str,
        actor_role: str,
        task_id: str | None = None,
        traces_dir: Path | None = None,
    ) -> None:
        self.raw_text = raw_text
        self.actor_id = actor_id
        self.actor_role = actor_role
        self.task_id = task_id or str(uuid.uuid4())
        self.traces_dir = traces_dir


class PipelineResult:
    def __init__(
        self,
        trace_id: str,
        task_id: str,
        contract: ActionContract,
        tool_call: ToolCall,
        predicted_delta: StateDelta,
        gate_decision: GateDecision,
        actual_delta: StateDelta | None,
        trace_path: Path,
        events: list[TraceEvent],
    ) -> None:
        self.trace_id = trace_id
        self.task_id = task_id
        self.contract = contract
        self.tool_call = tool_call
        self.predicted_delta = predicted_delta
        self.gate_decision = gate_decision
        self.actual_delta = actual_delta
        self.trace_path = trace_path
        self.events = events


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------


class NiyamPipeline:
    """
    Orchestrates one request end-to-end through the full NiyamTrace pipeline.
    Each pipeline instance is stateless; the ERP connection is injected so
    tests can provide a pre-seeded in-memory or file-backed DB.
    """

    def __init__(
        self,
        erp_conn: sqlite3.Connection,
        traces_dir: Path | None = None,
        policy: type = DEFAULT_POLICY,
        compiler: NiyamCompiler | None = None,
    ) -> None:
        self._erp_conn = erp_conn
        self._traces_dir = traces_dir
        self._gate = NiyamGate(policy=policy)
        self._simulator = ShadowSimulator(erp_conn)
        self._executor = ERPExecutor(erp_conn)
        self._compiler = compiler or _COMPILER

    def run(self, req: PipelineRequest) -> PipelineResult:
        trace_id = str(uuid.uuid4())

        with TraceWriter(trace_id=trace_id, traces_dir=self._traces_dir) as writer:
            t_pipeline_start = time.perf_counter()

            # ---------------------------------------------------------------
            # Week 3: Run multilingual intake BEFORE building the envelope
            # so that language_profile is real data, not the hardcoded stub.
            # ---------------------------------------------------------------
            t_intake_start = time.perf_counter()
            intake_result = _INTAKE.process(req.raw_text)
            intake_latency_ms = (time.perf_counter() - t_intake_start) * 1000

            # Common envelope fields shared by all events in this trace
            envelope: dict[str, Any] = {
                "trace_id": trace_id,
                "task_id": req.task_id,
                "parser_version": "0.3.0-intake+0.1.0-hardcoded-extractor",
                "policy_bundle_hash": DEFAULT_POLICY.bundle_hash(),
                "data_snapshot_id": SEED_SNAPSHOT_ID,
                "language_profile": intake_result.language_profile,  # REAL (Week 3)
                "model_version": "none",
                "prompt_commit": "none",
            }

            # ---------------------------------------------------------------
            # Event 1: input_received
            # ---------------------------------------------------------------
            t0 = time.perf_counter()
            raw_hash = _sha16(req.raw_text)
            writer.write(
                make_event(
                    **envelope,
                    event_type="input_received",
                    raw_hash=raw_hash,
                    payload={
                        "raw_text": req.raw_text,
                        "actor_id": req.actor_id,
                        "actor_role": req.actor_role,
                        "intake_latency_ms": intake_latency_ms,
                        "normalized_text": intake_result.normalized_text,
                        "primary_lang": intake_result.primary_lang,
                        "applied_maps": intake_result.normalization.get("applied_maps", []),
                    },
                    latency_ms=(time.perf_counter() - t0) * 1000,
                )
            )

            # ---------------------------------------------------------------
            # Event 2: contract_extracted
            # Real NLP Compiler replaces the Week 2/4 parser.
            # ---------------------------------------------------------------
            t0 = time.perf_counter()
            compiler_result = self._compiler.compile(
                req.actor_id, req.actor_role, req.raw_text, intake_result
            )
            
            contract = compiler_result.contract
            
            if not contract:
                # Compilation failed (TypeCheck, EntityLink, or Extract)
                decision = GateDecision(
                    verdict="CLARIFY" if compiler_result.clarification_prompt else "BLOCK",
                    reason_code=compiler_result.error_stage or "COMPILER_ERROR",
                    detail=compiler_result.error_detail or "Failed to extract contract",
                    check_results=[],
                    clarification_prompt=compiler_result.clarification_prompt
                )
                writer.write(
                    make_event(
                        **envelope,
                        event_type="gate_decision",
                        payload={"decision": decision.model_dump()},
                        decision=decision.verdict,
                        latency_ms=(time.perf_counter() - t0) * 1000,
                    )
                )
                return PipelineResult(
                    trace_id=trace_id,
                    task_id=req.task_id,
                    contract=None,  # type: ignore
                    tool_call=None, # type: ignore
                    predicted_delta=None, # type: ignore
                    gate_decision=decision,
                    actual_delta=None,
                    trace_path=writer.path,
                    events=writer.events(),
                )

            # Update parser version in the envelope to match what the compiler used
            envelope["parser_version"] = contract.parser_version
            
            writer.write(
                make_event(
                    **envelope,
                    event_type="contract_extracted",
                    raw_hash=raw_hash,
                    normalized_hash=_sha16(contract.normalized_text),
                    payload={
                        "contract": contract.model_dump(),
                        "intake_primary_lang": intake_result.primary_lang,
                        "intake_normalized_text": intake_result.normalized_text,
                    },
                    latency_ms=(time.perf_counter() - t0) * 1000,
                )
            )

            # ---------------------------------------------------------------
            # Event 3: retrieval_completed  [IMPLEMENTED — Week 5]
            # Real EvidenceRetriever + NLI Engine. ACL-filtered.
            # ---------------------------------------------------------------
            t0 = time.perf_counter()
            query_text = f"{contract.intent} {contract.normalized_text}"
            retrieved_chunks = _RETRIEVER.retrieve(
                query=query_text,
                actor_role=req.actor_role,
                top_k=3,
            )
            evidence_verdict_raw, evidence_reason = _NLI.classify(
                intent=contract.intent,
                actor_role=req.actor_role,
                chunks=retrieved_chunks,
            )
            # Gate policy.py expects EvidenceVerdict literal — cast to it
            evidence_verdict: EvidenceVerdict = evidence_verdict_raw  # type: ignore[assignment]
            writer.write(
                make_event(
                    **envelope,
                    event_type="retrieval_completed",
                    payload={
                        "verdict": evidence_verdict,
                        "evidence_reason": evidence_reason,
                        "retrieved_chunks": [c.to_dict() for c in retrieved_chunks],
                        "retrieval_note": "NiyamEvidence — ACL-filtered retriever + deterministic NLI (Week 5)",
                    },
                    latency_ms=(time.perf_counter() - t0) * 1000,
                )
            )

            # ---------------------------------------------------------------
            # Event 4: policy_evaluated
            # ---------------------------------------------------------------
            writer.write(
                make_event(
                    **envelope,
                    event_type="policy_evaluated",
                    payload={
                        "policy_bundle": "0.2.0-hardcoded",
                        "actor_role": req.actor_role,
                        "action": contract.intent,
                        "approval_state": "NONE",
                    },
                    latency_ms=(time.perf_counter() - t0) * 1000,
                )
            )

            # ---------------------------------------------------------------
            # Event 5: tool_proposed
            # ---------------------------------------------------------------
            t0 = time.perf_counter()
            tool_call = _build_tool_call(contract)
            tool_sh = schema_hash("archive_invoices")
            envelope["tool_schema_hash"] = tool_sh

            try:
                validate_tool_call({"tool_name": tool_call.tool_name, "arguments": tool_call.arguments})
                schema_valid = True
                schema_error = None
            except Exception as exc:
                schema_valid = False
                schema_error = str(exc)

            writer.write(
                make_event(
                    **envelope,
                    event_type="tool_proposed",
                    payload={
                        "tool_call": {"tool_name": tool_call.tool_name, "arguments": tool_call.arguments},
                        "schema_valid": schema_valid,
                        "schema_error": schema_error,
                    },
                    latency_ms=(time.perf_counter() - t0) * 1000,
                )
            )

            if not schema_valid:
                # Hard block before simulation — malformed tool call
                _write_gate_block(writer, envelope, "TOOL_SCHEMA_INVALID", schema_error or "")
                return _early_exit(trace_id, req, contract, tool_call, writer)

            # ---------------------------------------------------------------
            # Event 6: tool_simulated
            # ---------------------------------------------------------------
            t0 = time.perf_counter()
            predicted_delta = self._simulator.predict(tool_call)
            writer.write(
                make_event(
                    **envelope,
                    event_type="tool_simulated",
                    payload={
                        "predicted_record_ids": predicted_delta.affected_record_ids,
                        "estimated_row_count": predicted_delta.estimated_row_count,
                        "record_deltas": [d.model_dump() for d in predicted_delta.record_deltas],
                    },
                    latency_ms=(time.perf_counter() - t0) * 1000,
                )
            )

            # ---------------------------------------------------------------
            # Event 7: gate_decision
            # ---------------------------------------------------------------
            t0 = time.perf_counter()
            gate_decision = self._gate.evaluate(
                contract=contract,
                predicted_delta=predicted_delta,
                tool_call=tool_call,
                evidence_verdict=evidence_verdict,
            )
            writer.write(
                make_event(
                    **envelope,
                    event_type="gate_decision",
                    decision=gate_decision.verdict,
                    payload={
                        "verdict": gate_decision.verdict,
                        "reason_code": gate_decision.reason_code,
                        "detail": gate_decision.detail,
                        "check_results": [r.model_dump() for r in gate_decision.check_results],
                        "correction": gate_decision.correction,
                        "gate_latency_ms": gate_decision.latency_ms,
                    },
                    latency_ms=(time.perf_counter() - t0) * 1000,
                )
            )

            actual_delta: StateDelta | None = None

            # ---------------------------------------------------------------
            # Event 8: tool_executed  (only if ALLOW)
            # ---------------------------------------------------------------
            if gate_decision.verdict == "ALLOW":
                t0 = time.perf_counter()
                actual_delta = self._executor.execute(tool_call)
                writer.write(
                    make_event(
                        **envelope,
                        event_type="tool_executed",
                        decision="EXECUTED",
                        payload={
                            "actual_record_ids": actual_delta.affected_record_ids,
                            "actual_row_count": actual_delta.estimated_row_count,
                            "record_deltas": [d.model_dump() for d in actual_delta.record_deltas],
                        },
                        latency_ms=(time.perf_counter() - t0) * 1000,
                    )
                )
            else:
                # Emit a skipped tool_executed event so trace always has 9 event types
                writer.write(
                    make_event(
                        **envelope,
                        event_type="tool_executed",
                        decision="SKIPPED_GATE_BLOCK",
                        payload={"reason": gate_decision.reason_code},
                    )
                )

            # ---------------------------------------------------------------
            # Event 9: evaluation_verdict
            # ---------------------------------------------------------------
            t_total = (time.perf_counter() - t_pipeline_start) * 1000

            fidelity: float | None = None
            if actual_delta is not None and predicted_delta is not None:
                fidelity = _compute_fidelity(predicted_delta, actual_delta)

            writer.write(
                make_event(
                    **envelope,
                    event_type="evaluation_verdict",
                    decision=gate_decision.verdict,
                    payload={
                        "gate_verdict": gate_decision.verdict,
                        "simulator_fidelity": fidelity,
                        "total_pipeline_latency_ms": t_total,
                        "predicted_count": predicted_delta.estimated_row_count,
                        "actual_count": actual_delta.estimated_row_count if actual_delta else None,
                    },
                    latency_ms=t_total,
                )
            )

            return PipelineResult(
                trace_id=trace_id,
                task_id=req.task_id,
                contract=contract,
                tool_call=tool_call,
                predicted_delta=predicted_delta,
                gate_decision=gate_decision,
                actual_delta=actual_delta,
                trace_path=writer.path,
                events=writer.events(),
            )





def _build_tool_call(contract: ActionContract) -> ToolCall:
    """
    Build a ToolCall from the contract slots.
    """
    args = {}
    if "VENDOR_ID" in contract.slots:
        args["vendor_id"] = int(contract.slots["VENDOR_ID"])
    if "MONTH" in contract.slots:
        args["month"] = int(contract.slots["MONTH"])
    if "YEAR" in contract.slots:
        args["year"] = int(contract.slots["YEAR"])

    if contract.intent == "invoice.archive":
        return ToolCall(
            tool_name="archive_invoices",
            arguments=args,
            schema_version="1.0",
            tool_schema_hash=schema_hash("archive_invoices"),
        )
    
    # Placeholder for newer tool logic
    return ToolCall(
        tool_name="unknown_tool",
        arguments=contract.slots,
        schema_version="1.0",
        tool_schema_hash="unknown",
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _sha16(text: str) -> str:
    import hashlib
    return hashlib.sha256(text.encode()).hexdigest()[:16]


def _compute_fidelity(predicted: StateDelta, actual: StateDelta) -> float:
    """
    Simulator fidelity: what fraction of predicted record IDs exactly match
    the actual affected record IDs?
    Perfect fidelity = 1.0; mismatch produces < 1.0.
    """
    pred_ids = set(predicted.affected_record_ids)
    actual_ids = set(actual.affected_record_ids)
    if not pred_ids and not actual_ids:
        return 1.0
    union = pred_ids | actual_ids
    intersection = pred_ids & actual_ids
    return len(intersection) / len(union)


def _write_gate_block(
    writer: TraceWriter,
    envelope: dict[str, Any],
    reason_code: str,
    detail: str,
) -> None:
    writer.write(
        make_event(
            **envelope,
            event_type="gate_decision",
            decision="BLOCK",
            payload={"verdict": "BLOCK", "reason_code": reason_code, "detail": detail},
        )
    )


def _early_exit(
    trace_id: str,
    req: PipelineRequest,
    contract: ActionContract,
    tool_call: ToolCall,
    writer: TraceWriter,
) -> PipelineResult:
    """Return a minimal PipelineResult when pipeline exits early (e.g. schema error)."""
    empty_delta = StateDelta(
        affected_record_ids=[], record_deltas=[], table="vendor_invoices", estimated_row_count=0
    )
    block_decision = GateDecision(
        verdict="BLOCK",
        reason_code="TOOL_SCHEMA_INVALID",
        detail="Pipeline exited early due to tool schema validation failure.",
        check_results=[],
    )
    writer.write(
        make_event(
            trace_id=trace_id,
            task_id=req.task_id,
            event_type="tool_executed",
            decision="SKIPPED_EARLY_EXIT",
        )
    )
    writer.write(
        make_event(
            trace_id=trace_id,
            task_id=req.task_id,
            event_type="evaluation_verdict",
            decision="BLOCK",
        )
    )
    return PipelineResult(
        trace_id=trace_id,
        task_id=req.task_id,
        contract=contract,
        tool_call=tool_call,
        predicted_delta=empty_delta,
        gate_decision=block_decision,
        actual_delta=None,
        trace_path=writer.path,
        events=writer.events(),
    )


# ---------------------------------------------------------------------------
# Convenience wrapper for benchmark / test use
# ---------------------------------------------------------------------------


_DEFAULT_TRACES_DIR = Path(__file__).parent.parent.parent / "traces" / "bronze"


def run_pipeline(
    raw_text: str,
    actor_id: str,
    actor_role: str,
    task_id: str | None = None,
    traces_dir: Path | None = None,
) -> list[dict]:
    """
    High-level convenience function used by the benchmark runner and tests.

    Creates a fresh in-memory ERP connection, runs the full pipeline,
    and returns the trace events as a list of plain Python dicts.

    Args:
        raw_text:   The raw user instruction text.
        actor_id:   Identifier of the requesting agent/user.
        actor_role: Role of the requesting agent (procurement_manager, etc.).
        task_id:    Optional task identifier (auto-generated if None).
        traces_dir: Directory to write JSONL trace files (defaults to traces/bronze/).

    Returns:
        List of serialized TraceEvent dicts in pipeline order.
    """
    from data.synthetic.erp import seed_fresh

    erp_conn = seed_fresh()
    pipeline = NiyamPipeline(
        erp_conn=erp_conn,
        traces_dir=traces_dir or _DEFAULT_TRACES_DIR,
    )
    req = PipelineRequest(
        raw_text=raw_text,
        actor_id=actor_id,
        actor_role=actor_role,
        task_id=task_id,
    )
    result = pipeline.run(req)
    # Serialize TraceEvent objects to dicts for benchmark runner compatibility
    return [ev.model_dump() if hasattr(ev, "model_dump") else dict(ev) for ev in result.events]

