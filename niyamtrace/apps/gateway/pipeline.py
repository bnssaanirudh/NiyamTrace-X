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

import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from data.synthetic.erp import SEED_SNAPSHOT_ID
from packages.auth.models import AuthorizationContext
from packages.contracts.schema import (
    ActionContract,
    GateDecision,
    StateDelta,
    ToolCall,
    TraceEvent,
)
from packages.evidence.nli import NLIEngine
from packages.evidence.retriever import EvidenceRetriever
from packages.gate.broker import (
    BrokerVerificationError,
    ExecutionMediationError,
    SecurityError,
    VerifiedExecutionBroker,
)
from packages.gate.executor import ERPExecutor
from packages.gate.gate import NiyamGate
from packages.gate.policy import DEFAULT_POLICY, EvidenceVerdict
from packages.gate.simulator import ShadowSimulator
from packages.gate.tool_schemas import ToolSchemaValidationError, schema_hash, validate_tool_call
from packages.lake.writer import TraceWriter, make_event
from packages.nlp.compiler import NiyamCompiler
from packages.nlp.intake import MultilingualIntake
from packages.observability.logger import current_trace_id, get_logger
from packages.storage.models import PendingApproval
from packages.storage.session import SessionManager, StateMismatchError

logger = get_logger(__name__)

_INTAKE = MultilingualIntake()  # stateless; safe to share across requests
_COMPILER = NiyamCompiler()
_RETRIEVER = EvidenceRetriever()  # loads policy_docs.json once at startup (Week 5)
_NLI = NLIEngine()                # stateless rule-based NLI (Week 5)

# ---------------------------------------------------------------------------
# Pipeline request / response types
# ---------------------------------------------------------------------------


class PipelineRequest:
    """Immutable pipeline request carrying the full authenticated context.

    Security invariant: actor_id, actor_role, auth_context must always come
    from a verified Principal — never from caller-supplied request text.
    """

    def __init__(
        self,
        raw_text: str,
        actor_id: str,
        actor_role: str,
        task_id: str | None = None,
        traces_dir: Path | None = None,
        reference_dt: datetime | None = None,
        approval_id: str | None = None,
        auth_context: AuthorizationContext | None = None,
    ) -> None:
        self.raw_text = raw_text
        self.actor_id = actor_id
        self.actor_role = actor_role  # display only — use auth_context for authz
        self.task_id = task_id or str(uuid.uuid4())
        self.approval_id = approval_id
        self.reference_dt = reference_dt
        self.traces_dir = traces_dir
        
        if auth_context is None:
            from packages.auth.models import AuthorizationContext, Principal
            principal = Principal(
                subject=actor_id,
                tenant_id="acme",
                roles=frozenset([actor_role]) if actor_role else frozenset(),
                scopes=frozenset(["all"])
            )
            self.auth_context = AuthorizationContext.from_principal(principal)
        else:
            self.auth_context = auth_context


class PipelineResult:
    def __init__(
        self,
        trace_id: str,
        task_id: str,
        contract: ActionContract,
        tool_calls: list[ToolCall],
        predicted_delta: StateDelta,
        gate_decision: GateDecision,
        actual_delta: StateDelta | None,
        trace_path: Path,
        events: list[TraceEvent],
    ) -> None:
        self.trace_id = trace_id
        self.task_id = task_id
        self.contract = contract
        self.tool_calls = tool_calls
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
        engine: AsyncEngine,
        traces_dir: Path | None = None,
        policy: type = DEFAULT_POLICY,
        compiler: NiyamCompiler | None = None,
    ) -> None:
        self._engine = engine
        self._session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
        self._traces_dir = traces_dir
        self._gate = NiyamGate(policy=policy)
        self._compiler = compiler or _COMPILER

    async def run(self, req: PipelineRequest) -> PipelineResult:
        trace_id = str(uuid.uuid4())
        current_trace_id.set(trace_id)
        logger.info(f"Starting pipeline for request: {req.task_id} by {req.actor_role}")

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
                "parser_version": self._compiler.parser_version,
                "policy_bundle_hash": DEFAULT_POLICY.policy_hash,
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
                req.actor_id, req.actor_role, req.raw_text, intake_result, req.reference_dt
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
                    tool_calls=[],
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
                        "policy_bundle": DEFAULT_POLICY.policy_hash,
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
            tool_calls = _build_tool_calls(contract)
            
            # Schema hash is now a registry-wide hash
            envelope["tool_schema_hash"] = schema_hash()

            schema_valid = True
            schema_error = None
            for tc in tool_calls:
                try:
                    validate_tool_call({"tool_name": tc.tool_name, "arguments": tc.arguments})
                except (ToolSchemaValidationError, ValueError, KeyError, TypeError) as exc:
                    schema_valid = False
                    schema_error = str(exc)
                    break

            writer.write(
                make_event(
                    **envelope,
                    event_type="tool_proposed",
                    payload={
                        "tool_calls": [{"tool_name": tc.tool_name, "arguments": tc.arguments} for tc in tool_calls],
                        "schema_valid": schema_valid,
                        "schema_error": schema_error,
                    },
                    latency_ms=(time.perf_counter() - t0) * 1000,
                )
            )

            if not schema_valid:
                # Hard block before simulation — malformed tool call
                _write_gate_block(writer, envelope, "TOOL_SCHEMA_INVALID", schema_error or "")
                return _early_exit(trace_id, req, contract, tool_calls, writer, envelope)

            # ---------------------------------------------------------------
            # Phase 9: Transactional Boundary for Simulate + Gate + Execute
            # ---------------------------------------------------------------
            try:
                async with self._session_factory() as db_session:
                    session_manager = SessionManager(db_session)
                    simulator = ShadowSimulator(db_session)
                    executor = ERPExecutor(db_session)
                    broker = VerifiedExecutionBroker(db_session)
                    
                    async with session_manager.transaction():
                        # ---------------------------------------------------------------
                        # Event 6: shadow_simulated
                        # ---------------------------------------------------------------
                        t0 = time.perf_counter()
                        predicted_deltas: list[StateDelta] = []
                        predicted_delta = StateDelta(affected_record_ids=[], record_deltas=[], table=[], estimated_row_count=0)
                        
                        for tc in tool_calls:
                            tc_delta = await simulator.predict(tc)
                            predicted_deltas.append(tc_delta)
                            predicted_delta = predicted_delta + tc_delta
                        
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
                    
                    # Fetch approval if provided
                    active_approval = None
                    if req.approval_id:
                        result = await db_session.execute(select(PendingApproval).filter_by(approval_id=req.approval_id))
                        active_approval = result.scalars().first()
                        if not active_approval:
                            gate_decision = GateDecision(verdict="BLOCK", reason_code="APPROVAL_NOT_FOUND", detail=f"Approval ticket {req.approval_id} not found.", check_results=[])
                        elif active_approval.status != "APPROVED":
                            gate_decision = GateDecision(verdict="BLOCK", reason_code="APPROVAL_NOT_GRANTED", detail=f"Approval ticket is in state {active_approval.status}.", check_results=[])
                        elif active_approval.expires_at < time.time():
                            gate_decision = GateDecision(verdict="BLOCK", reason_code="APPROVAL_EXPIRED", detail="Approval ticket has expired.", check_results=[])

                    # Evaluate all tool calls. If any fail, it's a BLOCK/ESCALATE. 
                    if 'gate_decision' not in locals() or gate_decision is None:
                        gate_decision = None
                        for tc, tc_delta in zip(tool_calls, predicted_deltas):
                            tc_decision = self._gate.evaluate(
                                contract=contract,
                                predicted_delta=tc_delta,
                                tool_call=tc,
                                evidence_verdict=evidence_verdict,
                                auth_context=req.auth_context,
                            )
                            if gate_decision is None or tc_decision.verdict == "BLOCK" or (tc_decision.verdict == "ESCALATE" and gate_decision.verdict == "ALLOW"):
                                gate_decision = tc_decision
                            if gate_decision.verdict == "BLOCK":
                                break

                        # Override ESCALATE to ALLOW if we have a valid approval
                        if gate_decision.verdict == "ESCALATE" and active_approval:
                            gate_decision.verdict = "ALLOW"
                            gate_decision.detail = f"Escalation bypassed via valid approval {req.approval_id}."
                    
                    # If verdict is still ESCALATE, create a pending approval
                    created_approval_id = None
                    if gate_decision.verdict == "ESCALATE":
                        created_approval_id = str(uuid.uuid4())
                        new_approval = PendingApproval(
                            approval_id=created_approval_id,
                            trace_id=trace_id,
                            contract=contract.model_dump(),
                            tool_calls=[tc.model_dump() for tc in tool_calls],
                            requested_by=req.actor_id,
                            status="PENDING",
                            created_at=time.time(),
                            expires_at=time.time() + 86400, # 24 hours
                        )
                        db_session.add(new_approval)
                        await db_session.commit()
                        gate_decision.detail = f"Action escalated. Approval ticket {created_approval_id} created."

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
                                "approval_id": created_approval_id or req.approval_id,
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
                        actual_delta = StateDelta(affected_record_ids=[], record_deltas=[], table=[], estimated_row_count=0)
                        for tc in tool_calls:
                            actual_delta = actual_delta + await broker.commit(gate_decision.effect_certificate, tc, req.auth_context)
                            
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

                        await db_session.commit()

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

            except StateMismatchError as e:
                logger.error(f"High-severity incident: StateMismatchError - {e}")
                gate_decision.verdict = "BLOCK"
                gate_decision.reason_code = "TRANSACTION_ROLLBACK"
                gate_decision.detail = "State changed during transaction execution."
                actual_delta = None
            except (
                BrokerVerificationError,
                ExecutionMediationError,
                SecurityError,
                SQLAlchemyError,
                RuntimeError,
                ValueError,
                OSError,
                KeyError,
                TypeError,
            ) as e:
                logger.error(f"Execution error: {e}")
                gate_decision = gate_decision or GateDecision(verdict="BLOCK", reason_code="INTERNAL_ERROR", detail=str(e), check_results=[])
                actual_delta = None

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

            logger.info(f"Pipeline completed with verdict: {gate_decision.verdict} in {t_total:.1f}ms")

            return PipelineResult(
                trace_id=trace_id,
                task_id=req.task_id,
                contract=contract,
                tool_calls=tool_calls,
                predicted_delta=predicted_delta,
                gate_decision=gate_decision,
                actual_delta=actual_delta,
                trace_path=writer.path,
                events=writer.events(),
            )





def _build_tool_calls(contract: ActionContract) -> list[ToolCall]:
    """
    Build a list of ToolCalls from the contract slots.
    Splits multi-intents if separated by '+'.
    """
    intents = contract.intent.split("+")
    tool_calls = []

    for intent in intents:
        args = {}
        if "VENDOR_ID" in contract.slots:
            args["vendor_id"] = int(contract.slots["VENDOR_ID"])
        if "MONTH" in contract.slots:
            args["month"] = int(contract.slots["MONTH"])
        if "YEAR" in contract.slots:
            args["year"] = int(contract.slots["YEAR"])
        
        # New tools mappings
        if "USER_ID" in contract.slots:
            args["user_id"] = contract.slots["USER_ID"]
        elif "TARGET_ID" in contract.slots:
            args["user_id"] = contract.slots["TARGET_ID"]
            
        if "DURATION_DAYS" in contract.slots:
            args["duration_days"] = int(contract.slots["DURATION_DAYS"])
        if "NEW_LIMIT_INR" in contract.slots:
            args["new_limit_inr"] = float(contract.slots["NEW_LIMIT_INR"])
        if "JUSTIFICATION" in contract.slots:
            args["justification"] = contract.slots["JUSTIFICATION"]

        if intent == "invoice.archive":
            tool_calls.append(ToolCall(
                tool_name="archive_invoices",
                arguments=args,
                schema_version="1.0",
                tool_schema_hash=schema_hash(),
            ))
        elif intent == "access.block":
            tool_calls.append(ToolCall(
                tool_name="block_user_access",
                arguments=args,
                schema_version="1.0",
                tool_schema_hash=schema_hash(),
            ))
        elif intent == "limit.update":
            tool_calls.append(ToolCall(
                tool_name="update_credit_limit",
                arguments=args,
                schema_version="1.0",
                tool_schema_hash=schema_hash(),
            ))
        elif intent == "vendor.suspend":
            tool_calls.append(ToolCall(
                tool_name="suspend_vendor",
                arguments=args,
                schema_version="1.0",
                tool_schema_hash=schema_hash(),
            ))
        else:
            # Placeholder for unknown tool logic
            tool_calls.append(ToolCall(
                tool_name="unknown_tool",
                arguments=contract.slots,
                schema_version="1.0",
                tool_schema_hash="unknown",
            ))

    return tool_calls


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
    contract: ActionContract | None,
    tool_calls: list[ToolCall],
    writer: TraceWriter,
    envelope: dict[str, Any],
) -> PipelineResult:
    """Return a minimal PipelineResult when pipeline exits early (e.g. schema error)."""
    empty_delta = StateDelta(
        affected_record_ids=[], record_deltas=[], table="", estimated_row_count=0
    )
    block_decision = GateDecision(
        verdict="BLOCK",
        reason_code="TOOL_SCHEMA_INVALID",
        detail="Pipeline exited early due to tool schema validation failure.",
        check_results=[],
    )
    writer.write(
        make_event(
            **envelope,
            event_type="tool_executed",
            decision="SKIPPED_EARLY_EXIT",
            payload={}
        )
    )
    writer.write(
        make_event(
            **envelope,
            event_type="evaluation_verdict",
            decision="BLOCK",
            payload={}
        )
    )
    return PipelineResult(
        trace_id=trace_id,
        task_id=req.task_id,
        contract=contract,
        tool_calls=tool_calls,
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


async def run_pipeline(
    raw_text: str,
    actor_id: str,
    actor_role: str,
    task_id: str | None = None,
    approval_id: str | None = None,
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
    from data.synthetic.erp import seed_fresh_async
    from packages.storage.postgres import engine

    await seed_fresh_async(engine)
    pipeline = NiyamPipeline(
        engine=engine,
        traces_dir=traces_dir or _DEFAULT_TRACES_DIR,
    )
    req = PipelineRequest(
        raw_text=raw_text,
        actor_id=actor_id,
        actor_role=actor_role,
        task_id=task_id,
        approval_id=approval_id,
    )
    result = await pipeline.run(req)
    # Serialize TraceEvent objects to dicts for benchmark runner compatibility
    return [ev.model_dump() if hasattr(ev, "model_dump") else dict(ev) for ev in result.events]

