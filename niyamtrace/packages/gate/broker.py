"""
packages/gate/broker.py — Verified Execution Broker V2

Integrates transaction-first verification of the EffectCertificate before mutation.
"""

import time
from sqlalchemy.ext.asyncio import AsyncSession
from packages.contracts.schema import EffectCertificate, ToolCall, StateDelta
from packages.gate.executor import ERPExecutor

class BrokerVerificationError(Exception):
    pass

class VerifiedExecutionBroker:
    def __init__(self, session: AsyncSession):
        self._session = session
        self._executor = ERPExecutor(session)
        
    async def commit(self, cert: EffectCertificate, tool_call: ToolCall, auth_context) -> StateDelta:
        """
        Verify the certificate and execute, raising an error if it doesn't match the authorized delta.
        """
        # 1. Verify certificate integrity
        if not cert.verify():
            raise BrokerVerificationError("Certificate integrity check failed (tampered).")
            
        # 2. Verify actor identity matches
        if cert.actor != auth_context.subject:
            raise BrokerVerificationError("Actor identity mismatch between context and certificate.")
            
        # 3. Expiry check
        if hasattr(cert, "expires_at") and cert.expires_at < time.time():
            raise BrokerVerificationError("EffectCertificate expired.")
            
        # 4. Execute to recompute actual delta (we are inside the transaction)
        actual_delta = await self._executor.execute(tool_call)
        
        # 5. Verify actual state matches predicted
        pred_record_ids = cert.predicted_delta.get("record_ids", [])
        if set(actual_delta.affected_record_ids) != set(pred_record_ids):
            raise BrokerVerificationError(f"State mismatch: authorized {pred_record_ids}, got {actual_delta.affected_record_ids}")
            
        return actual_delta
