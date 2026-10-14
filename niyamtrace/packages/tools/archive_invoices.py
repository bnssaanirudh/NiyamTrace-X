"""
packages/tools/archive_invoices.py
"""

from typing import Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from packages.contracts.schema import RecordDelta, StateDelta
from packages.storage.models import VendorInvoice
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
        if "vendor_id" in arguments and (
            not isinstance(arguments["vendor_id"], int) or arguments["vendor_id"] < 1
        ):
            raise ToolSchemaValidationError("INVALID_ARG:vendor_id:must_be_positive_int")
        if "month" in arguments and (
            not isinstance(arguments["month"], int) or not (1 <= arguments["month"] <= 12)
        ):
            raise ToolSchemaValidationError("INVALID_ARG:month:must_be_1_to_12")
        if "year" in arguments and (
            not isinstance(arguments["year"], int) or not (2000 <= arguments["year"] <= 2099)
        ):
            raise ToolSchemaValidationError("INVALID_ARG:year:must_be_2000_to_2099")

    async def simulate(self, session: AsyncSession, arguments: dict[str, Any]) -> StateDelta:
        vendor_id: int = arguments.get("vendor_id")
        month: int = arguments.get("month")
        year: int = arguments.get("year")

        stmt = select(VendorInvoice.invoice_id, VendorInvoice.status).where(
            VendorInvoice.vendor_id == vendor_id,
            VendorInvoice.status == 'OPEN'
        )
        if month is not None:
            stmt = stmt.where(VendorInvoice.month == month)
        if year is not None:
            stmt = stmt.where(VendorInvoice.year == year)
        stmt = stmt.order_by(VendorInvoice.invoice_id)

        result = await session.execute(stmt)
        rows = result.all()

        record_deltas = [
            RecordDelta(
                record_id=str(row.invoice_id),
                table="vendor_invoices",
                field="status",
                old_value=row.status,
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

    async def execute(
        self,
        session: AsyncSession,
        arguments: dict[str, Any],
        authorization: Any | None = None,
        auth_context: Any | None = None,
        policy: Any | None = None,
        current_snapshot_id: str | None = None,
    ) -> StateDelta:
        from packages.gate.broker import verify_tool_authorization_binding
        verify_tool_authorization_binding(
            authorization=authorization,
            tool_name="archive_invoices",
            arguments=arguments,
            auth_context=auth_context,
            policy=policy,
            current_snapshot_id=current_snapshot_id,
        )

        vendor_id: int = arguments["vendor_id"]
        month: int = arguments.get("month")
        year: int = arguments.get("year")

        stmt = select(VendorInvoice.invoice_id, VendorInvoice.status).where(
            VendorInvoice.vendor_id == vendor_id,
            VendorInvoice.status == 'OPEN'
        )
        if month is not None:
            stmt = stmt.where(VendorInvoice.month == month)
        if year is not None:
            stmt = stmt.where(VendorInvoice.year == year)
        stmt = stmt.order_by(VendorInvoice.invoice_id)

        result = await session.execute(stmt)
        pre_rows = result.all()

        if not pre_rows:
            return StateDelta(
                affected_record_ids=[], record_deltas=[], table="vendor_invoices", estimated_row_count=0
            )

        upd_stmt = update(VendorInvoice).where(
            VendorInvoice.vendor_id == vendor_id,
            VendorInvoice.status == 'OPEN'
        )
        if month is not None:
            upd_stmt = upd_stmt.where(VendorInvoice.month == month)
        if year is not None:
            upd_stmt = upd_stmt.where(VendorInvoice.year == year)
        
        upd_stmt = upd_stmt.values(status='ARCHIVED')
        await session.execute(upd_stmt)
        # commit is managed by pipeline SessionManager

        record_deltas = [
            RecordDelta(
                record_id=str(row.invoice_id),
                table="vendor_invoices",
                field="status",
                old_value=row.status,
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
