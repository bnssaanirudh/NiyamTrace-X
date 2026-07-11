"""
packages/gate/simulator.py — NiyamGate Shadow Simulator (SELECT-before-write)

The simulator predicts which ERP records would be mutated by a proposed tool
call WITHOUT actually mutating anything. It runs a SELECT query that mirrors
the WHERE clause the real executor would use, then packages the result as a
StateDelta.

The gate compares predicted_delta ⊆ allowed_effects(contract, policy) before
permitting the actual write. See Section 6 of the NiyamTrace brief.

Design:
- Read-only: never writes to the ERP connection passed in.
- Tool-specific: each tool has a dedicated _simulate_<tool> function.
- Returns StateDelta with the affected record IDs, field-level deltas, and
  an estimated row count.

Status: IMPLEMENTED (Week 2) — archive_invoices simulation only.
"""

from __future__ import annotations

import sqlite3
import time
from typing import Any

from packages.contracts.schema import RecordDelta, StateDelta, ToolCall


# ---------------------------------------------------------------------------
# Public simulator entry point
# ---------------------------------------------------------------------------


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
        Dispatch to the appropriate per-tool simulation function.
        Returns a StateDelta describing what would change.
        Raises ValueError for unknown tools.
        """
        handlers = {
            "archive_invoices": self._simulate_archive_invoices,
        }
        fn = handlers.get(tool_call.tool_name)
        if fn is None:
            raise ValueError(
                f"ShadowSimulator: no simulation handler for tool '{tool_call.tool_name}'"
            )
        return fn(tool_call.arguments)

    # ------------------------------------------------------------------
    # Per-tool simulation functions
    # ------------------------------------------------------------------

    def _simulate_archive_invoices(self, args: dict[str, Any]) -> StateDelta:
        """
        Predict which OPEN invoices for vendor_id, month, year would be
        archived (status → ARCHIVED). Read-only SELECT — no writes.

        The SELECT mirrors the WHERE clause the executor will use exactly,
        so simulator fidelity is guaranteed for the seed data.
        """
        vendor_id: int = args.get("vendor_id")
        month: int = args.get("month")
        year: int = args.get("year")

        clauses = ["vendor_id = ?", "status = 'OPEN'"]
        params = [vendor_id]
        if month is not None:
            clauses.append("month = ?")
            params.append(month)
        if year is not None:
            clauses.append("year = ?")
            params.append(year)
            
        where = " AND ".join(clauses)

        rows = self._conn.execute(
            f"""
            SELECT invoice_id, status
            FROM vendor_invoices
            WHERE {where}
            ORDER BY invoice_id
            """,
            params,
        ).fetchall()

        record_deltas = [
            RecordDelta(
                record_id=row["invoice_id"],
                table="vendor_invoices",
                field="status",
                old_value=row["status"],
                new_value="ARCHIVED",
            )
            for row in rows
        ]

        return StateDelta(
            affected_record_ids=[r.record_id for r in record_deltas],
            record_deltas=record_deltas,
            table="vendor_invoices",
            estimated_row_count=len(record_deltas),
        )
