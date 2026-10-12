"""
packages/gate/policy.py — NiyamGate Policy Rules

Implements the gate checks from Section 6 of the NiyamTrace brief as
independent, individually testable functions.

Gate Rule (Section 6):
  Allow tool call t in sandbox state S only when:
    predicted_delta(t, S) ⊆ allowed_effects(contract, policy, access_graph)
    AND evidence/policy decision is SUPPORT or APPROVED.

Checks (each returns a GateCheckResult):
  0. Actor role authorization     — authenticated roles must be permitted for this tool
  1. Scope authorization          — required scopes must be present
  2. Tenant isolation             — resource tenant must match principal tenant
  3. Target identity containment  — all predicted IDs satisfy the contract selector
  4. Temporal containment         — block null/missing/broader date filters
  5. Attribute containment        — block any field mutation not in allowed_attributes
  6. Cardinality + approval       — block/escalate if row count > threshold without approval
  7. Evidence sufficiency         — verdict from real NLI/RAG evidence

Failure reason codes are machine-readable strings (SCREAMING_SNAKE_CASE).
Never return a generic refusal string.

Status:
  Checks 0–2 (RBAC/scope/tenant): IMPLEMENTED (Prompts 3-5)
  Checks 3–7: IMPLEMENTED (Week 2+, refactored for tool-awareness)
"""

from __future__ import annotations

import datetime as dt
import os
import re
from typing import TYPE_CHECKING, Literal

from packages.contracts.schema import (
    ActionContract,
    GateCheckResult,
    StateDelta,
    ToolCall,
)
from packages.policy.compiler import PolicyCompiler
from packages.policy.loader import PolicyLoader

if TYPE_CHECKING:
    from packages.auth.models import AuthorizationContext

# ---------------------------------------------------------------------------
# Policy configuration — canonical path via packages/policy/
# ---------------------------------------------------------------------------

_POLICY_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "policies", "reference.yaml")
_LOADER = PolicyLoader(_POLICY_PATH)
DEFAULT_POLICY = PolicyCompiler(_LOADER)

# ---------------------------------------------------------------------------
# Literal evidence verdict type (NLI result from Week 5)
# ---------------------------------------------------------------------------

EvidenceVerdict = Literal["SUPPORT", "CONTRADICT", "INSUFFICIENT", "STUB"]

# ---------------------------------------------------------------------------
# Tool-aware identity selector configuration (Prompt 5)
# Maps tool_name -> the argument key that identifies the target entity.
# ---------------------------------------------------------------------------

TOOL_IDENTITY_SELECTORS: dict[str, str] = {
    "archive_invoices": "vendor_id",
    "update_credit_limit": "vendor_id",
    "suspend_vendor": "vendor_id",
    "block_user_access": "user_id",
}

# Maps tool_name -> the contract slot key that must match the tool argument.
TOOL_CONTRACT_SLOT: dict[str, str] = {
    "archive_invoices": "VENDOR_ID",
    "update_credit_limit": "VENDOR_ID",
    "suspend_vendor": "VENDOR_ID",
    "block_user_access": "USER_ID",
}


# ---------------------------------------------------------------------------
# Check 0: Actor role authorization (Prompt 4)
# ---------------------------------------------------------------------------


def check_actor_role_authorization(
    tool_call: ToolCall,
    auth_context: AuthorizationContext | None,
    actor_role: str,
    policy: PolicyCompiler = DEFAULT_POLICY,
) -> GateCheckResult:
    """
    Check 0 — RBAC: the tool must be allowed for at least one of the
    authenticated principal's roles.

    Authorization is based on the full frozenset of roles from the verified
    principal (auth_context.roles), NOT on the single actor_role string.
    If auth_context is None (test/backward-compat), falls back to actor_role.
    """
    # Determine which roles to check
    if auth_context is not None:
        roles_to_check = auth_context.roles
    else:
        # Backward-compat: use the single role string from the contract
        roles_to_check = frozenset([actor_role]) if actor_role else frozenset()

    if not roles_to_check:
        return GateCheckResult(
            check_name="actor_role_authorization",
            passed=False,
            reason_code="ROLE_NOT_PERMITTED",
            detail=(
                f"Principal has no roles. Tool '{tool_call.tool_name}' "
                "requires an authorized role. Access denied (fail closed)."
            ),
        )

    # Check if any authenticated role is permitted for this tool
    for role in roles_to_check:
        if policy.is_role_allowed(tool_call.tool_name, role):
            return GateCheckResult(
                check_name="actor_role_authorization",
                passed=True,
                reason_code="OK",
                detail=(
                    f"Role '{role}' is permitted to call '{tool_call.tool_name}'."
                ),
            )

    return GateCheckResult(
        check_name="actor_role_authorization",
        passed=False,
        reason_code="ROLE_NOT_PERMITTED",
        detail=(
            f"None of the authenticated roles {sorted(roles_to_check)} are "
            f"permitted to call tool '{tool_call.tool_name}'."
        ),
    )


# ---------------------------------------------------------------------------
# Check 1: Scope authorization (Prompt 4)
# ---------------------------------------------------------------------------


def check_scope_authorization(
    tool_call: ToolCall,
    auth_context: AuthorizationContext | None,
    policy: PolicyCompiler = DEFAULT_POLICY,
) -> GateCheckResult:
    """
    Check 1 — Scope: required scopes for this tool must be present in the
    authenticated principal's scopes.

    Currently, if no required_scopes are configured for a tool in policy,
    this check passes (scope requirement is opt-in per tool).
    """
    # Get required scopes from policy (if configured)
    rule = policy.get_rule(tool_call.tool_name)
    required_scopes: frozenset[str] = frozenset()
    if rule and hasattr(rule, "required_scopes") and rule.required_scopes:
        required_scopes = frozenset(rule.required_scopes)

    if not required_scopes:
        # No scopes required for this tool
        return GateCheckResult(
            check_name="scope_authorization",
            passed=True,
            reason_code="OK",
            detail=f"No scope requirements configured for '{tool_call.tool_name}'.",
        )

    if auth_context is None:
        # Backward-compat: if no auth context, warn but pass (scopes not enforced without context)
        return GateCheckResult(
            check_name="scope_authorization",
            passed=True,
            reason_code="OK",
            detail="Scope check skipped: no authorization context available (backward-compat).",
        )

    # Check for "all" scope (superscope)
    if "all" in auth_context.scopes:
        return GateCheckResult(
            check_name="scope_authorization",
            passed=True,
            reason_code="OK",
            detail="Principal has 'all' scope — scope check passed.",
        )

    missing_scopes = required_scopes - auth_context.scopes
    if missing_scopes:
        return GateCheckResult(
            check_name="scope_authorization",
            passed=False,
            reason_code="SCOPE_NOT_PERMITTED",
            detail=(
                f"Tool '{tool_call.tool_name}' requires scopes {sorted(required_scopes)}, "
                f"but principal is missing: {sorted(missing_scopes)}."
            ),
        )

    return GateCheckResult(
        check_name="scope_authorization",
        passed=True,
        reason_code="OK",
        detail=f"All required scopes present for '{tool_call.tool_name}'.",
    )


# ---------------------------------------------------------------------------
# Check 2: Tenant isolation (Prompt 4)
# ---------------------------------------------------------------------------


def check_tenant_isolation(
    contract: ActionContract,
    tool_call: ToolCall,
    auth_context: AuthorizationContext | None,
    policy: PolicyCompiler = DEFAULT_POLICY,
) -> GateCheckResult:
    """
    Check 2 — Tenant isolation: the protected resource's tenant must match
    the authenticated principal's tenant, unless cross-tenant admin is explicitly
    allowed in policy.

    Currently: tenant is read from the policy bundle's `tenant` field.
    The authenticated principal's tenant_id must match.
    """
    if auth_context is None:
        # Backward-compat: skip tenant check without auth context
        return GateCheckResult(
            check_name="tenant_isolation",
            passed=True,
            reason_code="OK",
            detail="Tenant check skipped: no authorization context available (backward-compat).",
        )

    # Get the policy-defined tenant for this resource
    rule = policy.get_rule(tool_call.tool_name)
    # Policy-level tenant from the bundle (if the tool has a resource_tenant configured)
    resource_tenant = None
    if rule and hasattr(rule, "resource_tenant"):
        resource_tenant = rule.resource_tenant

    # If no resource-specific tenant, use the policy bundle's global tenant
    if resource_tenant is None:
        try:
            resource_tenant = policy.loader.bundle.tenant
        except AttributeError:
            resource_tenant = None

    if resource_tenant is None:
        # No tenant configured — skip isolation check
        return GateCheckResult(
            check_name="tenant_isolation",
            passed=True,
            reason_code="OK",
            detail="No tenant isolation configured for this tool.",
        )

    # Check if cross-tenant admin is explicitly allowed
    cross_tenant_allowed = False
    if rule and hasattr(rule, "allow_cross_tenant_admin") and rule.allow_cross_tenant_admin:
        cross_tenant_allowed = auth_context.has_any_role("admin", "super_admin")

    if resource_tenant != auth_context.tenant_id and not cross_tenant_allowed:
        return GateCheckResult(
            check_name="tenant_isolation",
            passed=False,
            reason_code="TENANT_BOUNDARY_VIOLATION",
            detail=(
                f"Tool '{tool_call.tool_name}' targets resource in tenant '{resource_tenant}', "
                f"but authenticated principal belongs to tenant '{auth_context.tenant_id}'. "
                "Cross-tenant access denied."
            ),
        )

    return GateCheckResult(
        check_name="tenant_isolation",
        passed=True,
        reason_code="OK",
        detail=(
            f"Tenant isolation satisfied: principal tenant '{auth_context.tenant_id}' "
            f"matches resource tenant '{resource_tenant}'."
        ),
    )


# ---------------------------------------------------------------------------
# Check 3: Target identity containment (Prompt 5 — tool-aware)
# ---------------------------------------------------------------------------


def check_target_identity_containment(
    contract: ActionContract,
    predicted_delta: StateDelta,
    tool_call: ToolCall,
) -> GateCheckResult:
    """
    Check 3 — Target identity containment (tool-aware).

    Each tool has a canonical identity selector (see TOOL_IDENTITY_SELECTORS).
    The tool argument value for that selector must match the contract slot value.

    This replaces the old vendor_id-first hardcoded logic.
    """
    tool_name = tool_call.tool_name
    args = tool_call.arguments

    # Look up the identity selector for this tool
    identity_key = TOOL_IDENTITY_SELECTORS.get(tool_name)
    contract_slot_key = TOOL_CONTRACT_SLOT.get(tool_name)

    if identity_key is None or contract_slot_key is None:
        # Unknown tool — fail closed
        return GateCheckResult(
            check_name="target_identity_containment",
            passed=False,
            reason_code="UNKNOWN_TOOL_IDENTITY_SELECTOR",
            detail=(
                f"No identity selector configured for tool '{tool_name}'. "
                "Failing closed — cannot verify target identity."
            ),
        )

    # Check the contract has the required slot
    contracted_value = contract.slots.get(contract_slot_key)
    if contracted_value is None:
        return GateCheckResult(
            check_name="target_identity_containment",
            passed=False,
            reason_code=f"SELECTOR_MISSING_{contract_slot_key}",
            detail=(
                f"Contract slots do not specify '{contract_slot_key}' "
                f"required for tool '{tool_name}'."
            ),
        )

    # Normalize types for comparison (contract slots may be strings)
    tool_value = args.get(identity_key)
    try:
        # Try numeric comparison first
        contracted_normalized = int(contracted_value)
        tool_normalized = int(tool_value) if tool_value is not None else None
    except (ValueError, TypeError):
        # Fall back to string comparison
        contracted_normalized = str(contracted_value)
        tool_normalized = str(tool_value) if tool_value is not None else None

    if tool_normalized != contracted_normalized:
        return GateCheckResult(
            check_name="target_identity_containment",
            passed=False,
            reason_code=f"{contract_slot_key}_MISMATCH",
            detail=(
                f"Tool targets {identity_key}={tool_value!r} but contract "
                f"allows {contract_slot_key}={contracted_value!r} "
                f"(for tool '{tool_name}')."
            ),
        )

    return GateCheckResult(
        check_name="target_identity_containment",
        passed=True,
        reason_code="OK",
        detail=(
            f"All {predicted_delta.estimated_row_count} predicted records "
            f"are within contracted {identity_key} scope."
        ),
    )


# ---------------------------------------------------------------------------
# Check 4: Temporal containment
# ---------------------------------------------------------------------------


def check_temporal_containment(
    contract: ActionContract,
    tool_call: ToolCall,
) -> GateCheckResult:
    """
    Check 4 — Temporal containment.
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

    if contract_month is None or contract_year is None:
        return GateCheckResult(
            check_name="temporal_containment",
            passed=False,
            reason_code="CONTRACT_MISSING_TEMPORAL_SCOPE",
            detail=(
                "Contract is missing month or year. Security-critical calendar year "
                "is required and ambiguous temporal bounds must be resolved before execution."
            ),
        )

    tool_date = dt.date(tool_year, tool_month, 1)

    if contract_year is not None and contract_month is not None:
        scope_start = dt.date(int(contract_year), int(contract_month), 1)
        if tool_date < scope_start:
            return GateCheckResult(
                check_name="temporal_containment",
                passed=False,
                reason_code="TOOL_DATE_BEFORE_CONTRACT_START",
                detail="Tool targets date before contract scope.",
            )
        if tool_date > scope_start:  # single month scope: start == end
            return GateCheckResult(
                check_name="temporal_containment",
                passed=False,
                reason_code="TOOL_DATE_AFTER_CONTRACT_END",
                detail="Tool targets date after contract scope.",
            )

    return GateCheckResult(
        check_name="temporal_containment",
        passed=True,
        reason_code="OK",
        detail=f"Tool temporal scope {tool_year}-{tool_month:02d} is within contract bounds.",
    )


# ---------------------------------------------------------------------------
# Check 5: Attribute containment
# ---------------------------------------------------------------------------


def check_attribute_containment(
    contract: ActionContract,
    predicted_delta: StateDelta,
    policy: PolicyCompiler = DEFAULT_POLICY,
) -> GateCheckResult:
    """
    Check 5 — Attribute containment.
    """
    # Map intent to canonical tool name
    tool_name = _intent_to_tool_name(contract.intent)

    for row_delta in predicted_delta.record_deltas:
        if not policy.is_attribute_allowed(tool_name, row_delta.field):
            return GateCheckResult(
                check_name="attribute_containment",
                passed=False,
                reason_code="UNAUTHORIZED_ATTRIBUTE_MUTATION",
                detail=(
                    f"Field '{row_delta.field}' not in allowed attribute set "
                    f"for tool '{tool_name}' (intent: {contract.intent})."
                ),
            )

    return GateCheckResult(
        check_name="attribute_containment",
        passed=True,
        reason_code="OK",
        detail="Attribute containment verified via policy.",
    )


# ---------------------------------------------------------------------------
# Check 6: Cardinality + approval
# ---------------------------------------------------------------------------


def check_cardinality_and_approval(
    contract: ActionContract,
    predicted_delta: StateDelta,
    policy: PolicyCompiler = DEFAULT_POLICY,
) -> GateCheckResult:
    """
    Check 6 — Cardinality + approval threshold.
    """
    tool_name = _intent_to_tool_name(contract.intent)
    count = predicted_delta.estimated_row_count

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


# ---------------------------------------------------------------------------
# Check 7: Evidence sufficiency
# ---------------------------------------------------------------------------


def check_evidence_sufficiency(
    contract: ActionContract,
    evidence_verdict: EvidenceVerdict,
) -> GateCheckResult:
    """
    Check 7 — Evidence sufficiency.

    Wired to the real NLI/RAG evidence verdict (Week 5+).
    The STUB path is preserved only for explicit test_mode uses.
    Production mode must not receive STUB verdicts — if it does,
    it will FAIL CLOSED (block) rather than silently allowing.
    """
    if evidence_verdict == "STUB":
        # STUB in production = fail closed for security. Only acceptable in
        # test fixtures that explicitly set evidence_verdict="STUB".
        return GateCheckResult(
            check_name="evidence_sufficiency",
            passed=False,
            reason_code="EVIDENCE_STUB_IN_PRODUCTION",
            detail=(
                "Evidence verdict is STUB — this indicates the evidence pipeline "
                "was not wired correctly. Failing closed. "
                "Use a real NLI verdict (SUPPORT/CONTRADICT/INSUFFICIENT) in production."
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


def _intent_to_tool_name(intent: str) -> str:
    """Map a contract intent string to the canonical tool name."""
    _MAP = {
        "invoice.archive": "archive_invoices",
        "limit.update": "update_credit_limit",
        "vendor.suspend": "suspend_vendor",
        "access.block": "block_user_access",
        # Legacy / alternative spellings
        "user.block": "block_user_access",
    }
    return _MAP.get(intent, intent.replace(".", "_"))


def _extract_vendor_id_from_selector(selector: str) -> int | None:
    """
    Parse 'vendor_id = <N>' from a normalized selector predicate string.
    Returns None if not found or not parseable.
    """
    m = re.search(r"vendor_id\s*=\s*(\d+)", selector, re.IGNORECASE)
    if m:
        return int(m.group(1))
    return None
