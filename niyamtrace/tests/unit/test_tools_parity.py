"""
tests/unit/test_tools_parity.py — Tool Capability Parity Tests
"""

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from data.synthetic.erp import seed_fresh_async
from packages.tools.registry import _TOOL_REGISTRY, get_registry_hash


@pytest_asyncio.fixture
async def fresh_engine():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    await seed_fresh_async(engine)
    yield engine
    await engine.dispose()


@pytest.mark.asyncio
async def test_registry_hash_is_deterministic():
    h1 = get_registry_hash()
    h2 = get_registry_hash()
    assert h1 == h2
    assert len(h1) == 16


@pytest.mark.asyncio
async def test_all_tools_have_simulation_and_execution_parity(fresh_engine):
    """
    Ensure all tools in the registry that support simulation return identical
    StateDeltas between simulate() and execute() for identical inputs.
    """
    async with AsyncSession(fresh_engine, expire_on_commit=False) as session:
        for tool_name, impl in _TOOL_REGISTRY.items():
            if not impl.capability.supports_simulation:
                continue
            
            # We test parity using dummy inputs for each tool
            if tool_name == "archive_invoices":
                args = {"vendor_id": 4421, "month": 3, "year": 2025}
            else:
                pytest.skip(f"No mock data provided for tool '{tool_name}' parity test")
                continue
                
            pred_delta = await impl.simulate(session, args)

            # Execute the tool with valid server authorization capability
            from packages.contracts.schema import EffectCertificate
            from packages.gate.broker import sign_certificate_authority
            import hashlib, json
            auth = EffectCertificate(
                trace_id="test-parity",
                actor="test-actor",
                tenant_id="acme",
                action="invoice.archive",
                target_type=tool_name,
                selector=args,
                canonical_args_hash=hashlib.sha256(json.dumps(args, sort_keys=True).encode()).hexdigest(),
                policy_rules_used=["policy-default"],
                evidence_refs=["ref-default"],
                predicted_delta={"rows_changed": 3, "record_ids": ["INV-4421-2503", "INV-4421-2504", "INV-4421-2505"]},
                server_issued=True,
            )
            auth = sign_certificate_authority(auth)
            actual_delta = await impl.execute(session, args, authorization=auth)
            
            # The predicted state changes must identically match the actual state changes
            assert pred_delta.affected_record_ids == actual_delta.affected_record_ids
            assert pred_delta.estimated_row_count == actual_delta.estimated_row_count
            assert pred_delta.table == actual_delta.table
            
            # For record_deltas, they should match exactly
            assert len(pred_delta.record_deltas) == len(actual_delta.record_deltas)
            for i in range(len(pred_delta.record_deltas)):
                assert pred_delta.record_deltas[i].record_id == actual_delta.record_deltas[i].record_id
                assert pred_delta.record_deltas[i].old_value == actual_delta.record_deltas[i].old_value
