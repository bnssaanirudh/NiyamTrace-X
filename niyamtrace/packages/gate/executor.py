"""
packages/gate/executor.py — ERP Executor (post-gate actual mutation)

Applies the real write to the SQLite ERP ONLY after the gate returns ALLOW.
Returns an ActualDelta for comparison with the PredictedDelta.

This is the only component that writes to the ERP.
The simulator (simulator.py) is read-only.

Status: IMPLEMENTED (Week 2) — archive_invoices only.
"""

from __future__ import annotations

import sqlite3
from typing import Any

from packages.contracts.schema import RecordDelta, StateDelta, ToolCall


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
        Execute the tool call and return the actual delta.
        Raises ValueError for unknown tools.
        """
        handlers = {
            "archive_invoices": self._execute_archive_invoices,
        }
        fn = handlers.get(tool_call.tool_name)
        if fn is None:
            raise ValueError(
                f"ERPExecutor: no execution handler for tool '{tool_call.tool_name}'"
            )
        return fn(tool_call.arguments)

    # ------------------------------------------------------------------
    # Per-tool execution functions
    # ------------------------------------------------------------------

    def _execute_archive_invoices(self, args: dict[str, Any]) -> StateDelta:
        """
        Set status = 'ARCHIVED' for all OPEN invoices matching the
        vendor_id × month × year filter.

        Returns the actual delta (rows actually changed) for comparison
        with the predicted delta from ShadowSimulator.
        """
        vendor_id: int = args["vendor_id"]
        month: int = args["month"]
        year: int = args["year"]

        # Capture pre-state (same SELECT as the simulator)
        pre_rows = self._conn.execute(
            """
            SELECT invoice_id, status
            FROM vendor_invoices
            WHERE vendor_id = ?
              AND month     = ?
              AND year      = ?
              AND status    = 'OPEN'
            ORDER BY invoice_id
            """,
            (vendor_id, month, year),
        ).fetchall()

        if not pre_rows:
            # Nothing to archive — return empty delta
            return StateDelta(
                affected_record_ids=[],
                record_deltas=[],
                table="vendor_invoices",
                estimated_row_count=0,
            )

        # Execute the write
        self._conn.execute(
            """
            UPDATE vendor_invoices
            SET status = 'ARCHIVED'
            WHERE vendor_id = ?
              AND month     = ?
              AND year      = ?
              AND status    = 'OPEN'
            """,
            (vendor_id, month, year),
        )
        self._conn.commit()

        # Build actual delta from pre-state
        record_deltas = [
            RecordDelta(
                record_id=row["invoice_id"],
                table="vendor_invoices",
                field="status",
                old_value=row["status"],
                new_value="ARCHIVED",
            )
            for row in pre_rows
        ]

        return StateDelta(
            affected_record_ids=[r.record_id for r in record_deltas],
            record_deltas=record_deltas,
            table="vendor_invoices",
            estimated_row_count=len(record_deltas),
        )
