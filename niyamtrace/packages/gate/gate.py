"""
packages/gate/gate.py — NiyamGate Evaluator

Runs all gate checks in order and aggregates into a single GateDecision.
The gate is the only component allowed to authorize execution.

Gate Rule (Section 6 of brief):
  Allow only when predicted_delta ⊆ allowed_effects AND evidence is SUPPORT/APPROVED.

All checks are run independently so callers get a full diagnostic
(not just the first failure). Verdict = ALLOW only if all checks pass.
ESCALATE is returned when cardinality approval is needed (not a generic block).

Check order:
  0. actor_role_authorization  — RBAC: authenticated roles must permit this tool
  1. scope_authorization       — required scopes must be present
  2. tenant_isolation          — resource tenant must match principal tenant
  3. target_identity_containment — tool-aware: correct entity selector
  4. temporal_containment      — date/time scope must be within contract
  5. attribute_containment     — no unauthorized field mutations
  6. cardinality_and_approval  — row count within threshold or escalate
  7. evidence_sufficiency      — NLI verdict must be SUPPORT/APPROVED

Status: IMPLEMENTED (Prompts 3-7 security hardening)
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

from packages.contracts.schema import (
    ActionContract,
    GateCheckResult,
    GateDecision,
    StateDelta,
    ToolCall,
)
from packages.gate.policy import (
    DEFAULT_POLICY,
    EvidenceVerdict,
    check_actor_role_authorization,
    check_attribute_containment,
    check_cardinality_and_approval,
    check_evidence_sufficiency,
    check_scope_authorization,
    check_target_identity_containment,
    check_temporal_containment,
    check_tenant_isolation,
)
from packages.policy.compiler import PolicyCompiler

if TYPE_CHECKING:
    from packages.auth.models import AuthorizationContext


class NiyamGate:
    """
    Evaluates whether a proposed tool call should be allowed, blocked, or
    escalated based on the intent contract, predicted state delta, and policy.

    Security: all authorization decisions use the full AuthorizationContext
    (all roles, scopes, tenant) — not a single actor_role string.
    """

    def __init__(self, policy: PolicyCompiler = DEFAULT_POLICY) -> None:
        self._policy = policy

    def evaluate(
        self,
        contract: ActionContract,
        predicted_delta: StateDelta,
        tool_call: ToolCall,
        evidence_verdict: EvidenceVerdict = "SUPPORT",
        auth_context: AuthorizationContext | None = None,
    ) -> GateDecision:
        """
        Run all gate checks and return a GateDecision.

        Verdicts:
          ALLOW     — all checks pass
          BLOCK     — one or more checks failed (non-escalatable)
          ESCALATE  — cardinality approval required (soft block, not a policy violation)

        Args:
            contract:         The semantic action contract from NLP compilation.
            predicted_delta:  The state delta predicted by the shadow simulator.
            tool_call:        The proposed tool invocation.
            evidence_verdict: NLI verdict from the evidence retriever.
            auth_context:     Full authenticated principal context (Prompt 3).
                              When provided, RBAC/scope/tenant checks use the full
                              frozenset of roles. When None, backward-compat mode
                              uses contract.actor_role.
        """
        t0 = time.perf_counter()

        results: list[GateCheckResult] = []

        # Check 0: Actor role authorization (RBAC)
        results.append(
            check_actor_role_authorization(
                tool_call=tool_call,
                auth_context=auth_context,
                actor_role=contract.actor_role,
                policy=self._policy,
            )
        )

        # Check 1: Scope authorization
        results.append(
            check_scope_authorization(
                tool_call=tool_call,
                auth_context=auth_context,
                policy=self._policy,
            )
        )

        # Check 2: Tenant isolation
        results.append(
            check_tenant_isolation(
                contract=contract,
                tool_call=tool_call,
                auth_context=auth_context,
                policy=self._policy,
            )
        )

        # Check 3: Target identity containment (tool-aware)
        results.append(
            check_target_identity_containment(contract, predicted_delta, tool_call)
        )

        # Check 4: Temporal containment
        results.append(check_temporal_containment(contract, tool_call))

        # Check 5: Attribute containment
        results.append(check_attribute_containment(contract, predicted_delta, self._policy))

        # Check 6: Cardinality + approval
        results.append(
            check_cardinality_and_approval(contract, predicted_delta, self._policy)
        )

        # Check 7: Evidence sufficiency
        results.append(check_evidence_sufficiency(contract, evidence_verdict))

        latency_ms = (time.perf_counter() - t0) * 1000

        # Aggregate verdict
        failed = [r for r in results if not r.passed]

        if not failed:
            import hashlib
            import json
            import uuid

            from data.synthetic.erp import SEED_SNAPSHOT_ID
            from packages.contracts.schema import EffectCertificate
            from packages.gate.broker import sign_certificate_authority

            # Build a real certificate with actual provenance values
            policy_hash = self._policy.policy_hash
            evidence_hash = hashlib.sha256(
                json.dumps({"verdict": evidence_verdict}, sort_keys=True).encode()
            ).hexdigest()[:16]

            actor_id = auth_context.subject if auth_context else contract.actor_id
            tenant_id = auth_context.tenant_id if auth_context else "acme"
            roles_repr = sorted(auth_context.roles) if auth_context else [contract.actor_role]
            canonical_args_hash = hashlib.sha256(
                json.dumps(tool_call.arguments, sort_keys=True).encode()
            ).hexdigest()

            cert = EffectCertificate(
                trace_id=contract.contract_id,
                actor=actor_id,
                action=contract.intent,
                target_type=tool_call.tool_name,
                selector=contract.slots,
                policy_rules_used=[policy_hash],
                evidence_refs=[evidence_hash],
                predicted_delta={
                    "rows_changed": predicted_delta.estimated_row_count,
                    "fields_changed": [d.field for d in predicted_delta.record_deltas],
                    "record_ids": predicted_delta.affected_record_ids,
                    "tenant": tenant_id,
                    "roles": roles_repr,
                },
                tenant_id=tenant_id,
                canonical_args_hash=canonical_args_hash,
                policy_version_hash=policy_hash,
                snapshot_id=SEED_SNAPSHOT_ID,
                nonce=str(uuid.uuid4()),
                expires_at=time.time() + 60.0,
                server_issued=True,
            )
            cert = cert.seal()
            cert = sign_certificate_authority(cert)

            return GateDecision(
                verdict="ALLOW",
                reason_code="ALL_CHECKS_PASSED",
                detail=f"All {len(results)} gate checks passed.",
                check_results=results,
                latency_ms=latency_ms,
                effect_certificate=cert,
                policy_hash=policy_hash,
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
                policy_hash=self._policy.policy_hash,
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
            policy_hash=self._policy.policy_hash,
        )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _build_correction(check: GateCheckResult) -> dict[str, Any]:
    """
    Build a machine-readable structured correction payload for a failed check.
    """
    return {
        "failed_check": check.check_name,
        "reason_code": check.reason_code,
        "detail": check.detail,
        "suggested_action": _suggest_action(check.reason_code),
    }


def _suggest_action(reason_code: str) -> str:
    suggestions = {
        # RBAC/scope/tenant
        "ROLE_NOT_PERMITTED": "VERIFY_ROLE_ASSIGNMENT",
        "SCOPE_NOT_PERMITTED": "VERIFY_SCOPE_GRANT",
        "TENANT_BOUNDARY_VIOLATION": "USE_SAME_TENANT_CREDENTIALS",
        # Identity containment
        "VENDOR_ID_MISMATCH": "CORRECT_VENDOR_SCOPE",
        "SELECTOR_MISSING_VENDOR_ID": "CLARIFY_VENDOR",
        "USER_ID_MISMATCH": "CORRECT_USER_SCOPE",
        "SELECTOR_MISSING_USER_ID": "CLARIFY_USER",
        "UNKNOWN_TOOL_IDENTITY_SELECTOR": "CONTACT_ADMINISTRATOR",
        # Temporal
        "TOOL_ARGS_MISSING_TEMPORAL_SCOPE": "SPECIFY_MONTH_AND_YEAR",
        "CONTRACT_MISSING_TEMPORAL_SCOPE": "CLARIFY_TEMPORAL_BOUNDS",
        "TOOL_DATE_BEFORE_CONTRACT_START": "ADJUST_DATE_RANGE",
        "TOOL_DATE_AFTER_CONTRACT_END": "ADJUST_DATE_RANGE",
        # Attribute
        "UNAUTHORIZED_ATTRIBUTE_MUTATION": "REMOVE_UNAUTHORIZED_FIELDS",
        # Cardinality
        "CARDINALITY_BOUND_EXCEEDED": "SPLIT_INTO_SMALLER_BATCH",
        "APPROVAL_REQUIRED": "REQUEST_APPROVAL",
        # Evidence
        "EVIDENCE_CONTRADICTS_ACTION": "REVIEW_POLICY_OR_CONTEXT",
        "EVIDENCE_INSUFFICIENT": "PROVIDE_SUPPORTING_EVIDENCE",
        "EVIDENCE_STUB_IN_PRODUCTION": "WIRE_REAL_NLI_ENGINE",
    }
    return suggestions.get(reason_code, "CONTACT_ADMINISTRATOR")
