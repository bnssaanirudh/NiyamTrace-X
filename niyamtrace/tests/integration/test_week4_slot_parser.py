"""
tests/integration/test_week4_slot_parser.py — Week 4 NLP Slot Parser Integration Tests

Verifies that the slot parser is correctly integrated into the pipeline:
  - Different language inputs produce identical ActionContracts (semantic equivalence)
"""

import json
import sqlite3
import pytest

from apps.gateway.pipeline import NiyamPipeline, PipelineRequest
from data.synthetic.erp import init_schema, reset_to_seed
from packages.nlp.parser import SlotParser


@pytest.fixture
def fresh_erp():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    init_schema(conn)
    reset_to_seed(conn)
    yield conn
    conn.close()


@pytest.fixture
def mock_parser():
    return SlotParser(parser_version_suffix="mock-test")


@pytest.fixture
def pipeline(fresh_erp, tmp_path, mock_parser):
    traces_dir = tmp_path / "traces"
    return NiyamPipeline(erp_conn=fresh_erp, traces_dir=traces_dir, parser=mock_parser)


def test_slot_parser_integrated_in_trace(pipeline, tmp_path):
    req = PipelineRequest(
        raw_text="Archive March invoices for vendor 4421",
        actor_id="user-1",
        actor_role="manager"
    )
    result = pipeline.run(req)
    
    # Contract is parsed correctly
    assert result.contract.intent == "invoice.archive"
    assert result.contract.slots.get("VENDOR_ID") == "4421"
    assert "mock-test" in result.contract.parser_version
    
    # Check trace event
    events = result.events
    extracted_event = next(e for e in events if e.event_type == "contract_extracted")
    
    assert "contract" in extracted_event.payload
    assert extracted_event.parser_version == result.contract.parser_version


def test_semantic_equivalence_multilingual(pipeline):
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
        contracts.append(pipeline.run(req).contract)
        
    # The 3 contracts should be functionally identical despite different raw texts
    first = contracts[0]
    for c in contracts[1:]:
        assert c.intent == first.intent
        assert c.slots.get("VENDOR_ID") == first.slots.get("VENDOR_ID")
        assert c.slots.get("MONTH") == first.slots.get("MONTH")
        
        # But their language profiles will differ
        assert c.language_profile != first.language_profile
