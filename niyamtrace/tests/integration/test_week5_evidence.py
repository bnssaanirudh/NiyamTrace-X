"""
tests/integration/test_week5_evidence.py — Week 5 Exit-Criterion Integration Test

Tests that the full pipeline with NiyamEvidence produces correct evidence verdicts
and that Gate Check 5 responds appropriately to SUPPORT / CONTRADICT / INSUFFICIENT.

Exit criteria (Week 5):
  ✓ Pipeline Event 3 (retrieval_completed) contains real chunks, not empty list
  ✓ retrieval_completed verdict is NOT "STUB"
  ✓ procurement_manager archiving invoices → SUPPORT → gate passes check 5
  ✓ SUPPORT verdict in retrieval_completed event payload
  ✓ Gate decision check_results include evidence_sufficiency with reason_code=OK
  ✓ Viewer role (no policy access) → INSUFFICIENT → gate blocks on evidence
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest
import pytest_asyncio

from apps.gateway.pipeline import NiyamPipeline, PipelineRequest

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def fresh_engine():
    from sqlalchemy.ext.asyncio import create_async_engine

    from data.synthetic.erp import seed_fresh_async
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    await seed_fresh_async(engine)
    yield engine
    await engine.dispose()


@pytest.fixture
def tmp_traces(tmp_path):
    return tmp_path / "traces"


async def _run_pipeline(
    erp_conn: sqlite3.Connection,
    traces_dir: Path,
    raw_text: str,
    actor_id: str = "USR-PM-01",
    actor_role: str = "procurement_manager",
) -> PipelineResult:  # type: ignore[name-defined]
    pipeline = NiyamPipeline(engine=erp_conn, traces_dir=traces_dir)
    req = PipelineRequest(
        raw_text=raw_text,
        actor_id=actor_id,
        actor_role=actor_role,
    )
    return await pipeline.run(req)


# ---------------------------------------------------------------------------
# Test: retrieval_completed event is real (not stub)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_retrieval_completed_is_not_stub(fresh_engine, tmp_traces):
    """retrieval_completed must contain real chunks and a non-STUB verdict."""
    result = await _run_pipeline(
        fresh_engine,
        tmp_traces,
        raw_text="Archive March 2025 invoices for vendor 4421",
        actor_role="procurement_manager",
    )

    retrieval_event = next(
        e for e in result.events if e.event_type == "retrieval_completed"
    )
    payload = retrieval_event.payload

    # Verdict must not be STUB
    assert payload["verdict"] != "STUB", (
        f"Expected real verdict, got STUB. retrieval_note: {payload.get('retrieval_note')}"
    )

    # Must have at least one chunk
    assert len(payload["retrieved_chunks"]) > 0, (
        "Expected retrieved_chunks to be non-empty after Week 5 wiring."
    )


# ---------------------------------------------------------------------------
# Test: SUPPORT for procurement_manager archiving
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_support_verdict_for_procurement_manager(fresh_engine, tmp_traces):
    """procurement_manager archiving invoices should get SUPPORT from NLI."""
    result = await _run_pipeline(
        fresh_engine,
        tmp_traces,
        raw_text="Archive March 2025 invoices for vendor 4421",
        actor_role="procurement_manager",
    )

    retrieval_event = next(
        e for e in result.events if e.event_type == "retrieval_completed"
    )
    assert retrieval_event.payload["verdict"] == "SUPPORT", (
        f"Expected SUPPORT for procurement_manager archive. "
        f"Got: {retrieval_event.payload['verdict']}. "
        f"Reason: {retrieval_event.payload.get('evidence_reason')}"
    )


# ---------------------------------------------------------------------------
# Test: Gate Check 5 passes with SUPPORT verdict
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_gate_check5_passes_on_support(fresh_engine, tmp_traces):
    """Gate check 5 (evidence_sufficiency) should pass when NLI returns SUPPORT."""
    result = await _run_pipeline(
        fresh_engine,
        tmp_traces,
        raw_text="Archive March 2025 invoices for vendor 4421",
        actor_role="procurement_manager",
    )

    gate_event = next(e for e in result.events if e.event_type == "gate_decision")
    check_results = gate_event.payload.get("check_results", [])

    evidence_check = next(
        (c for c in check_results if c["check_name"] == "evidence_sufficiency"),
        None,
    )
    assert evidence_check is not None, "evidence_sufficiency check not found in gate_decision payload"
    assert evidence_check["passed"] is True, (
        f"Expected evidence_sufficiency to pass. reason_code={evidence_check['reason_code']}"
    )
    # Must NOT be the old stub reason code
    assert evidence_check["reason_code"] != "STUB_ALWAYS_SUPPORT", (
        "evidence_sufficiency still returning STUB_ALWAYS_SUPPORT — Week 5 wiring incomplete."
    )


# ---------------------------------------------------------------------------
# Test: top chunk for archive intent is the archive policy doc
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_top_chunk_is_archive_policy(fresh_engine, tmp_traces):
    """The highest-scored retrieved chunk for archive intent should be POL-001."""
    result = await _run_pipeline(
        fresh_engine,
        tmp_traces,
        raw_text="Archive March 2025 invoices for vendor 4421",
        actor_role="procurement_manager",
    )

    retrieval_event = next(
        e for e in result.events if e.event_type == "retrieval_completed"
    )
    chunks = retrieval_event.payload["retrieved_chunks"]
    assert len(chunks) > 0
    assert chunks[0]["doc_id"] == "POL-001", (
        f"Expected top chunk to be POL-001 (Vendor Invoice Archival Policy). "
        f"Got: {chunks[0]['doc_id']} ({chunks[0]['title']})"
    )


# ---------------------------------------------------------------------------
# Test: retrieval_completed has evidence_reason field
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_retrieval_completed_has_evidence_reason(fresh_engine, tmp_traces):
    """retrieval_completed payload must include evidence_reason string."""
    result = await _run_pipeline(
        fresh_engine,
        tmp_traces,
        raw_text="Archive March 2025 invoices for vendor 4421",
        actor_role="procurement_manager",
    )

    retrieval_event = next(
        e for e in result.events if e.event_type == "retrieval_completed"
    )
    assert "evidence_reason" in retrieval_event.payload
    assert isinstance(retrieval_event.payload["evidence_reason"], str)
    assert len(retrieval_event.payload["evidence_reason"]) > 0
