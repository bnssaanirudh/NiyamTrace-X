"""tests/unit/test_contracts.py — Unit tests for IntentContract and supporting types."""

from __future__ import annotations

import pytest
from datetime import datetime
from pydantic import ValidationError

from packages.contracts.schema import (
    GateDecision,
    ActionContract,
    RecordDelta,
    StateDelta,
    TemporalRange,
    ToolCall,
    TraceEvent,
)


# ---------------------------------------------------------------------------
# TemporalRange
# ---------------------------------------------------------------------------


class TestTemporalRange:
    def test_valid_with_both_bounds(self):
        tr = TemporalRange(start=datetime(2025, 3, 1), end=datetime(2025, 3, 31))
        assert tr.start is not None
        assert tr.end is not None

    def test_valid_with_start_only(self):
        tr = TemporalRange(start=datetime(2025, 3, 1))
        assert tr.end is None

    def test_valid_with_end_only(self):
        tr = TemporalRange(end=datetime(2025, 3, 31))
        assert tr.start is None

    def test_invalid_no_bounds(self):
        with pytest.raises(ValidationError):
            TemporalRange()


# ---------------------------------------------------------------------------
# ActionContract
# ---------------------------------------------------------------------------


def _valid_contract(**overrides) -> ActionContract:
    defaults = dict(
        actor_id="user-001",
        actor_role="procurement_manager",
        intent="invoice.archive",
        intent_confidence=0.97,
        slots={"VENDOR_ID": "4421", "MONTH": 3, "YEAR": 2025},
        requires_review=False,
        raw_text="Archive March invoices for vendor 4421",
        normalized_text="archive vendor_invoice vendor_id=4421 month=3 year=2025",
    )
    defaults.update(overrides)
    return ActionContract(**defaults)


class TestActionContract:
    def test_valid_contract_creates_successfully(self):
        c = _valid_contract()
        assert c.intent == "invoice.archive"
        assert c.intent_confidence == 0.97
        assert c.requires_review is False

    def test_contract_id_auto_generated(self):
        c = _valid_contract()
        assert len(c.contract_id) == 36  # UUID4

    def test_unknown_intent_requires_review(self):
        c = _valid_contract(intent="unknown")
        assert c.requires_review is True

    def test_confidence_below_zero_rejected(self):
        with pytest.raises(ValidationError):
            _valid_contract(intent_confidence=-0.1)

    def test_confidence_above_one_rejected(self):
        with pytest.raises(ValidationError):
            _valid_contract(intent_confidence=1.01)


# ---------------------------------------------------------------------------
# StateDelta
# ---------------------------------------------------------------------------


class TestStateDelta:
    def test_record_id_set(self):
        delta = StateDelta(
            affected_record_ids=["INV-001", "INV-002"],
            record_deltas=[],
            table="vendor_invoices",
            estimated_row_count=2,
        )
        assert delta.record_id_set() == {"INV-001", "INV-002"}

    def test_empty_delta(self):
        delta = StateDelta(
            affected_record_ids=[],
            record_deltas=[],
            table="vendor_invoices",
            estimated_row_count=0,
        )
        assert delta.record_id_set() == set()


# ---------------------------------------------------------------------------
# GateDecision
# ---------------------------------------------------------------------------


class TestGateDecision:
    def test_allow_decision(self):
        d = GateDecision(
            verdict="ALLOW",
            reason_code="ALL_CHECKS_PASSED",
            detail="ok",
            check_results=[],
        )
        assert d.verdict == "ALLOW"

    def test_block_decision(self):
        d = GateDecision(
            verdict="BLOCK",
            reason_code="VENDOR_ID_MISMATCH",
            detail="mismatch",
            check_results=[],
        )
        assert d.verdict == "BLOCK"
        assert d.reason_code == "VENDOR_ID_MISMATCH"


# ---------------------------------------------------------------------------
# TraceEvent
# ---------------------------------------------------------------------------


class TestTraceEvent:
    def test_event_serializes_to_json(self):
        e = TraceEvent(
            trace_id="t1",
            task_id="task1",
            event_type="input_received",
        )
        json_str = e.model_dump_json()
        assert "input_received" in json_str
        assert "t1" in json_str

    def test_all_9_event_types_valid(self):
        types = [
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
        for et in types:
            e = TraceEvent(trace_id="t", task_id="t", event_type=et)
            assert e.event_type == et
