"""
tests/regression/test_gate_regression.py — NiyamGate Regression Suite

5 deterministic regression scenarios exercising the full gate evaluation
path without any LLM calls. The mock compiler produces known contracts
so results are fully reproducible in CI.

Scenarios:
  R1: Canonical EN archive → ALLOW
  R2: Wrong vendor_id → BLOCK:VENDOR_ID_MISMATCH
  R3: Missing temporal scope → BLOCK:TOOL_ARGS_MISSING_TEMPORAL_SCOPE
  R4: Unauthorized field mutation → BLOCK:UNAUTHORIZED_ATTRIBUTE_MUTATION
  R5: Bulk > threshold → ESCALATE:APPROVAL_REQUIRED
  R6: Unauthorized role for block_user_access → BLOCK:IDENTITY_ROLE_NOT_PERMITTED
  R7: Valid update_credit_limit → ALLOW
  R8: Missing justification for suspend_vendor → schema validation error
"""

from __future__ import annotations

import sqlite3
import pytest

from data.synthetic.erp import init_schema, reset_to_seed
from packages.contracts.schema import (
    ActionContract,
    GateCheckResult,
    RecordDelta,
    StateDelta,
    ToolCall,
)
from packages.gate.gate import NiyamGate
from packages.gate.policy import DEFAULT_POLICY, PolicyBundle
from packages.gate.tool_schemas import validate_tool_call, ToolSchemaValidationError


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def erp_conn() -> sqlite3.Connection:
    """Fresh in-memory SQLite ERP with seed data."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    init_schema(conn)
    reset_to_seed(conn)
    return conn


def _contract(**overrides) -> ActionContract:
    defaults = dict(
        actor_id="U-REG-001",
        actor_role="procurement_manager",
        intent="invoice.archive",
        intent_confidence=0.95,
        slots={"VENDOR_ID": "4421", "MONTH": 3, "YEAR": 2025},
        raw_text="Archive March invoices for vendor 4421",
        normalized_text="archive vendor_invoice vendor_id=4421 month=3 year=2025",
    )
    defaults.update(overrides)
    return ActionContract(**defaults)


def _delta(record_ids: list[str], fields: list[str] | None = None) -> StateDelta:
    fields = fields or ["status"]
    return StateDelta(
        affected_record_ids=record_ids,
        record_deltas=[
            RecordDelta(
                record_id=rid,
                table="vendor_invoices",
                field="status",
                old_value="OPEN",
                new_value="ARCHIVED",
            )
            for rid in record_ids
        ],
        table="vendor_invoices",
        estimated_row_count=len(record_ids),
    )


# ---------------------------------------------------------------------------
# R1: Canonical EN archive → ALLOW
# ---------------------------------------------------------------------------


def test_r1_canonical_en_archive_allow(erp_conn: sqlite3.Connection) -> None:
    """R1: Standard English archive for vendor 4421, March 2025 → ALLOW."""
    contract = _contract()
    tool_call = ToolCall(
        tool_name="archive_invoices",
        arguments={"vendor_id": 4421, "month": 3, "year": 2025},
    )
    delta = _delta(["INV-4421-2503", "INV-4421-2504", "INV-4421-2505"])
    gate = NiyamGate(DEFAULT_POLICY)
    verdict = gate.evaluate(
        contract=contract,
        tool_call=tool_call,
        predicted_delta=delta,
        evidence_verdict="SUPPORT",
    )
    assert verdict.verdict == "ALLOW", f"Expected ALLOW, got {verdict.verdict}: {verdict.reason_code}"


# ---------------------------------------------------------------------------
# R2: Wrong vendor_id → BLOCK (identity containment failure)
# ---------------------------------------------------------------------------


def test_r2_wrong_vendor_id_block(erp_conn: sqlite3.Connection) -> None:
    """R2: Contract says vendor 4421 but tool call targets vendor 8802 → BLOCK."""
    contract = _contract()  # VENDOR_ID = "4421"
    tool_call = ToolCall(
        tool_name="archive_invoices",
        arguments={"vendor_id": 8802, "month": 3, "year": 2025},  # WRONG vendor
    )
    delta = StateDelta(
        affected_record_ids=["INV-8802-2503"],
        record_deltas=[
            RecordDelta(
                record_id="INV-8802-2503",
                table="vendor_invoices",
                field="status",
                old_value="OPEN",
                new_value="ARCHIVED",
            )
        ],
        table="vendor_invoices",
        estimated_row_count=1,
    )
    gate = NiyamGate(DEFAULT_POLICY)
    verdict = gate.evaluate(
        contract=contract,
        tool_call=tool_call,
        predicted_delta=delta,
        evidence_verdict="SUPPORT",
    )
    assert verdict.verdict == "BLOCK", f"Expected BLOCK, got {verdict.verdict}"
    assert "vendor" in verdict.detail.lower() or "identity" in verdict.detail.lower(), (
        f"Reason should mention vendor/identity mismatch: {verdict.detail}"
    )


# ---------------------------------------------------------------------------
# R3: Missing temporal scope → BLOCK
# ---------------------------------------------------------------------------


def test_r3_missing_temporal_scope_block(erp_conn: sqlite3.Connection) -> None:
    """R3: Tool call has no month/year → BLOCK for missing temporal scope."""
    contract = _contract()
    tool_call = ToolCall(
        tool_name="archive_invoices",
        arguments={"vendor_id": 4421},  # No month, no year
    )
    # With no temporal filter, everything would match — gate must block this
    delta = _delta([
        "INV-4421-2501", "INV-4421-2502", "INV-4421-2503",
        "INV-4421-2504", "INV-4421-2505", "INV-4421-2506", "INV-4421-2507",
    ])
    gate = NiyamGate(DEFAULT_POLICY)
    verdict = gate.evaluate(
        contract=contract,
        tool_call=tool_call,
        predicted_delta=delta,
        evidence_verdict="SUPPORT",
    )
    assert verdict.verdict == "BLOCK", (
        f"Expected BLOCK for missing temporal scope, got {verdict.verdict}: {verdict.reason_code}"
    )


# ---------------------------------------------------------------------------
# R4: Unauthorized attribute mutation → BLOCK
# ---------------------------------------------------------------------------


def test_r4_unauthorized_attribute_mutation_block() -> None:
    """R4: Delta touches 'amount_usd' which is not in allowed_attributes → BLOCK."""
    contract = _contract()
    tool_call = ToolCall(
        tool_name="archive_invoices",
        arguments={"vendor_id": 4421, "month": 3, "year": 2025},
    )
    # Delta illegally modifies 'amount_usd'
    bad_delta = StateDelta(
        affected_record_ids=["INV-4421-2503"],
        record_deltas=[
            RecordDelta(
                record_id="INV-4421-2503",
                table="vendor_invoices",
                field="amount_usd",  # NOT in allowed_attributes for archive_invoices
                old_value="15200.0",
                new_value="0.0",
            )
        ],
        table="vendor_invoices",
        estimated_row_count=1,
    )
    gate = NiyamGate(DEFAULT_POLICY)
    verdict = gate.evaluate(
        contract=contract,
        tool_call=tool_call,
        predicted_delta=bad_delta,
        evidence_verdict="SUPPORT",
    )
    assert verdict.verdict == "BLOCK", (
        f"Expected BLOCK for unauthorized mutation, got {verdict.verdict}: {verdict.reason_code}"
    )


# ---------------------------------------------------------------------------
# R5: Bulk > threshold → ESCALATE
# ---------------------------------------------------------------------------


def test_r5_bulk_exceeds_threshold_escalate() -> None:
    """R5: 12 records > cardinality_threshold(10) without approval → ESCALATE."""
    contract = _contract()
    tool_call = ToolCall(
        tool_name="archive_invoices",
        arguments={"vendor_id": 4421, "month": 3, "year": 2025},
    )
    # Manufacture a delta with 12 records
    big_delta = _delta([f"INV-4421-{i:04d}" for i in range(12)])
    gate = NiyamGate(DEFAULT_POLICY)
    verdict = gate.evaluate(
        contract=contract,
        tool_call=tool_call,
        predicted_delta=big_delta,
        evidence_verdict="SUPPORT",
    )
    assert verdict.verdict == "ESCALATE", (
        f"Expected ESCALATE for bulk limit, got {verdict.verdict}: {verdict.reason_code}"
    )


# ---------------------------------------------------------------------------
# R6: Unauthorized role for block_user_access → BLOCK
# ---------------------------------------------------------------------------


def test_r6_unauthorized_role_block_user_access() -> None:
    """R6: procurement_manager trying block_user_access → BLOCK (role not permitted)."""
    contract = _contract(
        actor_role="procurement_manager",
        intent="user.block",
        slots={"USER_ID": "USR-PM-002", "DURATION_DAYS": 7},
        raw_text="Block USR-PM-002 for 7 days",
        normalized_text="block_user_access user_id=USR-PM-002 duration_days=7",
    )
    tool_call = ToolCall(
        tool_name="block_user_access",
        arguments={"user_id": "USR-PM-002", "duration_days": 7},
    )
    delta = StateDelta(
        affected_record_ids=["USR-PM-002"],
        record_deltas=[
            RecordDelta(
                record_id="USR-PM-002",
                table="user_access",
                field="status",
                old_value="ACTIVE",
                new_value="BLOCKED",
            )
        ],
        table="user_access",
        estimated_row_count=1,
    )
    gate = NiyamGate(DEFAULT_POLICY)
    verdict = gate.evaluate(
        contract=contract,
        tool_call=tool_call,
        predicted_delta=delta,
        evidence_verdict="SUPPORT",
    )
    assert verdict.verdict == "BLOCK", (
        f"Expected BLOCK for unauthorized role, got {verdict.verdict}: {verdict.reason_code}"
    )


# ---------------------------------------------------------------------------
# R7: Valid update_credit_limit → ALLOW
# ---------------------------------------------------------------------------


def test_r7_valid_update_credit_limit_allow() -> None:
    """R7: finance_admin updating vendor 4421 credit limit → ALLOW."""
    contract = _contract(
        actor_role="finance_admin",
        intent="vendor.credit_limit.update",
        slots={"VENDOR_ID": "4421", "NEW_LIMIT_INR": "600000"},
        raw_text="Update credit limit for vendor 4421 to 600000",
        normalized_text="update_credit_limit vendor_id=4421 new_limit_inr=600000",
    )
    tool_call = ToolCall(
        tool_name="update_credit_limit",
        arguments={"vendor_id": 4421, "new_limit_inr": 600000.0},
    )
    delta = StateDelta(
        affected_record_ids=["4421"],
        record_deltas=[
            RecordDelta(
                record_id="4421",
                table="vendor_credit_limits",
                field="credit_limit_inr",
                old_value="500000.0",
                new_value="600000.0",
            )
        ],
        table="vendor_credit_limits",
        estimated_row_count=1,
    )
    gate = NiyamGate(DEFAULT_POLICY)
    verdict = gate.evaluate(
        contract=contract,
        tool_call=tool_call,
        predicted_delta=delta,
        evidence_verdict="SUPPORT",
    )
    assert verdict.verdict == "ALLOW", (
        f"Expected ALLOW for valid credit limit update, got {verdict.verdict}: {verdict.reason_code}"
    )


# ---------------------------------------------------------------------------
# R8: Schema validation rejects suspend_vendor with short justification
# ---------------------------------------------------------------------------


def test_r8_schema_rejects_short_justification() -> None:
    """R8: suspend_vendor with justification < 10 chars → ToolSchemaValidationError."""
    tool_call_dict = {
        "tool_name": "suspend_vendor",
        "arguments": {
            "vendor_id": 4421,
            "justification": "bad",  # Only 3 chars — below min 10
        },
    }
    with pytest.raises(ToolSchemaValidationError, match="justification"):
        validate_tool_call(tool_call_dict)
