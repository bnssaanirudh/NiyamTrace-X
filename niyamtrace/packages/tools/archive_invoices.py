"""
packages/tools/archive_invoices.py
"""

import sqlite3
from typing import Any

from packages.contracts.schema import RecordDelta, StateDelta
from packages.tools.base import ToolCapability, ToolImplementation
from packages.tools.registry import ToolSchemaValidationError


class ArchiveInvoicesTool(ToolImplementation):
    @property
    def capability(self) -> ToolCapability:
        return ToolCapability(
            name="archive_invoices",
            schema_version="1.0.0",
            risk_class="LOW_WRITE",
            required_scopes=frozenset(["procurement_manager", "finance_admin"]),
            supports_simulation=True,
            supports_idempotency=True,
        )

    @property
    def schema(self) -> dict[str, Any]:
        return {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "title": "archive_invoices",
            "description": (
                "Archive (set status=ARCHIVED) all OPEN invoices for a given vendor "
                "within a specific calendar month and year. "
                "This is a bounded write — it must not match records outside the "
                "specified vendor_id × month × year combination."
            ),
            "type": "object",
            "properties": {
                "tool_name": {"type": "string", "const": "archive_invoices"},
                "arguments": {
                    "type": "object",
                    "properties": {
                        "vendor_id": {"type": "integer", "description": "Numeric vendor identifier.", "minimum": 1},
                        "month": {"type": "integer", "description": "Calendar month (1–12).", "minimum": 1, "maximum": 12},
                        "year": {"type": "integer", "description": "Four-digit calendar year.", "minimum": 2000, "maximum": 2099},
                    },
                    "required": ["vendor_id"],
                    "additionalProperties": False,
                },
            },
            "required": ["tool_name", "arguments"],
            "additionalProperties": False,
        }

    def validate_arguments(self, arguments: dict[str, Any]) -> None:
        if "vendor_id" in arguments:
            if not isinstance(arguments["vendor_id"], int) or arguments["vendor_id"] < 1:
                raise ToolSchemaValidationError("INVALID_ARG:vendor_id:must_be_positive_int")
        if "month" in arguments:
            if not isinstance(arguments["month"], int) or not (1 <= arguments["month"] <= 12):
                raise ToolSchemaValidationError("INVALID_ARG:month:must_be_1_to_12")
        if "year" in arguments:
            if not isinstance(arguments["year"], int) or not (2000 <= arguments["year"] <= 2099):
                raise ToolSchemaValidationError("INVALID_ARG:year:must_be_2000_to_2099")

    def simulate(self, conn: sqlite3.Connection, arguments: dict[str, Any]) -> StateDelta:
        vendor_id: int = arguments.get("vendor_id")
        month: int = arguments.get("month")
        year: int = arguments.get("year")

        clauses = ["vendor_id = ?", "status = 'OPEN'"]
        params: list[Any] = [vendor_id]
        if month is not None:
            clauses.append("month = ?")
            params.append(month)
        if year is not None:
            clauses.append("year = ?")
            params.append(year)

        where = " AND ".join(clauses)
        rows = conn.execute(
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
                record_id=str(row["invoice_id"]),
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

    def execute(self, conn: sqlite3.Connection, arguments: dict[str, Any]) -> StateDelta:
        vendor_id: int = arguments["vendor_id"]
        month: int = arguments.get("month")
        year: int = arguments.get("year")

        clauses = ["vendor_id = ?", "status = 'OPEN'"]
        params: list[Any] = [vendor_id]
        if month is not None:
            clauses.append("month = ?")
            params.append(month)
        if year is not None:
            clauses.append("year = ?")
            params.append(year)

        where = " AND ".join(clauses)
        pre_rows = conn.execute(
            f"SELECT invoice_id, status FROM vendor_invoices WHERE {where} ORDER BY invoice_id",
            params,
        ).fetchall()

        if not pre_rows:
            return StateDelta(
                affected_record_ids=[], record_deltas=[], table="vendor_invoices", estimated_row_count=0
            )

        conn.execute(
            f"UPDATE vendor_invoices SET status = 'ARCHIVED' WHERE {where}", params
        )
        conn.commit()

        record_deltas = [
            RecordDelta(
                record_id=str(row["invoice_id"]),
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
