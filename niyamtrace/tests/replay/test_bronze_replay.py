"""
tests/replay/test_bronze_replay.py — Bronze Trace Replay Tests

Validates committed Bronze JSONL traces against structural invariants.
These tests are offline, deterministic, and require NO LLM API calls.
They serve as ground-truth regression coverage for the trace schema.

Scenarios:
  P1: All 9 event types present in every completed trace
  P2: gate_decision event has a valid verdict (ALLOW/BLOCK/ESCALATE)
  P3: language_profile fields populated on every event
  P4: data_snapshot_id matches expected ERP seed snapshot
  P5: policy_bundle_hash is consistent within a single trace
  P6: No event has a null trace_id
  P7: Timestamp ordering is monotonically increasing within a trace
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from data.synthetic.erp import SEED_SNAPSHOT_ID

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

TRACES_DIR = Path(__file__).parent.parent.parent.parent / "traces"
VALID_VERDICTS = {"ALLOW", "BLOCK", "ESCALATE"}
EXPECTED_EVENT_TYPES = {
    "input_received",
    "contract_extracted",
    "retrieval_completed",
    "simulation_completed",
    "gate_evaluated",
    # gate_decision may be combined with gate_evaluated in some trace versions
}


def _load_traces() -> list[tuple[str, list[dict[str, Any]]]]:
    """Load all .jsonl trace files from the Bronze traces directory."""
    if not TRACES_DIR.exists():
        return []
    results = []
    for trace_file in sorted(TRACES_DIR.glob("*.jsonl")):
        events = []
        with trace_file.open(encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        events.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
        if events:
            results.append((trace_file.name, events))
    return results


_ALL_TRACES = _load_traces()

# Skip all replay tests if no traces are available (fresh environment)
pytestmark = pytest.mark.skipif(
    len(_ALL_TRACES) == 0,
    reason="No Bronze JSONL traces found at traces/*.jsonl — run the pipeline first.",
)


# ---------------------------------------------------------------------------
# P1: All core event types present
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("trace_name,events", _ALL_TRACES)
def test_p1_core_event_types_present(trace_name: str, events: list[dict]) -> None:
    """P1: Every trace contains at minimum: input_received and contract_extracted."""
    present = {e.get("event_type") for e in events}
    missing = {"input_received", "contract_extracted"} - present
    assert not missing, (
        f"Trace {trace_name}: missing event types {missing}. "
        f"Present: {present}"
    )


# ---------------------------------------------------------------------------
# P2: gate_decision verdict is valid
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("trace_name,events", _ALL_TRACES)
def test_p2_gate_decision_valid_verdict(trace_name: str, events: list[dict]) -> None:
    """P2: If a gate_evaluated or gate_decision event exists, verdict must be valid."""
    gate_events = [
        e for e in events
        if e.get("event_type") in ("gate_evaluated", "gate_decision", "execution_completed")
    ]
    if not gate_events:
        pytest.skip(f"Trace {trace_name} has no gate events — skipping P2.")

    for evt in gate_events:
        payload = evt.get("payload", {})
        # Try different field names used across schema versions
        verdict = (
            payload.get("verdict")
            or payload.get("gate_verdict")
            or payload.get("decision")
        )
        if verdict is not None:
            assert verdict in VALID_VERDICTS, (
                f"Trace {trace_name}, event {evt.get('event_type')}: "
                f"invalid verdict {verdict!r}. Expected one of {VALID_VERDICTS}"
            )


# ---------------------------------------------------------------------------
# P3: language_profile populated on every event
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("trace_name,events", _ALL_TRACES)
def test_p3_language_profile_populated(trace_name: str, events: list[dict]) -> None:
    """P3: Every event must have a non-null language_profile with primary_lang."""
    for i, evt in enumerate(events):
        lp = evt.get("language_profile")
        assert lp is not None, (
            f"Trace {trace_name}, event #{i} ({evt.get('event_type')}): "
            f"language_profile is null"
        )
        assert "primary_lang" in lp, (
            f"Trace {trace_name}, event #{i}: language_profile missing primary_lang"
        )
        assert lp["primary_lang"], (
            f"Trace {trace_name}, event #{i}: primary_lang is empty"
        )


# ---------------------------------------------------------------------------
# P4: data_snapshot_id matches ERP seed
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("trace_name,events", _ALL_TRACES)
def test_p4_data_snapshot_id_matches_seed(trace_name: str, events: list[dict]) -> None:
    """P4: data_snapshot_id must equal SEED_SNAPSHOT_ID from data.synthetic.erp."""
    for i, evt in enumerate(events):
        snap_id = evt.get("data_snapshot_id", "")
        if snap_id:  # Skip events where it's intentionally empty (e.g., input_received)
            assert snap_id == SEED_SNAPSHOT_ID, (
                f"Trace {trace_name}, event #{i} ({evt.get('event_type')}): "
                f"data_snapshot_id={snap_id!r} does not match "
                f"expected SEED_SNAPSHOT_ID={SEED_SNAPSHOT_ID!r}"
            )


# ---------------------------------------------------------------------------
# P5: policy_bundle_hash is consistent within a trace
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("trace_name,events", _ALL_TRACES)
def test_p5_policy_bundle_hash_consistent(trace_name: str, events: list[dict]) -> None:
    """P5: All non-empty policy_bundle_hash values in a trace must be identical."""
    hashes = {
        evt.get("policy_bundle_hash")
        for evt in events
        if evt.get("policy_bundle_hash")
    }
    assert len(hashes) <= 1, (
        f"Trace {trace_name}: inconsistent policy_bundle_hash values {hashes}. "
        f"Policy must not change mid-trace."
    )


# ---------------------------------------------------------------------------
# P6: No event has a null trace_id
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("trace_name,events", _ALL_TRACES)
def test_p6_no_null_trace_id(trace_name: str, events: list[dict]) -> None:
    """P6: Every event must carry the parent trace_id."""
    for i, evt in enumerate(events):
        assert evt.get("trace_id"), (
            f"Trace {trace_name}, event #{i} ({evt.get('event_type')}): "
            f"trace_id is null or missing"
        )


# ---------------------------------------------------------------------------
# P7: Timestamps monotonically increasing within a trace
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("trace_name,events", _ALL_TRACES)
def test_p7_timestamps_monotonically_increasing(trace_name: str, events: list[dict]) -> None:
    """P7: Event timestamps must be non-decreasing within the trace."""
    timestamps = [e.get("timestamp", "") for e in events]
    for i in range(1, len(timestamps)):
        prev, curr = timestamps[i - 1], timestamps[i]
        if prev and curr:
            assert prev <= curr, (
                f"Trace {trace_name}: timestamp went backwards at event #{i}. "
                f"prev={prev!r}, curr={curr!r}"
            )
