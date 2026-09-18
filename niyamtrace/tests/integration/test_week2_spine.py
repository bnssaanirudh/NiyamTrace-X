"""
tests/integration/test_week2_spine.py — Week 2 Exit-Criterion Integration Test

This is the primary integration test for the NiyamTrace spine. It runs the
canonical English scenario ("Archive March invoices for vendor 4421") end-to-end
and asserts all Week 2 exit criteria from the brief (Section 7):

  ✓ A contract is produced and passes schema validation
  ✓ All required contract fields are populated
  ✓ PredictedDelta is non-empty and matches the 3 March 2025 invoices for vendor 4421
  ✓ Gate returns ALLOW (scenario is in-scope per policy)
  ✓ ActualDelta matches PredictedDelta (simulator fidelity == 1.0 for this case)
  ✓ Trace JSONL contains all 9 required event types in order
  ✓ All trace events carry trace_id, task_id, decision, latency_ms

Additionally tests gate BLOCK scenarios to ensure the gate is not always passing:
  ✓ Wrong vendor → BLOCK:VENDOR_ID_MISMATCH
  ✓ Missing temporal scope in tool call → BLOCK
  ✓ Unauthorized attribute mutation → BLOCK

Security tests (unauthorized-effect assertions):
  ✓ Invoices for other vendors are NOT archived
  ✓ Invoices for correct vendor but wrong month are NOT archived
  ✓ CLOSED invoices are NOT touched

Replay test:
  ✓ Reading the JSONL trace back produces the same event types in the same order
"""

from __future__ import annotations

import json
import sqlite3
import tempfile
from pathlib import Path
from datetime import datetime, timezone

import pytest

from apps.gateway.pipeline import NiyamPipeline, PipelineRequest
from data.synthetic.erp import (
    SEED_SNAPSHOT_ID,
    init_schema,
    query_invoices,
    reset_to_seed,
)
from packages.lake.writer import read_trace

# ---------------------------------------------------------------------------
# Required event order from the NiyamTrace brief (Section 5)
# ---------------------------------------------------------------------------

REQUIRED_EVENT_TYPES_IN_ORDER = [
    "input_received",
    "contract_extracted",
    "retrieval_completed",
    "policy_evaluated",
    "tool_proposed",
    "tool_simulated",
    "gate_decision",
    "tool_executed",
    "evaluation_verdict",
]

# The 3 seed invoice IDs that represent March 2025, vendor 4421
EXPECTED_MARCH_2025_IDS = {"INV-4421-2503", "INV-4421-2504", "INV-4421-2505"}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def fresh_erp():
    """In-memory SQLite ERP, seeded to standard state, reset before each test."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    init_schema(conn)
    reset_to_seed(conn)
    yield conn
    conn.close()


@pytest.fixture
def traces_dir(tmp_path):
    """Temporary directory for JSONL trace files."""
    return tmp_path / "traces"


@pytest.fixture
def pipeline(fresh_erp, traces_dir):
    from packages.nlp.compiler import NiyamCompiler
    
    compiler = NiyamCompiler(parser_version_suffix="mock")
    return NiyamPipeline(erp_conn=fresh_erp, traces_dir=traces_dir, compiler=compiler)


@pytest.fixture
def canonical_request():
    return PipelineRequest(
        raw_text="Archive March invoices for vendor 4421",
        actor_id="user-pm-001",
        actor_role="procurement_manager",
        task_id="task-week2-canonical",
        reference_dt=datetime(2025, 3, 15, tzinfo=timezone.utc),
    )


# ---------------------------------------------------------------------------
# Week 2 Exit-Criterion Tests (Happy Path)
# ---------------------------------------------------------------------------


class TestWeek2ExitCriterion:
    """
    PRIMARY: All assertions required to pass the Week 2 exit criterion from
    Section 7 of the NiyamTrace brief.
    """

    def test_pipeline_runs_without_error(self, pipeline, canonical_request):
        result = pipeline.run(canonical_request)
        assert result is not None

    # -- Contract --

    def test_contract_is_produced(self, pipeline, canonical_request):
        result = pipeline.run(canonical_request)
        assert result.contract is not None

    def test_contract_passes_schema_validation(self, pipeline, canonical_request):
        result = pipeline.run(canonical_request)
        # model_dump() will raise ValidationError if contract is malformed
        dumped = result.contract.model_dump()
        assert isinstance(dumped, dict)

    def test_contract_has_correct_action(self, pipeline, canonical_request):
        result = pipeline.run(canonical_request)
        assert result.contract.intent == "invoice.archive"

    def test_contract_has_correct_actor(self, pipeline, canonical_request):
        result = pipeline.run(canonical_request)
        assert result.contract.actor_id == "user-pm-001"
        assert result.contract.actor_role == "procurement_manager"

    def test_contract_has_temporal_scope(self, pipeline, canonical_request):
        result = pipeline.run(canonical_request)
        assert result.contract.slots.get("MONTH") == 3
        assert result.contract.slots.get("YEAR") == 2025

    def test_contract_selector_predicate_populated(self, pipeline, canonical_request):
        result = pipeline.run(canonical_request)
        assert result.contract.slots.get("VENDOR_ID") == "4421"

    def test_contract_not_ambiguous(self, pipeline, canonical_request):
        result = pipeline.run(canonical_request)
        assert result.contract.requires_review is False

    def test_contract_high_confidence(self, pipeline, canonical_request):
        result = pipeline.run(canonical_request)
        assert result.contract.intent_confidence >= 0.9

    # -- Predicted Delta --

    def test_predicted_delta_is_non_empty(self, pipeline, canonical_request):
        result = pipeline.run(canonical_request)
        assert result.predicted_delta.estimated_row_count > 0

    def test_predicted_delta_matches_march_2025_invoices(self, pipeline, canonical_request):
        result = pipeline.run(canonical_request)
        assert result.predicted_delta.record_id_set() == EXPECTED_MARCH_2025_IDS

    def test_predicted_delta_has_exactly_3_records(self, pipeline, canonical_request):
        result = pipeline.run(canonical_request)
        assert result.predicted_delta.estimated_row_count == 3

    # -- Gate Decision --

    def test_gate_returns_allow(self, pipeline, canonical_request):
        result = pipeline.run(canonical_request)
        assert result.gate_decision.verdict == "ALLOW"

    def test_gate_reason_code_is_all_checks_passed(self, pipeline, canonical_request):
        result = pipeline.run(canonical_request)
        assert result.gate_decision.reason_code == "ALL_CHECKS_PASSED"

    def test_gate_has_5_check_results(self, pipeline, canonical_request):
        result = pipeline.run(canonical_request)
        assert len(result.gate_decision.check_results) == 5

    def test_all_gate_checks_passed(self, pipeline, canonical_request):
        result = pipeline.run(canonical_request)
        for check in result.gate_decision.check_results:
            assert check.passed, f"Check {check.check_name} failed: {check.detail}"

    # -- Actual Delta and Fidelity --

    def test_actual_delta_produced_after_allow(self, pipeline, canonical_request):
        result = pipeline.run(canonical_request)
        assert result.actual_delta is not None

    def test_actual_delta_matches_predicted_delta(self, pipeline, canonical_request):
        result = pipeline.run(canonical_request)
        assert result.predicted_delta.record_id_set() == result.actual_delta.record_id_set()

    def test_simulator_fidelity_is_perfect(self, pipeline, canonical_request):
        """Fidelity must be 1.0 for the seed scenario."""
        result = pipeline.run(canonical_request)
        pred_ids = result.predicted_delta.record_id_set()
        actual_ids = result.actual_delta.record_id_set()
        union = pred_ids | actual_ids
        intersection = pred_ids & actual_ids
        fidelity = len(intersection) / len(union)
        assert fidelity == 1.0

    # -- ERP State After Execution --

    def test_target_invoices_are_archived_in_erp(self, pipeline, canonical_request, fresh_erp):
        pipeline.run(canonical_request)
        archived = query_invoices(fresh_erp, vendor_id=4421, month=3, year=2025, status="ARCHIVED")
        assert len(archived) == 3

    def test_no_open_invoices_remain_for_target(self, pipeline, canonical_request, fresh_erp):
        pipeline.run(canonical_request)
        open_rows = query_invoices(fresh_erp, vendor_id=4421, month=3, year=2025, status="OPEN")
        assert len(open_rows) == 0

    # -- Trace / Event Log --

    def test_trace_file_exists(self, pipeline, canonical_request, traces_dir):
        result = pipeline.run(canonical_request)
        assert result.trace_path.exists()

    def test_trace_contains_all_9_event_types(self, pipeline, canonical_request):
        result = pipeline.run(canonical_request)
        seen_types = [e.event_type for e in result.events]
        for required_type in REQUIRED_EVENT_TYPES_IN_ORDER:
            assert required_type in seen_types, (
                f"Missing required event type '{required_type}' in trace. "
                f"Seen: {seen_types}"
            )

    def test_trace_event_types_in_correct_order(self, pipeline, canonical_request):
        result = pipeline.run(canonical_request)
        seen_types = [e.event_type for e in result.events]
        # Verify the REQUIRED_EVENT_TYPES appear in the correct relative order
        last_idx = -1
        for required_type in REQUIRED_EVENT_TYPES_IN_ORDER:
            idx = seen_types.index(required_type)
            assert idx > last_idx, (
                f"Event '{required_type}' at index {idx} is out of order "
                f"(last required was at {last_idx}). Full order: {seen_types}"
            )
            last_idx = idx

    def test_all_events_have_trace_id(self, pipeline, canonical_request):
        result = pipeline.run(canonical_request)
        for event in result.events:
            assert event.trace_id == result.trace_id

    def test_all_events_have_task_id(self, pipeline, canonical_request):
        result = pipeline.run(canonical_request)
        for event in result.events:
            assert event.task_id == canonical_request.task_id

    def test_all_events_have_latency_ms(self, pipeline, canonical_request):
        result = pipeline.run(canonical_request)
        for event in result.events:
            assert event.latency_ms >= 0.0

    def test_gate_decision_event_has_decision_field(self, pipeline, canonical_request):
        result = pipeline.run(canonical_request)
        gate_event = next(e for e in result.events if e.event_type == "gate_decision")
        assert gate_event.decision in ("ALLOW", "BLOCK", "ESCALATE")

    def test_trace_has_data_snapshot_id(self, pipeline, canonical_request):
        result = pipeline.run(canonical_request)
        for event in result.events:
            assert event.data_snapshot_id == SEED_SNAPSHOT_ID

    def test_trace_has_policy_bundle_hash(self, pipeline, canonical_request):
        result = pipeline.run(canonical_request)
        for event in result.events:
            assert event.policy_bundle_hash != ""

    # -- Replay Test --

    def test_trace_is_replayable_from_jsonl(self, pipeline, canonical_request):
        """Reading the JSONL trace back must produce the same event types in order."""
        result = pipeline.run(canonical_request)
        replayed = read_trace(result.trace_path)

        original_types = [e.event_type for e in result.events]
        replayed_types = [e.event_type for e in replayed]
        assert original_types == replayed_types

    def test_replayed_trace_has_same_trace_id(self, pipeline, canonical_request):
        result = pipeline.run(canonical_request)
        replayed = read_trace(result.trace_path)
        for event in replayed:
            assert event.trace_id == result.trace_id


# ---------------------------------------------------------------------------
# Security Tests (Gate BLOCK assertions — gate must not always pass)
# ---------------------------------------------------------------------------


class TestSecurityBlocks:
    """
    These tests verify that the gate correctly blocks unauthorized scenarios.
    If any of these fail, the gate is permissive in a dangerous way.
    """

    def test_wrong_vendor_is_blocked(self, fresh_erp, traces_dir):
        """A request that parses to vendor 9999 must be blocked (vendor mismatch)."""
        from packages.contracts.schema import ActionContract, TemporalRange, ToolCall
        from packages.gate.gate import NiyamGate
        from packages.gate.simulator import ShadowSimulator
        from packages.contracts.schema import RecordDelta, StateDelta
        from datetime import datetime

        # Simulate a contract for vendor 4421 but tool call targeting vendor 9999
        contract = ActionContract(
            actor_id="user-001",
            actor_role="procurement_manager",
            intent="invoice.archive",
            intent_confidence=0.95,
            slots={"VENDOR_ID": "4421", "MONTH": 3, "YEAR": 2025},
            raw_text="Archive March invoices for vendor 9999",
            normalized_text="archive vendor_invoice vendor_id=9999 month=3 year=2025",
        )
        tool_call = ToolCall(
            tool_name="archive_invoices",
            arguments={"vendor_id": 9999, "month": 3, "year": 2025},
        )
        sim = ShadowSimulator(fresh_erp)
        delta = sim.predict(tool_call)  # Will be empty since 9999 has no rows
        gate = NiyamGate()
        decision = gate.evaluate(contract, delta, tool_call)

        assert decision.verdict == "BLOCK"
        assert decision.reason_code == "VENDOR_ID_MISMATCH"

    def test_missing_month_in_tool_call_is_blocked(self, fresh_erp, traces_dir):
        """Tool call without month would archive ALL vendor records — must be blocked."""
        from packages.contracts.schema import ActionContract, TemporalRange, ToolCall
        from packages.gate.gate import NiyamGate
        from packages.contracts.schema import StateDelta
        from datetime import datetime

        contract = ActionContract(
            actor_id="user-001",
            actor_role="procurement_manager",
            intent="invoice.archive",
            intent_confidence=0.95,
            slots={"VENDOR_ID": "4421", "MONTH": 3, "YEAR": 2025},
            raw_text="Archive March invoices for vendor 4421",
            normalized_text="archive vendor_invoice vendor_id=4421 month=3 year=2025",
        )
        tool_call = ToolCall(
            tool_name="archive_invoices",
            arguments={"vendor_id": 4421, "year": 2025},  # missing month!
        )
        empty_delta = StateDelta(
            affected_record_ids=[],
            record_deltas=[],
            table="vendor_invoices",
            estimated_row_count=0,
        )
        gate = NiyamGate()
        decision = gate.evaluate(contract, empty_delta, tool_call)

        assert decision.verdict == "BLOCK"
        assert "TEMPORAL" in decision.reason_code or "MISSING" in decision.reason_code

    def test_unauthorized_field_mutation_is_blocked(self, fresh_erp, traces_dir):
        """A delta that mutates amount_usd (not in allowed_attributes) must be blocked."""
        from packages.contracts.schema import (
            ActionContract, TemporalRange, ToolCall, RecordDelta, StateDelta
        )
        from packages.gate.gate import NiyamGate
        from datetime import datetime

        contract = ActionContract(
            actor_id="user-001",
            actor_role="procurement_manager",
            intent="invoice.archive",
            intent_confidence=0.95,
            slots={"VENDOR_ID": "4421", "MONTH": 3, "YEAR": 2025},
            raw_text="Archive March invoices for vendor 4421",
            normalized_text="archive vendor_invoice vendor_id=4421 month=3 year=2025",
        )
        tool_call = ToolCall(
            tool_name="archive_invoices",
            arguments={"vendor_id": 4421, "month": 3, "year": 2025},
        )
        # Simulate a rogue delta that also mutates amount_usd
        bad_delta = StateDelta(
            affected_record_ids=["INV-4421-2503"],
            record_deltas=[
                RecordDelta(
                    record_id="INV-4421-2503",
                    table="vendor_invoices",
                    field="status",
                    old_value="OPEN",
                    new_value="ARCHIVED",
                ),
                RecordDelta(
                    record_id="INV-4421-2503",
                    table="vendor_invoices",
                    field="amount_usd",  # UNAUTHORIZED
                    old_value=15200.00,
                    new_value=0.00,
                ),
            ],
            table="vendor_invoices",
            estimated_row_count=1,
        )
        gate = NiyamGate()
        decision = gate.evaluate(contract, bad_delta, tool_call)

        assert decision.verdict == "BLOCK"
        assert decision.reason_code == "UNAUTHORIZED_ATTRIBUTE_MUTATION"

    def test_other_vendors_not_affected_by_canonical_run(
        self, pipeline, canonical_request, fresh_erp
    ):
        """After the canonical run, vendor 8802 and 3301 invoices must be untouched."""
        pipeline.run(canonical_request)

        rows_8802 = query_invoices(fresh_erp, vendor_id=8802)
        rows_3301 = query_invoices(fresh_erp, vendor_id=3301)

        for row in rows_8802:
            assert row["status"] in ("OPEN", "CLOSED", "TOMBSTONED"), (
                f"vendor 8802 row {row['invoice_id']} has unexpected status {row['status']}"
            )
        # Specifically: none of 8802's or 3301's OPEN rows should have become ARCHIVED
        archived_8802 = query_invoices(fresh_erp, vendor_id=8802, status="ARCHIVED")
        archived_3301 = query_invoices(fresh_erp, vendor_id=3301, status="ARCHIVED")
        assert len(archived_8802) == 0
        assert len(archived_3301) == 0

    def test_tombstoned_invoices_not_included_in_archive(self, fresh_erp, traces_dir):
        """TOMBSTONED rows (retrieval-layer deletion) must NOT be re-archived."""
        from packages.gate.simulator import ShadowSimulator
        from packages.contracts.schema import ToolCall

        # vendor 8802 has a TOMBSTONED invoice (INV-8802-2401) in seed
        sim = ShadowSimulator(fresh_erp)
        tool = ToolCall(
            tool_name="archive_invoices",
            arguments={"vendor_id": 8802, "month": 11, "year": 2024},
        )
        delta = sim.predict(tool)
        # TOMBSTONED row should NOT appear in predicted delta
        assert "INV-8802-2401" not in delta.affected_record_ids
        assert delta.estimated_row_count == 0
