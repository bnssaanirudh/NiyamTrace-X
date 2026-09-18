"""
packages/gate/gate.py — NiyamGate Evaluator

Runs all 5 gate checks in order and aggregates into a single GateDecision.
The gate is the only component allowed to authorize execution.

Gate Rule (Section 6 of brief):
  Allow only when predicted_delta ⊆ allowed_effects AND evidence is SUPPORT/APPROVED.

All checks are run independently so callers get a full diagnostic
(not just the first failure). Verdict = ALLOW only if all checks pass.
ESCALATE is returned when cardinality approval is needed (not a generic block).

Status: IMPLEMENTED (Week 2)
"""

from __future__ import annotations

import time
from typing import Any

from packages.contracts.schema import (
    GateCheckResult,
    GateDecision,
    ActionContract,
    StateDelta,
    ToolCall,
)
from packages.gate.policy import (
    DEFAULT_POLICY,
    EvidenceVerdict,
    check_attribute_containment,
    check_cardinality_and_approval,
    check_evidence_sufficiency,
    check_target_identity_containment,
    check_temporal_containment,
)
from packages.policy.compiler import PolicyCompiler


class NiyamGate:
    """
    Evaluates whether a proposed tool call should be allowed, blocked, or
    escalated based on the intent contract, predicted state delta, and policy.
    """

    def __init__(self, policy: PolicyCompiler = DEFAULT_POLICY) -> None:
        self._policy = policy

    def evaluate(
        self,
        contract: ActionContract,
        predicted_delta: StateDelta,
        tool_call: ToolCall,
        evidence_verdict: EvidenceVerdict = "STUB",
    ) -> GateDecision:
        """
        Run all 5 checks and return a GateDecision.

        Verdicts:
          ALLOW     — all checks pass
          BLOCK     — one or more checks failed (non-escalatable)
          ESCALATE  — cardinality approval required (soft block, not a policy violation)
        """
        t0 = time.perf_counter()

        results: list[GateCheckResult] = []

        # Check 1: Target identity containment
        results.append(
            check_target_identity_containment(contract, predicted_delta, tool_call)
        )

        # Check 2: Temporal containment
        results.append(check_temporal_containment(contract, tool_call))

        # Check 3: Attribute containment
        results.append(check_attribute_containment(contract, predicted_delta))

        # Check 4: Cardinality + approval
        results.append(
            check_cardinality_and_approval(contract, predicted_delta, self._policy)
        )

        # Check 5: Evidence sufficiency (STUB in Week 2)
        results.append(check_evidence_sufficiency(contract, evidence_verdict))

        latency_ms = (time.perf_counter() - t0) * 1000

        # Aggregate verdict
        failed = [r for r in results if not r.passed]

        if not failed:
            from packages.contracts.schema import EffectCertificate
            cert = EffectCertificate(
                trace_id=contract.contract_id,
                actor=contract.actor_role,
                action=contract.intent,
                target_type=tool_call.tool_name,
                selector=contract.slots,
                policy_rules_used=["DEFAULT-POLICY"],  # Mocked for now
                evidence_refs=["evidence-1"],
                predicted_delta={
                    "rows_changed": predicted_delta.estimated_row_count,
                    "fields_changed": [d.field for d in predicted_delta.record_deltas],
                    "before_hash": "a1b2c3d4",
                    "after_hash": "e5f6g7h8"
                }
            )
            return GateDecision(
                verdict="ALLOW",
                reason_code="ALL_CHECKS_PASSED",
                detail=f"All {len(results)} gate checks passed.",
                check_results=results,
                latency_ms=latency_ms,
                effect_certificate=cert,
                policy_hash=self._policy.policy_hash
            )

        # Distinguish ESCALATE (approval needed) from BLOCK (hard failure)
        if all(r.reason_code == "APPROVAL_REQUIRED" for r in failed):
            first = failed[0]
            return GateDecision(
                verdict="ESCALATE",
                reason_code=first.reason_code,
                detail=first.detail,
                check_results=results,
                latency_ms=latency_ms,
                correction={
                    "action": "REQUEST_APPROVAL",
                    "approver_role": "finance_director",
                    "predicted_record_count": predicted_delta.estimated_row_count,
                },
                policy_hash=self._policy.policy_hash
            )

        # BLOCK — return first hard failure reason code plus full diagnostics
        first_failure = failed[0]
        return GateDecision(
            verdict="BLOCK",
            reason_code=first_failure.reason_code,
            detail=first_failure.detail,
            check_results=results,
            latency_ms=latency_ms,
            correction=_build_correction(first_failure),
            policy_hash=self._policy.policy_hash
        )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _build_correction(check: GateCheckResult) -> dict[str, Any]:
    """
    Build a machine-readable structured correction payload for a failed check.
    This payload can be consumed by callers to generate user-facing guidance
    or route the request programmatically.
    """
    return {
        "failed_check": check.check_name,
        "reason_code": check.reason_code,
        "detail": check.detail,
        "suggested_action": _suggest_action(check.reason_code),
    }


def _suggest_action(reason_code: str) -> str:
    suggestions = {
        "VENDOR_ID_MISMATCH": "CORRECT_VENDOR_SCOPE",
        "SELECTOR_MISSING_VENDOR_ID": "CLARIFY_VENDOR",
        "UNAUTHORIZED_RECORD_IDS": "RESTRICT_ENTITY_IDS",
        "TOOL_ARGS_MISSING_TEMPORAL_SCOPE": "SPECIFY_MONTH_AND_YEAR",
        "CONTRACT_MISSING_TEMPORAL_SCOPE": "CLARIFY_TEMPORAL_BOUNDS",
        "TOOL_DATE_BEFORE_CONTRACT_START": "ADJUST_DATE_RANGE",
        "TOOL_DATE_AFTER_CONTRACT_END": "ADJUST_DATE_RANGE",
        "UNAUTHORIZED_ATTRIBUTE_MUTATION": "REMOVE_UNAUTHORIZED_FIELDS",
        "CARDINALITY_BOUND_EXCEEDED": "SPLIT_INTO_SMALLER_BATCH",
        "APPROVAL_REQUIRED": "REQUEST_APPROVAL",
        "EVIDENCE_CONTRADICTS_ACTION": "REVIEW_POLICY_OR_CONTEXT",
        "EVIDENCE_INSUFFICIENT": "PROVIDE_SUPPORTING_EVIDENCE",
    }
    return suggestions.get(reason_code, "CONTACT_ADMINISTRATOR")
