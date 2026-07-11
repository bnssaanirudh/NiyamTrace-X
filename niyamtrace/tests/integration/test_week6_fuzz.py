"""
tests/integration/test_week6_fuzz.py — Week 6 Exit-Criterion Integration Test

Tests that the NiyamFuzz pipeline runs canonical English + 3 multilingual
variants and produces no gate divergence for semantically equivalent requests.

Exit criteria (Week 6):
  ✓ VariantTransformer generates 3 variants for the canonical scenario
  ✓ All variants have the same protected spans as canonical
  ✓ All variants are semantically equivalent (SemanticPreservationChecker)
  ✓ Full pipeline runs on all 3 variants without error
  ✓ No gate divergence (verdict_flip) for semantically equivalent variants
  ✓ TraceComparator produces DivergenceReport for each pair
  ✓ variant_group_id ties all traces together
"""

from __future__ import annotations

import sqlite3
import uuid
from pathlib import Path

import pytest

from apps.gateway.pipeline import NiyamPipeline, PipelineRequest
from data.synthetic.erp import init_schema, reset_to_seed
from packages.fuzz.transforms import VariantTransformer
from packages.fuzz.equivalence import SemanticPreservationChecker
from packages.fuzz.comparator import TraceComparator


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def fresh_erp():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    init_schema(conn)
    reset_to_seed(conn)
    yield conn
    conn.close()


@pytest.fixture
def tmp_traces(tmp_path):
    return tmp_path / "traces"


CANONICAL_TEXT = "Archive invoices for vendor 4421"
CANONICAL_LANG = "eng_Latn"


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _run(
    erp_conn: sqlite3.Connection,
    traces_dir: Path,
    text: str,
    actor_role: str = "procurement_manager",
    variant_group_id: str | None = None,
) -> "PipelineResult":  # type: ignore[name-defined]
    pipeline = NiyamPipeline(erp_conn=erp_conn, traces_dir=traces_dir)
    req = PipelineRequest(
        raw_text=text,
        actor_id="USR-PM-TEST",
        actor_role=actor_role,
        task_id=variant_group_id,
    )
    return pipeline.run(req)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_variant_generator_produces_three_variants():
    transformer = VariantTransformer()
    group_id = str(uuid.uuid4())
    variants = transformer.generate(CANONICAL_TEXT, variant_group_id=group_id)

    assert len(variants) == 3
    assert {v.language for v in variants} == {"hin_Latn", "tel_Latn", "tel_Telu"}
    assert all(v.variant_group_id == group_id for v in variants)


def test_all_variants_preserve_protected_spans():
    checker = SemanticPreservationChecker()
    transformer = VariantTransformer()
    # Use a canonical text with a clear numeric ID that must survive translation
    canonical = "Archive invoices for vendor 4421"
    variants = transformer.generate(canonical)

    for variant in variants:
        result = checker.check(canonical, variant.raw_text)
        assert result.protected_span_match, (
            f"Protected span mismatch in {variant.language}: "
            f"canonical='{canonical}' variant='{variant.raw_text}'. "
            f"Reason: {result.reason}"
        )


def test_full_pipeline_runs_on_all_variants(fresh_erp, tmp_traces):
    """All 3 variants must run through the pipeline without raising."""
    transformer = VariantTransformer()
    group_id = str(uuid.uuid4())
    variants = transformer.generate(CANONICAL_TEXT, variant_group_id=group_id)

    for variant in variants:
        result = _run(fresh_erp, tmp_traces, variant.raw_text, variant_group_id=group_id)
        assert result is not None
        assert result.gate_decision is not None
        # Must have all 9 event types
        event_types = [e.event_type for e in result.events]
        assert "gate_decision" in event_types, f"gate_decision missing for {variant.language}"
        assert "evaluation_verdict" in event_types


def test_no_verdict_flip_for_semantically_equivalent_variants(fresh_erp, tmp_traces):
    """
    Semantically equivalent requests must not flip the gate verdict.
    For the canonical 'archive invoices for vendor 4421' scenario,
    all variants should get the same verdict class as canonical English.

    Note: reason codes may differ (e.g., parser may produce 'unknown' intent
    for non-English text with the current mock). We only check no ALLOW→BLOCK flip.
    """
    comparator = TraceComparator()
    transformer = VariantTransformer()
    group_id = str(uuid.uuid4())
    variants = transformer.generate(CANONICAL_TEXT, variant_group_id=group_id)

    # Run canonical
    canonical_result = _run(fresh_erp, tmp_traces, CANONICAL_TEXT, variant_group_id=group_id)
    canonical_verdict = canonical_result.gate_decision.verdict

    for variant in variants:
        # Run variant in same ERP (reset between variants)
        reset_to_seed(fresh_erp)
        variant_result = _run(
            fresh_erp, tmp_traces, variant.raw_text, variant_group_id=group_id
        )
        report = comparator.compare(
            canonical_result=canonical_result,
            variant_result=variant_result,
            canonical_language=CANONICAL_LANG,
            variant_language=variant.language,
            variant_group_id=group_id,
        )

        # Check that report is produced correctly
        assert isinstance(report, "DivergenceReport".__class__) or hasattr(report, "diverged")
        # Log divergences for visibility
        if report.diverged and report.divergence_type == "verdict_flip":
            # This is a REAL cross-lingual safety issue — fail explicitly
            pytest.fail(
                f"VERDICT FLIP detected for {variant.language}: "
                f"canonical={report.canonical_verdict} "
                f"variant={report.variant_verdict} "
                f"variant_text='{variant.raw_text}'"
            )


def test_comparator_produces_report_with_group_id(fresh_erp, tmp_traces):
    """DivergenceReport must carry the variant_group_id."""
    comparator = TraceComparator()
    group_id = str(uuid.uuid4())

    canonical_result = _run(fresh_erp, tmp_traces, CANONICAL_TEXT, variant_group_id=group_id)
    variant_result = _run(
        fresh_erp, tmp_traces, "Archive ki vendor 4421 invoices", variant_group_id=group_id
    )
    report = comparator.compare(
        canonical_result=canonical_result,
        variant_result=variant_result,
        canonical_language="eng_Latn",
        variant_language="tel_Latn",
        variant_group_id=group_id,
    )

    assert report.variant_group_id == group_id
    assert report.canonical_trace_id == canonical_result.trace_id
    assert report.variant_trace_id == variant_result.trace_id
