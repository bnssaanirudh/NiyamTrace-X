"""
tests/unit/test_tools_parity.py — Tool Capability Parity Tests
"""

import pytest
import sqlite3

from packages.tools.registry import _TOOL_REGISTRY, get_registry_hash
from packages.contracts.schema import ToolCall

@pytest.fixture
def fresh_erp():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute(
        """
        CREATE TABLE vendor_invoices (
            invoice_id INTEGER PRIMARY KEY,
            vendor_id INTEGER,
            month INTEGER,
            year INTEGER,
            status TEXT
        )
        """
    )
    conn.execute("INSERT INTO vendor_invoices VALUES (101, 4421, 3, 2025, 'OPEN')")
    conn.execute("INSERT INTO vendor_invoices VALUES (102, 4421, 3, 2025, 'OPEN')")
    conn.execute("INSERT INTO vendor_invoices VALUES (103, 4421, 4, 2025, 'OPEN')")
    conn.execute("INSERT INTO vendor_invoices VALUES (104, 9999, 3, 2025, 'OPEN')")
    conn.execute("INSERT INTO vendor_invoices VALUES (105, 4421, 3, 2025, 'ARCHIVED')")
    conn.commit()
    return conn


def test_registry_hash_is_deterministic():
    h1 = get_registry_hash()
    h2 = get_registry_hash()
    assert h1 == h2
    assert len(h1) == 16


def test_all_tools_have_simulation_and_execution_parity(fresh_erp):
    """
    Ensure all tools in the registry that support simulation return identical
    StateDeltas between simulate() and execute() for identical inputs.
    """
    for tool_name, impl in _TOOL_REGISTRY.items():
        if not impl.capability.supports_simulation:
            continue
        
        # We test parity using dummy inputs for each tool
        if tool_name == "archive_invoices":
            args = {"vendor_id": 4421, "month": 3, "year": 2025}
        else:
            pytest.skip(f"No mock data provided for tool '{tool_name}' parity test")
            continue
            
        pred_delta = impl.simulate(fresh_erp, args)
        
        # Execute the tool
        actual_delta = impl.execute(fresh_erp, args)
        
        # The predicted state changes must identically match the actual state changes
        assert pred_delta.affected_record_ids == actual_delta.affected_record_ids
        assert pred_delta.estimated_row_count == actual_delta.estimated_row_count
        assert pred_delta.table == actual_delta.table
        
        # For record_deltas, they should match exactly
        assert len(pred_delta.record_deltas) == len(actual_delta.record_deltas)
        for i in range(len(pred_delta.record_deltas)):
            assert pred_delta.record_deltas[i].record_id == actual_delta.record_deltas[i].record_id
            assert pred_delta.record_deltas[i].old_value == actual_delta.record_deltas[i].old_value
            assert pred_delta.record_deltas[i].new_value == actual_delta.record_deltas[i].new_value
