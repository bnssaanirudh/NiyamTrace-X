"""tests/unit/test_simulator.py — Unit tests for ShadowSimulator and ERPExecutor."""

from __future__ import annotations

import pytest
import pytest_asyncio


async def async_query_invoices(engine, **kwargs):
    from sqlalchemy import text
    async with engine.begin() as conn:
        conditions = []
        params = {}
        for k, v in kwargs.items():
            conditions.append(f"{k} = :{k}")
            params[k] = v
        
        query = "SELECT * FROM vendor_invoices"
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
            
        result = await conn.execute(text(query), params)
        return [dict(row._mapping) for row in result.all()]
from packages.contracts.schema import ToolCall
from packages.gate.executor import ERPExecutor
from packages.gate.simulator import ShadowSimulator

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def erp_conn():
    from sqlalchemy.ext.asyncio import create_async_engine

    from data.synthetic.erp import seed_fresh_async
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    await seed_fresh_async(engine)
    yield engine
    await engine.dispose()


def _archive_tool(vendor_id=4421, month=3, year=2025) -> ToolCall:
    return ToolCall(
        tool_name="archive_invoices",
        arguments={"vendor_id": vendor_id, "month": month, "year": year},
    )


# ---------------------------------------------------------------------------
# ShadowSimulator tests
# ---------------------------------------------------------------------------


class TestShadowSimulator:
    pytestmark = pytest.mark.asyncio
    async def test_predicts_correct_records_for_canonical_scenario(self, erp_conn):
        sim = ShadowSimulator(__import__("sqlalchemy.ext.asyncio").ext.asyncio.AsyncSession(erp_conn, expire_on_commit=False))
        delta = await sim.predict(_archive_tool(vendor_id=4421, month=3, year=2025))

        # Seed has exactly 3 OPEN invoices for vendor 4421, month 3, year 2025
        assert delta.estimated_row_count == 3
        expected_ids = {"INV-4421-2503", "INV-4421-2504", "INV-4421-2505"}
        assert delta.record_id_set() == expected_ids

    async def test_all_predicted_deltas_are_status_changes(self, erp_conn):
        sim = ShadowSimulator(__import__("sqlalchemy.ext.asyncio").ext.asyncio.AsyncSession(erp_conn, expire_on_commit=False))
        delta = await sim.predict(_archive_tool())
        for rd in delta.record_deltas:
            assert rd.field == "status"
            assert rd.old_value == "OPEN"
            assert rd.new_value == "ARCHIVED"

    async def test_simulator_does_not_mutate_erp(self, erp_conn):
        sim = ShadowSimulator(__import__("sqlalchemy.ext.asyncio").ext.asyncio.AsyncSession(erp_conn, expire_on_commit=False))
        await sim.predict(_archive_tool())
        # ERP should still have 3 OPEN rows for vendor 4421 March 2025
        rows = await async_query_invoices(erp_conn, vendor_id=4421, month=3, year=2025, status="OPEN")
        assert len(rows) == 3

    async def test_empty_result_for_nonexistent_vendor(self, erp_conn):
        sim = ShadowSimulator(__import__("sqlalchemy.ext.asyncio").ext.asyncio.AsyncSession(erp_conn, expire_on_commit=False))
        delta = await sim.predict(_archive_tool(vendor_id=9999, month=3, year=2025))
        assert delta.estimated_row_count == 0
        assert delta.affected_record_ids == []

    async def test_empty_result_for_wrong_month(self, erp_conn):
        sim = ShadowSimulator(__import__("sqlalchemy.ext.asyncio").ext.asyncio.AsyncSession(erp_conn, expire_on_commit=False))
        delta = await sim.predict(_archive_tool(vendor_id=4421, month=6, year=2025))
        assert delta.estimated_row_count == 0

    async def test_unknown_tool_raises_error(self, erp_conn):
        sim = ShadowSimulator(__import__("sqlalchemy.ext.asyncio").ext.asyncio.AsyncSession(erp_conn, expire_on_commit=False))
        unknown = ToolCall(
            tool_name="delete_everything",
            arguments={"vendor_id": 4421},
        )
        with pytest.raises(ValueError, match="no simulation handler"):
            await sim.predict(unknown)

    async def test_already_closed_invoices_not_included(self, erp_conn):
        """Simulator must only predict OPEN rows — already-CLOSED rows are excluded."""
        sim = ShadowSimulator(__import__("sqlalchemy.ext.asyncio").ext.asyncio.AsyncSession(erp_conn, expire_on_commit=False))
        # vendor 8802, month 5 has a CLOSED invoice in seed data
        delta = await sim.predict(_archive_tool(vendor_id=8802, month=5, year=2025))
        assert delta.estimated_row_count == 0  # CLOSED row excluded


# ---------------------------------------------------------------------------
# ERPExecutor tests
# ---------------------------------------------------------------------------


class TestERPExecutor:
    pytestmark = pytest.mark.asyncio
    async def test_execute_archives_correct_rows(self, erp_conn):
        executor = ERPExecutor(__import__("sqlalchemy.ext.asyncio").ext.asyncio.AsyncSession(erp_conn, expire_on_commit=False))
        actual = await executor.execute(_archive_tool(vendor_id=4421, month=3, year=2025))

        assert actual.estimated_row_count == 3
        expected_ids = {"INV-4421-2503", "INV-4421-2504", "INV-4421-2505"}
        assert actual.record_id_set() == expected_ids

    async def test_executed_rows_are_archived_in_db(self, erp_conn):
        executor = ERPExecutor(__import__("sqlalchemy.ext.asyncio").ext.asyncio.AsyncSession(erp_conn, expire_on_commit=False))
        await executor.execute(_archive_tool(vendor_id=4421, month=3, year=2025))

        # Now query the DB — no OPEN rows should remain for vendor 4421, March 2025
        open_rows = await async_query_invoices(erp_conn, vendor_id=4421, month=3, year=2025, status="OPEN")
        archived_rows = await async_query_invoices(erp_conn, vendor_id=4421, month=3, year=2025, status="ARCHIVED")
        assert len(open_rows) == 0
        assert len(archived_rows) == 3

    async def test_execute_returns_empty_delta_when_nothing_to_archive(self, erp_conn):
        executor = ERPExecutor(__import__("sqlalchemy.ext.asyncio").ext.asyncio.AsyncSession(erp_conn, expire_on_commit=False))
        actual = await executor.execute(_archive_tool(vendor_id=9999, month=1, year=2025))
        assert actual.estimated_row_count == 0

    async def test_simulator_fidelity_is_perfect_for_canonical_scenario(self, erp_conn):
        """PredictedDelta must exactly match ActualDelta for the seed scenario."""
        sim = ShadowSimulator(__import__("sqlalchemy.ext.asyncio").ext.asyncio.AsyncSession(erp_conn, expire_on_commit=False))
        exe = ERPExecutor(__import__("sqlalchemy.ext.asyncio").ext.asyncio.AsyncSession(erp_conn, expire_on_commit=False))

        tool = _archive_tool()
        predicted = await sim.predict(tool)
        actual = await exe.execute(tool)

        assert predicted.record_id_set() == actual.record_id_set()
        assert predicted.estimated_row_count == actual.estimated_row_count

    async def test_other_vendors_not_affected_after_execution(self, erp_conn):
        """Executing archive for vendor 4421 must not touch vendor 8802 or 3301."""
        executor = ERPExecutor(__import__("sqlalchemy.ext.asyncio").ext.asyncio.AsyncSession(erp_conn, expire_on_commit=False))
        await executor.execute(_archive_tool(vendor_id=4421, month=3, year=2025))

        # vendor 8802 and 3301 March 2025 rows should still be OPEN
        rows_8802 = await async_query_invoices(erp_conn, vendor_id=8802, month=3, year=2025)
        rows_3301 = await async_query_invoices(erp_conn, vendor_id=3301, month=3, year=2025)
        assert all(r["status"] == "OPEN" for r in rows_8802)
        assert all(r["status"] == "OPEN" for r in rows_3301)
