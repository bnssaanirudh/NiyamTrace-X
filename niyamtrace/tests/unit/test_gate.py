"""tests/unit/test_gate.py — Unit tests for gate checks and NiyamGate evaluator."""

from __future__ import annotations

import pytest
from datetime import datetime

from packages.contracts.schema import (
    GateCheckResult,
    ActionContract,
    RecordDelta,
    StateDelta,
    TemporalRange,
    ToolCall,
)
from packages.gate.gate import NiyamGate
from packages.gate.policy import (
    DEFAULT_POLICY,
    PolicyBundle,
    check_attribute_containment,
    check_cardinality_and_approval,
    check_evidence_sufficiency,
    check_target_identity_containment,
    check_temporal_containment,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _contract(**overrides) -> ActionContract:
    defaults = dict(
        actor_id="user-001",
        actor_role="procurement_manager",
        intent="invoice.archive",
        intent_confidence=0.97,
        slots={"VENDOR_ID": "4421", "MONTH": 3, "YEAR": 2025},
        raw_text="Archive March invoices for vendor 4421",
        normalized_text="archive vendor_invoice vendor_id=4421 month=3 year=2025",
    )
    defaults.update(overrides)
    return ActionContract(**defaults)


def _tool_call(vendor_id=4421, month=3, year=2025) -> ToolCall:
    return ToolCall(
        tool_name="archive_invoices",
        arguments={"vendor_id": vendor_id, "month": month, "year": year},
    )


def _delta(record_ids=None, fields=None) -> StateDelta:
    record_ids = record_ids or ["INV-4421-2503", "INV-4421-2504", "INV-4421-2505"]
    fields = fields or ["status"]
    deltas = [
        RecordDelta(
            record_id=rid,
            table="vendor_invoices",
            field=f,
            old_value="OPEN",
            new_value="ARCHIVED",
        )
        for rid in record_ids
        for f in fields
    ]
    return StateDelta(
        affected_record_ids=record_ids,
        record_deltas=deltas,
        table="vendor_invoices",
        estimated_row_count=len(record_ids),
    )


# ---------------------------------------------------------------------------
# Check 1: Target identity containment
# ---------------------------------------------------------------------------


class TestTargetIdentityContainment:
    def test_matching_vendor_passes(self):
        result = check_target_identity_containment(_contract(), _delta(), _tool_call())
        assert result.passed
        assert result.reason_code == "OK"

    def test_wrong_vendor_blocked(self):
        result = check_target_identity_containment(
            _contract(), _delta(), _tool_call(vendor_id=9999)
        )
        assert not result.passed
        assert result.reason_code == "VENDOR_ID_MISMATCH"

    def test_missing_vendor_in_selector_blocked(self):
        c = _contract(slots={"MONTH": 3, "YEAR": 2025})
        result = check_target_identity_containment(c, _delta(), _tool_call())
        assert not result.passed
        assert result.reason_code == "SELECTOR_MISSING_VENDOR_ID"


# ---------------------------------------------------------------------------
# Check 2: Temporal containment
# ---------------------------------------------------------------------------


class TestTemporalContainment:
    def test_matching_month_year_passes(self):
        result = check_temporal_containment(_contract(), _tool_call(month=3, year=2025))
        assert result.passed

    def test_missing_month_blocked(self):
        tc = ToolCall(
            tool_name="archive_invoices",
            arguments={"vendor_id": 4421, "year": 2025},  # no month
        )
        result = check_temporal_containment(_contract(), tc)
        assert not result.passed
        assert result.reason_code == "TOOL_ARGS_MISSING_TEMPORAL_SCOPE"

    def test_missing_year_blocked(self):
        tc = ToolCall(
            tool_name="archive_invoices",
            arguments={"vendor_id": 4421, "month": 3},  # no year
        )
        result = check_temporal_containment(_contract(), tc)
        assert not result.passed
        assert result.reason_code == "TOOL_ARGS_MISSING_TEMPORAL_SCOPE"

    def test_wrong_month_blocked(self):
        result = check_temporal_containment(_contract(), _tool_call(month=4, year=2025))
        assert not result.passed
        assert result.reason_code == "TOOL_DATE_AFTER_CONTRACT_END"

    def test_contract_missing_temporal_scope_blocked(self):
        c = _contract(slots={"VENDOR_ID": "4421"})
        result = check_temporal_containment(c, _tool_call())
        assert not result.passed
        assert result.reason_code == "CONTRACT_MISSING_TEMPORAL_SCOPE"

    def test_date_before_scope_blocked(self):
        result = check_temporal_containment(_contract(), _tool_call(month=2, year=2025))
        assert not result.passed
        assert result.reason_code == "TOOL_DATE_BEFORE_CONTRACT_START"


# ---------------------------------------------------------------------------
# Check 3: Attribute containment
# ---------------------------------------------------------------------------


class TestAttributeContainment:
    def test_allowed_attribute_passes(self):
        result = check_attribute_containment(_contract(), _delta(fields=["status"]))
        assert result.passed


# ---------------------------------------------------------------------------
# Check 4: Cardinality + approval
# ---------------------------------------------------------------------------


class TestCardinalityAndApproval:
    def test_small_count_within_threshold_passes(self):
        result = check_cardinality_and_approval(_contract(), _delta(record_ids=["A", "B", "C"]))
        assert result.passed

    def test_count_exceeds_threshold_without_approval_escalates(self):
        ids = [f"INV-{i}" for i in range(11)]  # > default threshold of 10
        result = check_cardinality_and_approval(_contract(), _delta(record_ids=ids))
        assert not result.passed
        assert result.reason_code == "APPROVAL_REQUIRED"


# ---------------------------------------------------------------------------
# Check 5: Evidence sufficiency (stub behavior)
# ---------------------------------------------------------------------------


class TestEvidenceSufficiency:
    def test_stub_always_passes(self):
        result = check_evidence_sufficiency(_contract(), "STUB")
        assert result.passed
        assert result.reason_code == "STUB_ALWAYS_SUPPORT"

    def test_support_passes(self):
        result = check_evidence_sufficiency(_contract(), "SUPPORT")
        assert result.passed

    def test_contradict_blocks(self):
        result = check_evidence_sufficiency(_contract(), "CONTRADICT")
        assert not result.passed
        assert result.reason_code == "EVIDENCE_CONTRADICTS_ACTION"

    def test_insufficient_blocks(self):
        result = check_evidence_sufficiency(_contract(), "INSUFFICIENT")
        assert not result.passed
        assert result.reason_code == "EVIDENCE_INSUFFICIENT"


# ---------------------------------------------------------------------------
# NiyamGate integration (all checks combined)
# ---------------------------------------------------------------------------


class TestNiyamGate:
    def setup_method(self):
        self.gate = NiyamGate()

    def test_valid_scenario_returns_allow(self):
        decision = self.gate.evaluate(
            contract=_contract(),
            predicted_delta=_delta(),
            tool_call=_tool_call(),
            evidence_verdict="STUB",
        )
        assert decision.verdict == "ALLOW"
        assert decision.reason_code == "ALL_CHECKS_PASSED"
        assert len(decision.check_results) == 5

    def test_wrong_vendor_returns_block(self):
        decision = self.gate.evaluate(
            contract=_contract(),
            predicted_delta=_delta(),
            tool_call=_tool_call(vendor_id=9999),
            evidence_verdict="STUB",
        )
        assert decision.verdict == "BLOCK"
        assert decision.reason_code == "VENDOR_ID_MISMATCH"

    def test_missing_temporal_scope_returns_block(self):
        tc = ToolCall(
            tool_name="archive_invoices",
            arguments={"vendor_id": 4421},
        )
        decision = self.gate.evaluate(
            contract=_contract(),
            predicted_delta=_delta(),
            tool_call=tc,
            evidence_verdict="STUB",
        )
        assert decision.verdict == "BLOCK"
        assert "TEMPORAL" in decision.reason_code or "MISSING" in decision.reason_code

    def test_approval_required_returns_escalate(self):
        ids = [f"INV-{i}" for i in range(11)]
        decision = self.gate.evaluate(
            contract=_contract(),
            predicted_delta=_delta(record_ids=ids),
            tool_call=_tool_call(),
            evidence_verdict="STUB",
        )
        assert decision.verdict == "ESCALATE"
        assert decision.correction is not None
        assert decision.correction["action"] == "REQUEST_APPROVAL"

    def test_contradict_evidence_returns_block(self):
        decision = self.gate.evaluate(
            contract=_contract(),
            predicted_delta=_delta(),
            tool_call=_tool_call(),
            evidence_verdict="CONTRADICT",
        )
        assert decision.verdict == "BLOCK"

    def test_gate_latency_recorded(self):
        decision = self.gate.evaluate(
            contract=_contract(),
            predicted_delta=_delta(),
            tool_call=_tool_call(),
        )
        assert decision.latency_ms >= 0.0
