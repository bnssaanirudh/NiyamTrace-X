"""
packages/gate/executor.py — ERP Executor (post-gate actual mutation)

Applies the real write to the SQLite ERP ONLY after the gate returns ALLOW.
Returns an ActualDelta for comparison with the PredictedDelta.

This is the only component that writes to the ERP.
The simulator (simulator.py) is read-only.

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
            "block_user_access": self._execute_block_user_access,
            "update_credit_limit": self._execute_update_credit_limit,
            "suspend_vendor": self._execute_suspend_vendor,
        }
        fn = handlers.get(tool_call.tool_name)
        if fn is None:
            raise ValueError(
                f"ERPExecutor: no execution handler for tool '{tool_call.tool_name}'"
            )
        return fn(tool_call.arguments)

    # ------------------------------------------------------------------
    # archive_invoices
    # ------------------------------------------------------------------

    def _execute_archive_invoices(self, args: dict[str, Any]) -> StateDelta:
        """
        Set status = 'ARCHIVED' for all OPEN invoices matching the
        vendor_id × month × year filter.
        """
        vendor_id: int = args["vendor_id"]
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
        pre_rows = self._conn.execute(
            f"SELECT invoice_id, status FROM vendor_invoices WHERE {where} ORDER BY invoice_id",
            params,
        ).fetchall()

        if not pre_rows:
            return StateDelta(
                affected_record_ids=[], record_deltas=[], table="vendor_invoices", estimated_row_count=0
            )

        self._conn.execute(
            f"UPDATE vendor_invoices SET status = 'ARCHIVED' WHERE {where}", params
        )
        self._conn.commit()

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

    # ------------------------------------------------------------------
    # block_user_access
    # ------------------------------------------------------------------

    def _execute_block_user_access(self, args: dict[str, Any]) -> StateDelta:
        """
        Set user_access.status = BLOCKED and record blocked_until date.
        """
        user_id: str = args["user_id"]
        duration_days: int = args["duration_days"]
        blocked_until = (date.today() + timedelta(days=duration_days)).isoformat()

        pre_rows = self._conn.execute(
            "SELECT user_id, status, blocked_until FROM user_access WHERE user_id = ?",
            (user_id,),
        ).fetchall()

        if not pre_rows:
            return StateDelta(
                affected_record_ids=[], record_deltas=[], table="user_access", estimated_row_count=0
            )

        self._conn.execute(
            "UPDATE user_access SET status = 'BLOCKED', blocked_until = ? WHERE user_id = ?",
            (blocked_until, user_id),
        )
        self._conn.commit()

        record_deltas = [
            RecordDelta(record_id=user_id, table="user_access", field="status",
                        old_value=pre_rows[0]["status"], new_value="BLOCKED"),
            RecordDelta(record_id=user_id, table="user_access", field="blocked_until",
                        old_value=pre_rows[0]["blocked_until"], new_value=blocked_until),
        ]
        return StateDelta(
            affected_record_ids=[user_id],
            record_deltas=record_deltas,
            table="user_access",
            estimated_row_count=1,
        )

    # ------------------------------------------------------------------
    # update_credit_limit
    # ------------------------------------------------------------------

    def _execute_update_credit_limit(self, args: dict[str, Any]) -> StateDelta:
        """
        Update vendor_credit_limits.credit_limit_inr for the given vendor.
        """
        vendor_id: int = args["vendor_id"]
        new_limit: float = args["new_limit_inr"]
        updated_at = date.today().isoformat()

        pre_rows = self._conn.execute(
            "SELECT vendor_id, credit_limit_inr FROM vendor_credit_limits WHERE vendor_id = ?",
            (vendor_id,),
        ).fetchall()

        if not pre_rows:
            return StateDelta(
                affected_record_ids=[], record_deltas=[], table="vendor_credit_limits", estimated_row_count=0
            )

        self._conn.execute(
            "UPDATE vendor_credit_limits SET credit_limit_inr = ?, updated_at = ? WHERE vendor_id = ?",
            (new_limit, updated_at, vendor_id),
        )
        self._conn.commit()

        record_deltas = [
            RecordDelta(
                record_id=str(vendor_id),
                table="vendor_credit_limits",
                field="credit_limit_inr",
                old_value=str(pre_rows[0]["credit_limit_inr"]),
                new_value=str(new_limit),
            )
        ]
        return StateDelta(
            affected_record_ids=[str(vendor_id)],
            record_deltas=record_deltas,
            table="vendor_credit_limits",
            estimated_row_count=1,
        )

    # ------------------------------------------------------------------
    # suspend_vendor
    # ------------------------------------------------------------------

    def _execute_suspend_vendor(self, args: dict[str, Any]) -> StateDelta:
        """
        Suspend a vendor: set all OPEN invoices for the vendor to SUSPENDED.
        A justification is required (logged to trace; not stored in ERP).
        """
        vendor_id: int = args["vendor_id"]

        pre_rows = self._conn.execute(
            """
            SELECT invoice_id, status
            FROM vendor_invoices
            WHERE vendor_id = ? AND status = 'OPEN'
            ORDER BY invoice_id
            """,
            (vendor_id,),
        ).fetchall()

        if not pre_rows:
            return StateDelta(
                affected_record_ids=[], record_deltas=[], table="vendor_invoices", estimated_row_count=0
            )

        self._conn.execute(
            "UPDATE vendor_invoices SET status = 'SUSPENDED' WHERE vendor_id = ? AND status = 'OPEN'",
            (vendor_id,),
        )
        self._conn.commit()

        record_deltas = [
            RecordDelta(
                record_id=row["invoice_id"],
                table="vendor_invoices",
                field="status",
                old_value=row["status"],
                new_value="SUSPENDED",
            )
            for row in pre_rows
        ]
        return StateDelta(
            affected_record_ids=[r.record_id for r in record_deltas],
            record_deltas=record_deltas,
            table="vendor_invoices",
            estimated_row_count=len(record_deltas),
        )
