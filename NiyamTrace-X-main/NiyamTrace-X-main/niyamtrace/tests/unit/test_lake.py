"""
tests/unit/test_lake.py — Unit tests for NiyamLake Silver transform + Gold metrics (Week 7)

Covers:
  - SilverTransform: round-trip JSONL → Parquet → read back
  - _flatten_event: correct field extraction including language_profile
  - GoldMetrics: gate_verdict_counts, avg_latency_by_event, recent_traces (with empty data)
"""

from __future__ import annotations

import json
import sqlite3
import tempfile
from pathlib import Path

import pytest

from packages.lake.transform import SilverTransform, _flatten_event
from packages.lake.writer import TraceWriter, make_event


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------


def _write_test_trace(traces_dir: Path, trace_id: str, n_events: int = 3) -> Path:
    """Write a minimal JSONL trace file for testing."""
    with TraceWriter(trace_id=trace_id, traces_dir=traces_dir) as writer:
        for i in range(n_events):
            event_types = [
                "input_received",
                "contract_extracted",
                "retrieval_completed",
                "policy_evaluated",
                "tool_proposed",
                "tool_simulated",
                "gate_decision",
                "tool_executed",
                "evaluation_verdict",
            ]
            etype = event_types[i % len(event_types)]
            ev = make_event(
                trace_id=trace_id,
                task_id="task-test",
                event_type=etype,
                latency_ms=float(i + 1) * 0.5,
                decision="ALLOW" if etype == "gate_decision" else "",
                language_profile={
                    "primary_lang": "eng_Latn",
                    "code_switched": False,
                    "script": "Latin",
                    "confidence": 0.98,
                },
                payload={"verdict": "ALLOW", "reason_code": "OK"} if etype == "gate_decision" else {},
            )
            writer.write(ev)
    return traces_dir / f"{trace_id}.jsonl"


# ---------------------------------------------------------------------------
# _flatten_event tests
# ---------------------------------------------------------------------------


class TestFlattenEvent:
    def test_extracts_scalar_fields(self):
        raw = {
            "trace_id": "abc123",
            "task_id": "task-1",
            "event_type": "gate_decision",
            "latency_ms": 1.23,
            "decision": "ALLOW",
            "language_profile": {},
            "payload": {},
        }
        flat = _flatten_event(raw)
        assert flat["trace_id"] == "abc123"
        assert flat["event_type"] == "gate_decision"
        assert flat["latency_ms"] == 1.23

    def test_extracts_language_profile(self):
        raw = {
            "trace_id": "x",
            "language_profile": {
                "primary_lang": "tel_Latn",
                "code_switched": True,
                "script": "Latin",
                "confidence": 0.91,
            },
            "payload": {},
        }
        flat = _flatten_event(raw)
        assert flat["lang_primary"] == "tel_Latn"
        assert flat["lang_code_switched"] is True
        assert flat["lang_confidence"] == 0.91

    def test_payload_serialized_to_json_string(self):
        raw = {
            "trace_id": "x",
            "language_profile": {},
            "payload": {"verdict": "BLOCK", "reason_code": "VENDOR_ID_MISMATCH"},
        }
        flat = _flatten_event(raw)
        assert isinstance(flat["payload_json"], str)
        payload = json.loads(flat["payload_json"])
        assert payload["verdict"] == "BLOCK"

    def test_gate_verdict_extracted_from_payload(self):
        raw = {
            "trace_id": "x",
            "language_profile": {},
            "payload": {"verdict": "BLOCK", "reason_code": "APPROVAL_REQUIRED"},
        }
        flat = _flatten_event(raw)
        assert flat["gate_verdict"] == "BLOCK"
        assert flat["gate_reason_code"] == "APPROVAL_REQUIRED"

    def test_missing_fields_return_none(self):
        flat = _flatten_event({})
        assert flat["trace_id"] is None
        assert flat["lang_primary"] is None


# ---------------------------------------------------------------------------
# SilverTransform tests
# ---------------------------------------------------------------------------


class TestSilverTransform:
    def test_transform_empty_bronze_dir(self, tmp_path):
        bronze_dir = tmp_path / "bronze"
        bronze_dir.mkdir()
        silver_dir = tmp_path / "silver"
        transform = SilverTransform(bronze_dir=bronze_dir, silver_dir=silver_dir)
        try:
            count = transform.run(verbose=False)
            assert count == 0
        except ImportError:
            pytest.skip("pyarrow not installed — skipping Silver transform test")

    def test_transform_one_trace(self, tmp_path):
        bronze_dir = tmp_path / "bronze"
        bronze_dir.mkdir()
        silver_dir = tmp_path / "silver"

        trace_id = "test-trace-001"
        _write_test_trace(bronze_dir, trace_id, n_events=9)

        transform = SilverTransform(bronze_dir=bronze_dir, silver_dir=silver_dir)
        try:
            count = transform.run(verbose=False)
            assert count == 1
            assert (silver_dir / f"{trace_id}.parquet").exists()
        except ImportError:
            pytest.skip("pyarrow not installed — skipping Silver transform test")

    def test_round_trip_preserves_event_count(self, tmp_path):
        bronze_dir = tmp_path / "bronze"
        bronze_dir.mkdir()
        silver_dir = tmp_path / "silver"

        trace_id = "test-trace-rt"
        _write_test_trace(bronze_dir, trace_id, n_events=5)

        transform = SilverTransform(bronze_dir=bronze_dir, silver_dir=silver_dir)
        try:
            transform.run(verbose=False)
            rows = transform.read_silver(trace_id)
            assert len(rows) == 5
        except ImportError:
            pytest.skip("pyarrow not installed — skipping Silver round-trip test")

    def test_round_trip_trace_id_preserved(self, tmp_path):
        bronze_dir = tmp_path / "bronze"
        bronze_dir.mkdir()
        silver_dir = tmp_path / "silver"

        trace_id = "test-trace-id-check"
        _write_test_trace(bronze_dir, trace_id, n_events=3)

        transform = SilverTransform(bronze_dir=bronze_dir, silver_dir=silver_dir)
        try:
            transform.run(verbose=False)
            rows = transform.read_silver(trace_id)
            for row in rows:
                assert row["trace_id"] == trace_id
        except ImportError:
            pytest.skip("pyarrow not installed")


# ---------------------------------------------------------------------------
# GoldMetrics tests (with empty data — no pyarrow needed for empty case)
# ---------------------------------------------------------------------------


class TestGoldMetricsEmpty:
    def test_empty_silver_dir_returns_empty_dicts(self, tmp_path):
        silver_dir = tmp_path / "silver_empty"
        silver_dir.mkdir()
        try:
            from packages.lake.metrics import GoldMetrics
            gm = GoldMetrics(silver_dir=silver_dir)
            assert gm.gate_verdict_counts() == {}
            assert gm.avg_latency_by_event() == {}
            assert gm.evidence_verdict_distribution() == {}
            divergence = gm.cross_lingual_divergence_rate()
            assert divergence["total_groups"] == 0
            assert divergence["divergence_rate"] == 0.0
            gm.close()
        except ImportError:
            pytest.skip("duckdb not installed — skipping Gold metrics test")

    def test_recent_traces_empty_returns_empty_list(self, tmp_path):
        silver_dir = tmp_path / "silver_empty2"
        silver_dir.mkdir()
        try:
            from packages.lake.metrics import GoldMetrics
            gm = GoldMetrics(silver_dir=silver_dir)
            assert gm.recent_traces(n=10) == []
            gm.close()
        except ImportError:
            pytest.skip("duckdb not installed")
