"""
packages/gate/executor.py — ERP Executor (post-gate actual mutation)

Applies the real write to the SQLite ERP ONLY after the gate returns ALLOW.
Returns an ActualDelta for comparison with the PredictedDelta.

Forwards execution to the registered tool implementations (Phase 6).
"""

from __future__ import annotations

import sqlite3

from packages.contracts.schema import StateDelta, ToolCall
from packages.tools.registry import get_tool_implementation


class ERPExecutor:
    """
    Applies gate-approved tool calls to the SQLite ERP and returns the
    actual state delta for fidelity comparison.

    Caller MUST verify gate verdict == ALLOW before calling execute().
    This class does NOT check the gate verdict itself — the pipeline does.
    """

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def execute(self, tool_call: ToolCall) -> StateDelta:
        """
        Execute the tool call and return the actual delta via the registry.
        Raises ValueError for unknown tools.
        """
        impl = get_tool_implementation(tool_call.tool_name)
        if impl is None:
            raise ValueError(
                f"ERPExecutor: no execution handler for tool '{tool_call.tool_name}'"
            )
        return impl.execute(self._conn, tool_call.arguments)
