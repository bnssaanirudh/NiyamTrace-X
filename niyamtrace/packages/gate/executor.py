"""
packages/gate/executor.py — ERP Executor (post-gate actual mutation)

Applies the real write to the SQLite ERP ONLY after gate verification.
Returns an ActualDelta for comparison with the PredictedDelta.

MANDATORY EXECUTION MEDIATION:
Direct invocation without a server-issued, context-bound authorization capability
and valid principal context is strictly blocked.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from sqlalchemy.ext.asyncio import AsyncSession

from packages.contracts.schema import EffectCertificate, StateDelta, ToolCall
from packages.gate.broker import ExecutionMediationError
from packages.tools.registry import get_tool_implementation

if TYPE_CHECKING:
    from packages.auth.models import AuthorizationContext


class ERPExecutor:
    """
    Applies gate-approved tool calls to the SQLite ERP and returns the
    actual state delta for fidelity comparison.

    Requires valid server-issued authorization capability.
    Direct unauthorized calls without authorization raise ExecutionMediationError.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def execute(
        self,
        tool_call: ToolCall,
        authorization: EffectCertificate | None = None,
        auth_context: AuthorizationContext | None = None,
        policy: Any | None = None,
        current_snapshot_id: str | None = None,
    ) -> StateDelta:
        """
        Execute the tool call via the registry ONLY with valid server authorization.
        Raises ExecutionMediationError if authorization is missing or invalid.
        """
        if authorization is None:
            raise ExecutionMediationError(
                "ERPExecutor: direct execution without server authorization capability is blocked."
            )

        if auth_context is None:
            raise ExecutionMediationError(
                "ERPExecutor: execution without authenticated principal context is blocked."
            )

        from packages.gate.broker import verify_tool_authorization_binding
        verify_tool_authorization_binding(
            authorization=authorization,
            tool_name=tool_call.tool_name,
            arguments=tool_call.arguments,
            auth_context=auth_context,
            policy=policy,
            current_snapshot_id=current_snapshot_id,
        )

        impl = get_tool_implementation(tool_call.tool_name)
        if impl is None:
            raise ValueError(
                f"ERPExecutor: no execution handler for tool '{tool_call.tool_name}'"
            )

        return await impl.execute(
            self._session,
            tool_call.arguments,
            authorization=authorization,
            auth_context=auth_context,
            policy=policy,
            current_snapshot_id=current_snapshot_id,
        )
