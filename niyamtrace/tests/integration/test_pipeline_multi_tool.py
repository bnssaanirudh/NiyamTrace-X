import pytest
from unittest.mock import patch
from datetime import datetime, UTC

from apps.gateway.pipeline import run_pipeline
from packages.nlp.compiler import CandidateIntent, CandidateSlots

@pytest.mark.asyncio
async def test_multi_tool_failure_rollback():
    """
    Test that if a contract translates into multiple tool calls,
    and one of them is blocked by the gate, the entire transaction is blocked
    and NO tools are executed.
    """
    
    # We will patch NiyamCompiler._extract_candidate to return a multi-intent
    # We want: archive invoices (allowed for procurement_manager) + block user (denied for procurement_manager)
    
    mock_candidate = CandidateIntent(
        intent="invoice.archive+access.block",
        slots=CandidateSlots(
            VENDOR_ID="4421",
            MONTH=3,
            YEAR=2024,
            USER_ID="user-999" # For access.block
        ),
        confidence=0.99
    )
    
    with patch("packages.nlp.compiler.NiyamCompiler._extract_candidate", return_value=mock_candidate):
        events = await run_pipeline(
            raw_text="Archive invoices for vendor 4421 and block user 999",
            actor_id="user-001",
            actor_role="procurement_manager",
        )
        
        # Verify event sequence
        gate_decision = next((e for e in events if e["event_type"] == "gate_decision"), None)
        assert gate_decision is not None, "Gate decision event not found"
        
        # The entire request should be blocked because procurement_manager cannot block users
        assert gate_decision["decision"] == "BLOCK", f"Expected BLOCK, got {gate_decision['decision']}"
        
        # Verify tool_executed was skipped
        tool_executed = next((e for e in events if e["event_type"] == "tool_executed"), None)
        assert tool_executed is not None, "Tool executed event missing"
        assert tool_executed.get("decision") in ("SKIPPED_GATE_BLOCK", "SKIPPED_EARLY_EXIT"), "Tool should not have been executed"
