"""
tests/integration/test_week4_slot_parser.py — Week 4 NLP Slot Parser Integration Tests

Verifies that the slot parser is correctly integrated into the pipeline:
  - Different language inputs produce identical ActionContracts (semantic equivalence)
"""

import pytest
import pytest_asyncio

from apps.gateway.pipeline import NiyamPipeline, PipelineRequest
from packages.nlp.compiler import NiyamCompiler


@pytest_asyncio.fixture
async def fresh_engine():
    from sqlalchemy.ext.asyncio import create_async_engine

    from data.synthetic.erp import seed_fresh_async
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    await seed_fresh_async(engine)
    yield engine
    await engine.dispose()


@pytest.fixture
def mock_compiler():
    return NiyamCompiler(parser_version_suffix="mock-test")


@pytest.fixture
def pipeline(fresh_engine, tmp_path, mock_compiler):
    traces_dir = tmp_path / "traces"
    return NiyamPipeline(engine=fresh_engine, traces_dir=traces_dir, compiler=mock_compiler)


@pytest.mark.asyncio
async def test_slot_parser_integrated_in_trace(pipeline, tmp_path):
    req = PipelineRequest(
        raw_text="Archive March invoices for vendor 4421",
        actor_id="user-1",
        actor_role="manager"
    )
    result = await pipeline.run(req)
    
    # Contract is parsed correctly
    assert result.contract.intent == "invoice.archive"
    assert str(result.contract.slots.get("VENDOR_ID")) == "4421"
    assert "mock-test" in result.contract.parser_version
    
    # Check trace event
    events = result.events
    extracted_event = next(e for e in events if e.event_type == "contract_extracted")
    
    assert "contract" in extracted_event.payload
    assert extracted_event.parser_version == result.contract.parser_version


@pytest.mark.asyncio
async def test_semantic_equivalence_multilingual(pipeline):
    """
    All language variants of the same intent should resolve to exactly the
    same functional fields in the ActionContract because they hit the same
    XLM-R wrapper logic.
    """
    variants = [
        "Archive March invoices for vendor 4421",
        "Vendor 4421 ke March invoices archive karo",
        "వెండర్ 4421 మార్చి ఇన్వాయిస్లు ఆర్కైవ్ చేయండి"
    ]
    
    contracts = []
    for var in variants:
        req = PipelineRequest(raw_text=var, actor_id="a", actor_role="r")
        contracts.append((await pipeline.run(req)).contract)
        
    # The 3 contracts should be functionally identical despite different raw texts
    first = contracts[0]
    for c in contracts[1:]:
        assert c.intent == first.intent
        assert c.slots.get("VENDOR_ID") == first.slots.get("VENDOR_ID")
        assert c.slots.get("MONTH") == first.slots.get("MONTH")
        
        # But their language profiles will differ
        assert c.language_profile != first.language_profile
