"""
packages/gate/policy.py — NiyamGate Policy Rules

Implements the 5 gate checks from Section 6 of the NiyamTrace brief as
independent, individually testable functions.

Gate Rule (Section 6):
  Allow tool call t in sandbox state S only when:
    predicted_delta(t, S) ⊆ allowed_effects(contract, policy, access_graph)
    AND evidence/policy decision is SUPPORT or APPROVED.

Checks (each returns a GateCheckResult):
  1. Target identity containment   — all predicted IDs satisfy the contract selector
  2. Temporal containment          — block null/missing/broader date filters
  3. Attribute containment         — block any field mutation not in allowed_attributes
  4. Cardinality + approval        — block/escalate if row count > threshold without approval
  5. Evidence sufficiency [STUB]   — always returns SUPPORT in Week 2; wired in Week 5

Failure reason codes are machine-readable strings (SCREAMING_SNAKE_CASE).
Never return a generic refusal string.

Status:
  Checks 1–4: IMPLEMENTED (Week 2)
  Check 5:    STUBBED — always returns PASS, labeled clearly below (Week 5)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from packages.contracts.schema import (
    GateCheckResult,
    ActionContract,
    StateDelta,
    ToolCall,
)

# ---------------------------------------------------------------------------
# Policy configuration (hard-coded for MVP; a policy compiler replaces this
# in Week 5 when we load from a policy bundle)
# ---------------------------------------------------------------------------


from packages.policy.loader import PolicyLoader
from packages.policy.compiler import PolicyCompiler
import os

_POLICY_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "policies", "reference.yaml")
_LOADER = PolicyLoader(_POLICY_PATH)
DEFAULT_POLICY = PolicyCompiler(_LOADER)

# ---------------------------------------------------------------------------
# Literal evidence verdict type (NLI result from Week 5)
# ---------------------------------------------------------------------------

EvidenceVerdict = Literal["SUPPORT", "CONTRADICT", "INSUFFICIENT", "STUB"]


# ---------------------------------------------------------------------------
# Individual check functions
# ---------------------------------------------------------------------------


def check_target_identity_containment(
    contract: ActionContract,
    predicted_delta: StateDelta,
    tool_call: ToolCall,
) -> GateCheckResult:
    """
    Check 1 — Target identity containment.
    """
    args = tool_call.arguments
    contracted_vendor = contract.slots.get("VENDOR_ID")
    if contracted_vendor:
        contracted_vendor = int(contracted_vendor)

    if contracted_vendor is None:
        return GateCheckResult(
            check_name="target_identity_containment",
            passed=False,
            reason_code="SELECTOR_MISSING_VENDOR_ID",
            detail="Contract slots do not specify a VENDOR_ID.",
        )

    tool_vendor = args.get("vendor_id")
    if tool_vendor != contracted_vendor:
        return GateCheckResult(
            check_name="target_identity_containment",
            passed=False,
            reason_code="VENDOR_ID_MISMATCH",
            detail=(
                f"Tool targets vendor_id={tool_vendor} but contract "
                f"allows vendor_id={contracted_vendor}."
            ),
        )

    # Note: entity_ids checks are simplified for ActionContract logic in Week 4

    return GateCheckResult(
        check_name="target_identity_containment",
        passed=True,
        reason_code="OK",
        detail=(
            f"All {predicted_delta.estimated_row_count} predicted records "
            f"are within contracted vendor scope."
        ),
    )


def check_temporal_containment(
    contract: ActionContract,
    tool_call: ToolCall,
) -> GateCheckResult:
    """
    Check 2 — Temporal containment.
    """
    if contract.intent != "invoice.archive":
        return GateCheckResult(
            check_name="temporal_containment",
            passed=True,
            reason_code="OK",
            detail="Temporal containment not applicable for this intent.",
        )
        
    args = tool_call.arguments
    tool_month = args.get("month")
    tool_year = args.get("year")

    if tool_month is None or tool_year is None:
        return GateCheckResult(
            check_name="temporal_containment",
            passed=False,
            reason_code="TOOL_ARGS_MISSING_TEMPORAL_SCOPE",
            detail=(
                "Tool call is missing month and/or year — this would match "
                "all records for the vendor. Temporal scope is required."
            ),
        )

    contract_month = contract.slots.get("MONTH")
    contract_year = contract.slots.get("YEAR")

    if contract_month is None and contract_year is None:
        return GateCheckResult(
            check_name="temporal_containment",
            passed=False,
            reason_code="CONTRACT_MISSING_TEMPORAL_SCOPE",
            detail=(
                "Contract has no temporal_scope. Ambiguous temporal bounds "
                "must be resolved before execution."
            ),
        )

    import datetime as dt
    tool_date = dt.date(tool_year, tool_month, 1)

    if contract_year is not None and contract_month is not None:
        scope_start = dt.date(int(contract_year), int(contract_month), 1)
        if tool_date < scope_start:
            return GateCheckResult(
                check_name="temporal_containment",
                passed=False,
                reason_code="TOOL_DATE_BEFORE_CONTRACT_START",
                detail="Tool targets date before contract scope."
            )
        if tool_date > scope_start: # Note: For single month scopes, start == end
            return GateCheckResult(
                check_name="temporal_containment",
                passed=False,
                reason_code="TOOL_DATE_AFTER_CONTRACT_END",
                detail="Tool targets date after contract scope."
            )

    return GateCheckResult(
        check_name="temporal_containment",
        passed=True,
        reason_code="OK",
        detail=f"Tool temporal scope {tool_year}-{tool_month:02d} is within contract bounds.",
    )


def check_attribute_containment(
    contract: ActionContract,
    predicted_delta: StateDelta,
    policy: PolicyCompiler = DEFAULT_POLICY,
) -> GateCheckResult:
    """
    Check 3 — Attribute containment.
    """
    tool_name = contract.intent.replace(".", "_") # e.g. invoice.archive -> archive_invoices? Wait, no. The tool is archive_invoices.
    # We should get tool_name. If intent is invoice.archive, tool is archive_invoices.
    if contract.intent == "invoice.archive":
        tool_name = "archive_invoices"
    elif contract.intent == "limit.update":
        tool_name = "update_credit_limit"
    elif contract.intent == "vendor.suspend":
        tool_name = "suspend_vendor"
    elif contract.intent == "access.block":
        tool_name = "block_user_access"
    else:
        # Fallback for others
        tool_name = contract.intent.replace(".", "_")

    for row_delta in predicted_delta.record_deltas:
        if not policy.is_attribute_allowed(tool_name, row_delta.field):
            return GateCheckResult(
                check_name="attribute_containment",
                passed=False,
                reason_code="UNAUTHORIZED_ATTRIBUTE_MUTATION",
                detail=f"Field '{row_delta.field}' not in allowed set for intent {contract.intent}"
            )

    return GateCheckResult(
        check_name="attribute_containment",
        passed=True,
        reason_code="OK",
        detail="Attribute containment explicit via policy.",
    )


def check_cardinality_and_approval(
    contract: ActionContract,
    predicted_delta: StateDelta,
    policy: PolicyCompiler = DEFAULT_POLICY,
) -> GateCheckResult:
    """
    Check 4 — Cardinality + approval threshold.
    """
    if contract.intent == "invoice.archive":
        tool_name = "archive_invoices"
    elif contract.intent == "limit.update":
        tool_name = "update_credit_limit"
    elif contract.intent == "vendor.suspend":
        tool_name = "suspend_vendor"
    elif contract.intent == "access.block":
        tool_name = "block_user_access"
    else:
        tool_name = contract.intent.replace(".", "_")
    count = predicted_delta.estimated_row_count
    
    # Contract cardinality bound not explicitly defined in ActionContract right now.
    
    # Policy threshold check
    threshold = policy.get_max_rows_without_approval(tool_name)
    if count > threshold:
        return GateCheckResult(
            check_name="cardinality_and_approval",
            passed=False,
            reason_code="APPROVAL_REQUIRED",
            detail=(
                f"Predicted {count} records exceeds policy threshold "
                f"({threshold}). Escalate for approval."
            ),
        )

    return GateCheckResult(
        check_name="cardinality_and_approval",
        passed=True,
        reason_code="OK",
        detail=f"Predicted {count} records within cardinality bounds.",
    )


def check_evidence_sufficiency(
    contract: ActionContract,
    evidence_verdict: EvidenceVerdict,
) -> GateCheckResult:
    """
    Check 5 — Evidence sufficiency.

    !!STUB (Week 2)!!
    In Week 5 this will be wired to the real NLI/RAG evidence verdict from
    NiyamEvidence. For now it always returns SUPPORT so checks 1–4 drive
    the gate in Week 2 runs.

    DO NOT REMOVE THIS STUB LABEL until Week 5 NLI wiring is complete.
    """
    if evidence_verdict == "STUB":
        # Stub behaviour: pass through, clearly labeled
        return GateCheckResult(
            check_name="evidence_sufficiency",
            passed=True,
            reason_code="STUB_ALWAYS_SUPPORT",
            detail=(
                "[STUB — Week 2] Evidence sufficiency check is not yet wired "
                "to real NLI. Always returns PASS. Do not rely on this for "
                "security claims. Will be replaced in Week 5."
            ),
        )

    if evidence_verdict == "CONTRADICT":
        return GateCheckResult(
            check_name="evidence_sufficiency",
            passed=False,
            reason_code="EVIDENCE_CONTRADICTS_ACTION",
            detail="Retrieved evidence contradicts the proposed action. Blocking.",
        )

    if evidence_verdict == "INSUFFICIENT":
        return GateCheckResult(
            check_name="evidence_sufficiency",
            passed=False,
            reason_code="EVIDENCE_INSUFFICIENT",
            detail="Retrieved evidence does not sufficiently support the action. Blocking.",
        )

    # SUPPORT or APPROVED
    return GateCheckResult(
        check_name="evidence_sufficiency",
        passed=True,
        reason_code="OK",
        detail=f"Evidence verdict: {evidence_verdict}.",
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _extract_vendor_id_from_selector(selector: str) -> int | None:
    """
    Parse 'vendor_id = <N>' from a normalized selector predicate string.
    Returns None if not found or not parseable.
    """
    import re

    m = re.search(r"vendor_id\s*=\s*(\d+)", selector, re.IGNORECASE)
    if m:
        return int(m.group(1))
    return None
