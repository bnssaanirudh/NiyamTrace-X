"""
tests/integration/test_simulate_execute_atomicity.py — Simulate-Execute Atomicity & Transaction Integrity

Verifies that:
1. ShadowSimulator is strictly read-only and causes 0 mutations (before/after DB SHA identical).
2. Broker commit verifies fidelity and executes atomically inside a transaction.
3. State mismatch or execution failure triggers full atomic rollback (zero partial mutations).
"""

import hashlib
import json
import sqlite3

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from data.synthetic.erp import SEED_SNAPSHOT_ID, seed_fresh_async
from packages.auth.models import AuthorizationContext, Principal
from packages.contracts.schema import EffectCertificate, ToolCall
from packages.gate.broker import (
    BrokerVerificationError,
    VerifiedExecutionBroker,
    sign_certificate_authority,
)
from packages.gate.policy import DEFAULT_POLICY
from packages.gate.simulator import ShadowSimulator
from packages.storage.postgres import get_async_engine


def compute_table_hash(conn: sqlite3.Connection, table: str = "vendor_invoices") -> str:
    cursor = conn.execute(f"SELECT * FROM {table} ORDER BY invoice_id")
    rows = [tuple(r) for r in cursor.fetchall()]
    return hashlib.sha256(json.dumps(rows, default=str).encode()).hexdigest()


@pytest.fixture
async def real_db(tmp_path):
    db_file = tmp_path / "erp_atomicity.db"
    db_url = f"sqlite+aiosqlite:///{db_file}"
    engine = get_async_engine(db_url)
    await seed_fresh_async(engine)
    yield engine, db_file
    await engine.dispose()


@pytest.fixture
def auth_context():
    principal = Principal(
        subject="user-procurement-01",
        tenant_id="acme",
        roles=frozenset(["procurement_manager"]),
        scopes=frozenset(["procurement.write"]),
    )
    return AuthorizationContext.from_principal(principal)


@pytest.mark.asyncio
async def test_simulation_is_strictly_read_only(real_db):
    engine, db_file = real_db
    conn = sqlite3.connect(str(db_file))
    before_hash = compute_table_hash(conn)

    async with AsyncSession(engine, expire_on_commit=False) as session:
        sim = ShadowSimulator(session)
        tool_call = ToolCall(tool_name="archive_invoices", arguments={"vendor_id": 4421, "month": 3, "year": 2025})
        predicted_delta = await sim.predict(tool_call)

    after_hash = compute_table_hash(conn)
    conn.close()

    assert predicted_delta.estimated_row_count == 3
    assert before_hash == after_hash, "Simulation mutated database state!"


@pytest.mark.asyncio
async def test_execution_atomicity_and_containment_success(real_db, auth_context):
    engine, db_file = real_db
    conn = sqlite3.connect(str(db_file))
    before_hash = compute_table_hash(conn)

    tool_call = ToolCall(tool_name="archive_invoices", arguments={"vendor_id": 4421, "month": 3, "year": 2025})
    args_hash = hashlib.sha256(json.dumps(tool_call.arguments, sort_keys=True).encode()).hexdigest()

    async with AsyncSession(engine, expire_on_commit=False) as session:
        sim = ShadowSimulator(session)
        predicted_delta = await sim.predict(tool_call)

        cert = EffectCertificate(
            trace_id="trace-atomicity-01",
            actor=auth_context.subject,
            tenant_id=auth_context.tenant_id,
            action="invoice.archive",
            target_type="archive_invoices",
            selector={"vendor_id": 4421, "month": 3, "year": 2025},
            canonical_args_hash=args_hash,
            policy_rules_used=[DEFAULT_POLICY.policy_hash],
            policy_version_hash=DEFAULT_POLICY.policy_hash,
            evidence_refs=["evidence-ref-01"],
            predicted_delta={
                "rows_changed": predicted_delta.estimated_row_count,
                "fields_changed": [d.field for d in predicted_delta.record_deltas],
                "record_ids": predicted_delta.affected_record_ids,
                "tenant": auth_context.tenant_id,
            },
            snapshot_id=SEED_SNAPSHOT_ID,
            server_issued=True,
        )
        cert = cert.seal()
        cert = sign_certificate_authority(cert)

        broker = VerifiedExecutionBroker(session, current_snapshot_id=SEED_SNAPSHOT_ID)
        actual_delta = await broker.commit(cert, tool_call, auth_context, current_snapshot_id=SEED_SNAPSHOT_ID)
        await session.commit()

    after_hash = compute_table_hash(conn)
    cursor = conn.execute("SELECT COUNT(*) FROM vendor_invoices WHERE vendor_id=4421 AND month=3 AND year=2025 AND status='ARCHIVED'")
    archived_count = cursor.fetchone()[0]
    conn.close()

    assert actual_delta.estimated_row_count == 3
    assert archived_count == 3
    assert before_hash != after_hash


@pytest.mark.asyncio
async def test_execution_rollback_on_state_mismatch(real_db, auth_context):
    engine, db_file = real_db
    conn = sqlite3.connect(str(db_file))
    before_hash = compute_table_hash(conn)

    tool_call = ToolCall(tool_name="archive_invoices", arguments={"vendor_id": 4421, "month": 3, "year": 2025})
    args_hash = hashlib.sha256(json.dumps(tool_call.arguments, sort_keys=True).encode()).hexdigest()

    async with AsyncSession(engine, expire_on_commit=False) as session:
        # Authorization only permits 1 record, but tool will attempt to archive 3!
        cert = EffectCertificate(
            trace_id="trace-atomicity-mismatch",
            actor=auth_context.subject,
            tenant_id=auth_context.tenant_id,
            action="invoice.archive",
            target_type="archive_invoices",
            selector={"vendor_id": 4421, "month": 3, "year": 2025},
            canonical_args_hash=args_hash,
            policy_rules_used=[DEFAULT_POLICY.policy_hash],
            policy_version_hash=DEFAULT_POLICY.policy_hash,
            evidence_refs=["evidence-ref-01"],
            predicted_delta={
                "rows_changed": 1,
                "fields_changed": ["status"],
                "record_ids": ["INV-4421-2503"],  # Only 1 record authorized!
                "tenant": auth_context.tenant_id,
            },
            snapshot_id=SEED_SNAPSHOT_ID,
            server_issued=True,
        )
        cert = cert.seal()
        cert = sign_certificate_authority(cert)

        broker = VerifiedExecutionBroker(session, current_snapshot_id=SEED_SNAPSHOT_ID)
        with pytest.raises(BrokerVerificationError, match="State mismatch"):
            await broker.commit(cert, tool_call, auth_context, current_snapshot_id=SEED_SNAPSHOT_ID)

    after_hash = compute_table_hash(conn)
    cursor = conn.execute("SELECT COUNT(*) FROM vendor_invoices WHERE status='ARCHIVED'")
    archived_count = cursor.fetchone()[0]
    conn.close()

    # Mismatch MUST cause complete transaction rollback: zero rows mutated!
    assert archived_count == 0
    assert before_hash == after_hash, "Rollback failed — changes leaked into database!"
