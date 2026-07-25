"""
packages/gate/simulator.py — NiyamGate Shadow Simulator (SELECT-before-write)

The simulator predicts which ERP records would be mutated by a proposed tool
call WITHOUT actually mutating anything. It runs a SELECT query that mirrors
the WHERE clause the real executor would use, then packages the result as a
StateDelta.

Tools supported:
  - archive_invoices    (Week 2)
  - block_user_access   (Week 9)
  - update_credit_limit (Week 9)
  - suspend_vendor      (Week 9)

Status: IMPLEMENTED (Week 9) — 4 tools.
"""

from __future__ import annotations

import sqlite3
from datetime import date, timedelta
from typing import Any

from packages.contracts.schema import RecordDelta, StateDelta, ToolCall


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
            "block_user_access": self._simulate_block_user_access,
            "update_credit_limit": self._simulate_update_credit_limit,
            "suspend_vendor": self._simulate_suspend_vendor,
        }
        fn = handlers.get(tool_call.tool_name)
        if fn is None:
            raise ValueError(
                f"ShadowSimulator: no simulation handler for tool '{tool_call.tool_name}'"
            )
        return fn(tool_call.arguments)

    # ------------------------------------------------------------------
    # archive_invoices
    # ------------------------------------------------------------------

    def _simulate_archive_invoices(self, args: dict[str, Any]) -> StateDelta:
        """
        Predict which OPEN invoices for vendor_id, month, year would be
        archived (status → ARCHIVED). Read-only SELECT — no writes.
        """
        vendor_id: int = args.get("vendor_id")
        month: int = args.get("month")
        year: int = args.get("year")

        clauses = ["vendor_id = ?", "status = 'OPEN'"]
        params: list[Any] = [vendor_id]
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

    # ------------------------------------------------------------------
    # block_user_access
    # ------------------------------------------------------------------

    def _simulate_block_user_access(self, args: dict[str, Any]) -> StateDelta:
        """
        Predict the effect of blocking a user: status → BLOCKED,
        blocked_until → today + duration_days.
        Read-only SELECT — no writes.
        """
        user_id: str = args.get("user_id", "")
        duration_days: int = args.get("duration_days", 1)

        rows = self._conn.execute(
            "SELECT user_id, status, blocked_until FROM user_access WHERE user_id = ?",
            (user_id,),
        ).fetchall()

        blocked_until = (date.today() + timedelta(days=duration_days)).isoformat()

        record_deltas = []
        for row in rows:
            record_deltas.append(
                RecordDelta(
                    record_id=row["user_id"],
                    table="user_access",
                    field="status",
                    old_value=row["status"],
                    new_value="BLOCKED",
                )
            )
            record_deltas.append(
                RecordDelta(
                    record_id=row["user_id"],
                    table="user_access",
                    field="blocked_until",
                    old_value=row["blocked_until"],
                    new_value=blocked_until,
                )
            )

        return StateDelta(
            affected_record_ids=[user_id] if rows else [],
            record_deltas=record_deltas,
            table="user_access",
            estimated_row_count=len(rows),
        )

    # ------------------------------------------------------------------
    # update_credit_limit
    # ------------------------------------------------------------------

    def _simulate_update_credit_limit(self, args: dict[str, Any]) -> StateDelta:
        """
        Predict the effect of updating a vendor's credit limit.
        Read-only SELECT — no writes.
        """
        vendor_id: int = args.get("vendor_id")
        new_limit: float = args.get("new_limit_inr", 0.0)

        rows = self._conn.execute(
            "SELECT vendor_id, credit_limit_inr FROM vendor_credit_limits WHERE vendor_id = ?",
            (vendor_id,),
        ).fetchall()

        record_deltas = [
            RecordDelta(
                record_id=str(row["vendor_id"]),
                table="vendor_credit_limits",
                field="credit_limit_inr",
                old_value=str(row["credit_limit_inr"]),
                new_value=str(new_limit),
            )
            for row in rows
        ]

        return StateDelta(
            affected_record_ids=[str(vendor_id)] if rows else [],
            record_deltas=record_deltas,
            table="vendor_credit_limits",
            estimated_row_count=len(rows),
        )

    # ------------------------------------------------------------------
    # suspend_vendor
    # ------------------------------------------------------------------

    def _simulate_suspend_vendor(self, args: dict[str, Any]) -> StateDelta:
        """
        Predict the effect of suspending a vendor: all OPEN invoices for
        the vendor are flagged as SUSPENDED (simulated only — actual ERP
        would set a vendor-level status flag).
        Read-only SELECT — no writes.
        """
        vendor_id: int = args.get("vendor_id")

        rows = self._conn.execute(
            """
            SELECT invoice_id, status
            FROM vendor_invoices
            WHERE vendor_id = ? AND status = 'OPEN'
            ORDER BY invoice_id
            """,
            (vendor_id,),
        ).fetchall()

        record_deltas = [
            RecordDelta(
                record_id=row["invoice_id"],
                table="vendor_invoices",
                field="status",
                old_value=row["status"],
                new_value="SUSPENDED",
            )
            for row in rows
        ]

        return StateDelta(
            affected_record_ids=[r.record_id for r in record_deltas],
            record_deltas=record_deltas,
            table="vendor_invoices",
            estimated_row_count=len(record_deltas),
        )
