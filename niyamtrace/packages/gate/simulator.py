"""
packages/gate/simulator.py — NiyamGate Shadow Simulator (SELECT-before-write)

Forwards simulation execution to the registered tool implementations (Phase 6).
"""

from __future__ import annotations

import sqlite3

from packages.contracts.schema import StateDelta, ToolCall
from packages.tools.registry import get_tool_implementation


class ShadowSimulator:
    """
    Predicts the state delta for a proposed tool call without executing it.

    Usage:
        sim = ShadowSimulator(conn)
        delta = sim.predict(tool_call)
    """

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def predict(self, tool_call: ToolCall) -> StateDelta:
        """
        Dispatch to the appropriate per-tool simulation function via the registry.
        Returns a StateDelta describing what would change.
        Raises ValueError for unknown tools.
        """
        impl = get_tool_implementation(tool_call.tool_name)
        if impl is None:
            raise ValueError(
                f"ShadowSimulator: no simulation handler for tool '{tool_call.tool_name}'"
            )
        
        if not impl.capability.supports_simulation:
            raise ValueError(
                f"ShadowSimulator: tool '{tool_call.tool_name}' does not support simulation"
            )

        return impl.simulate(self._conn, tool_call.arguments)
