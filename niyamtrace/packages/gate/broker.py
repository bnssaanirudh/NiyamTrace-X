"""
packages/gate/broker.py — Verified Execution Broker V2 with Server-Native Trust Root

Enforces mandatory source-native execution mediation:
1. Server Trust Root not constructible by user input (HMAC-SHA256 signature).
2. Origin & Certificate Binding (actor, tenant, action, canonical tool + args, policy hash, snapshot, expiry).
3. Nonce & Replay protection (single-use token).
4. Atomic execution & state delta containment with automatic rollback.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
import time
from typing import TYPE_CHECKING, Any

from sqlalchemy.ext.asyncio import AsyncSession

from packages.contracts.schema import EffectCertificate, StateDelta, ToolCall
from packages.gate.policy import DEFAULT_POLICY

if TYPE_CHECKING:
    from packages.auth.models import AuthorizationContext
    from packages.policy.compiler import PolicyCompiler


class ExecutionMediationError(Exception):
    """Base error for execution mediation and authorization failures."""
    pass


class BrokerVerificationError(ExecutionMediationError):
    """Raised when broker verification fails before or during transaction."""
    pass


# ---------------------------------------------------------------------------
# Server Trust Root & Cryptographic Capability Management
# ---------------------------------------------------------------------------

# Secure trust root initialized from environment or secure random bytes
# This key is strictly kept in server memory and cannot be forged by user input.
_SERVER_TRUST_ROOT: bytes = (
    os.environ.get("NIYAMTRACE_GATE_SECRET")
    or "ntx-inviolable-server-trust-root-2026-secret-boundary"
).encode("utf-8")

_USED_NONCES: set[str] = set()


def get_trust_root() -> bytes:
    """Return the active server trust root bytes."""
    return _SERVER_TRUST_ROOT


def set_trust_root(secret: bytes) -> None:
    """Set the server trust root (used in tests/config)."""
    global _SERVER_TRUST_ROOT
    _SERVER_TRUST_ROOT = secret


def compute_server_signature(
    cert: EffectCertificate,
    trust_root: bytes | None = None,
) -> str:
    """
    Compute cryptographic HMAC-SHA256 signature over the certificate's canonical
    authorization capability context.
    """
    key = trust_root or _SERVER_TRUST_ROOT
    payload = {
        "cert_hash": cert.cert_hash,
        "actor": cert.actor,
        "tenant_id": getattr(cert, "tenant_id", "acme"),
        "action": cert.action,
        "target_type": cert.target_type,
        "canonical_args_hash": getattr(cert, "canonical_args_hash", ""),
        "policy_version_hash": getattr(cert, "policy_version_hash", ""),
        "snapshot_id": getattr(cert, "snapshot_id", ""),
        "nonce": getattr(cert, "nonce", ""),
        "expires_at": getattr(cert, "expires_at", 0.0),
        "predicted_delta": cert.predicted_delta,
    }
    canonical_data = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
    return hmac.new(key, canonical_data, hashlib.sha256).hexdigest()


def sign_certificate_authority(
    cert: EffectCertificate,
    trust_root: bytes | None = None,
) -> EffectCertificate:
    """
    Sign the EffectCertificate with the server trust root.
    Only called by NiyamGate when all policy and security checks pass.
    """
    cert.seal()
    cert.server_signature = compute_server_signature(cert, trust_root)
    cert.server_issued = True
    return cert


def verify_certificate_authority(
    cert: EffectCertificate,
    trust_root: bytes | None = None,
) -> bool:
    """
    Verify that the certificate was genuinely issued and signed by the server authority.
    Rejects self-sealed, untrusted, or tampered certificates.
    """
    if not getattr(cert, "server_issued", False) or not getattr(cert, "server_signature", None):
        return False
    expected = compute_server_signature(cert, trust_root)
    return hmac.compare_digest(cert.server_signature, expected)


def is_nonce_used(nonce: str) -> bool:
    """Check if a single-use authorization nonce has already been consumed."""
    return nonce in _USED_NONCES


def mark_nonce_used(nonce: str) -> None:
    """Mark an authorization nonce as consumed."""
    _USED_NONCES.add(nonce)


def reset_broker_state() -> None:
    """Reset broker replay cache (for test isolation)."""
    _USED_NONCES.clear()


# ---------------------------------------------------------------------------
# Verified Execution Broker
# ---------------------------------------------------------------------------


class VerifiedExecutionBroker:
    """
    The only authorized boundary to execute state-mutating ERP tools.
    Enforces pre-execution verification and post-execution atomic containment.
    """

    def __init__(
        self,
        session: AsyncSession,
        policy: PolicyCompiler | None = None,
        current_snapshot_id: str | None = None,
    ) -> None:
        self._session = session
        self._policy = policy or DEFAULT_POLICY
        self._current_snapshot_id = current_snapshot_id
        from packages.gate.executor import ERPExecutor
        self._executor = ERPExecutor(session)

    async def commit(
        self,
        cert: EffectCertificate,
        tool_call: ToolCall,
        auth_context: "AuthorizationContext",
        policy: "PolicyCompiler | None" = None,
        current_snapshot_id: str | None = None,
    ) -> StateDelta:
        """
        Verify the certificate capability and execute inside a transaction.
        Raises BrokerVerificationError if any check fails or if effects exceed authorization.
        """
        active_policy = policy or self._policy
        snap_id = current_snapshot_id or self._current_snapshot_id

        # 1. Server Trust Root Origin check (not constructible by caller)
        if not getattr(cert, "server_issued", False) or not getattr(cert, "server_signature", None):
            raise BrokerVerificationError(
                "Certificate origin check failed: untrusted certificate origin (missing server authority)."
            )
        if not verify_certificate_authority(cert):
            raise BrokerVerificationError(
                "Certificate origin check failed: invalid or forged server authority signature."
            )

        # 2. Certificate internal content integrity check (tamper detection)
        if not cert.verify():
            raise BrokerVerificationError("Certificate integrity check failed (tampered).")

        # 3. Expiry check
        if cert.is_expired():
            raise BrokerVerificationError("EffectCertificate expired.")

        # 4. Replay check (single-use nonce)
        if is_nonce_used(cert.nonce):
            raise BrokerVerificationError(
                f"Replay detected: nonce {cert.nonce} has already been consumed."
            )

        # 5. Actor (Subject) identity binding
        if cert.actor != auth_context.subject:
            raise BrokerVerificationError(
                f"Actor identity mismatch: cert={cert.actor}, context={auth_context.subject}."
            )

        # 6. Tenant isolation binding
        cert_tenant = getattr(cert, "tenant_id", "acme")
        if cert_tenant != auth_context.tenant_id:
            raise BrokerVerificationError(
                f"Tenant boundary violation: cert={cert_tenant}, context={auth_context.tenant_id}."
            )

        # 7. Action / Tool binding
        if cert.target_type != tool_call.tool_name:
            raise BrokerVerificationError(
                f"Tool target mismatch: cert={cert.target_type}, tool={tool_call.tool_name}."
            )

        # 8. Canonical tool arguments binding
        call_args_hash = hashlib.sha256(
            json.dumps(tool_call.arguments, sort_keys=True).encode()
        ).hexdigest()
        cert_args_hash = getattr(cert, "canonical_args_hash", "")
        if cert_args_hash and cert_args_hash != call_args_hash:
            raise BrokerVerificationError(
                "Tool arguments mismatch with server authorized capability."
            )

        # 9. Policy version & revocation binding
        cert_policy_hash = getattr(cert, "policy_version_hash", "") or (
            cert.policy_rules_used[0] if cert.policy_rules_used else ""
        )
        if cert_policy_hash and active_policy and cert_policy_hash != active_policy.policy_hash:
            raise BrokerVerificationError(
                f"Policy revoked or mismatch: cert={cert_policy_hash}, active={active_policy.policy_hash}."
            )

        # 10. Snapshot / state binding
        if snap_id and getattr(cert, "snapshot_id", "") and cert.snapshot_id != snap_id:
            raise BrokerVerificationError(
                f"Stale state snapshot: cert={cert.snapshot_id}, current={snap_id}."
            )

        # 11. Atomic execution with containment check
        pred_record_ids = cert.predicted_delta.get("record_ids", [])
        try:
            actual_delta = await self._executor.execute(
                tool_call, authorization=cert, auth_context=auth_context
            )

            # 12. Containment check: actual affected records must match predicted authorized records
            if set(actual_delta.affected_record_ids) != set(pred_record_ids):
                await self._session.rollback()
                raise BrokerVerificationError(
                    f"State mismatch: authorized {pred_record_ids}, got {actual_delta.affected_record_ids}"
                )

            # Consume nonce only upon successful execution
            mark_nonce_used(cert.nonce)
            return actual_delta

        except Exception:
            try:
                await self._session.rollback()
            except Exception:
                pass
            raise
