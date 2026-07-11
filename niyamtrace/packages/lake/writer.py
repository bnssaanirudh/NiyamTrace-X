"""
packages/lake/writer.py — NiyamLake Bronze Layer JSONL Trace Writer

Every pipeline event writes one TraceEvent to a JSONL file (Bronze layer).
Silver (Parquet) and Gold (DuckDB metrics) transforms are Week 7 scope.

Design:
- One JSONL file per pipeline run, named by trace_id.
- Thread-safe: each write is a single json.dumps + newline flush.
- All 9 event types from Section 5 of the brief are supported.
- The writer is injected into the pipeline so tests can substitute a mock.

Status: IMPLEMENTED (Week 1)
Silver/Gold transforms: STUBBED (Week 7)
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone as _tz
from pathlib import Path
from typing import Any

from packages.contracts.schema import TraceEvent, EVENT_TYPES

# Default traces directory (relative to repo root, gitignored)
_DEFAULT_TRACES_DIR = Path(__file__).parent.parent.parent.parent / "traces"


class TraceWriter:
    """
    Append-only JSONL writer for the NiyamLake Bronze layer.

    Usage:
        writer = TraceWriter(trace_id="abc123")
        writer.write(event)
        ...
        writer.close()

    Or as a context manager:
        with TraceWriter(trace_id="abc123") as writer:
            writer.write(event)
    """

    def __init__(
        self,
        trace_id: str,
        traces_dir: Path | None = None,
    ) -> None:
        self.trace_id = trace_id
        self.traces_dir = traces_dir or _DEFAULT_TRACES_DIR
        self.traces_dir.mkdir(parents=True, exist_ok=True)

        self._path = self.traces_dir / f"{trace_id}.jsonl"
        self._file = self._path.open("a", encoding="utf-8")
        self._events: list[TraceEvent] = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def write(self, event: TraceEvent) -> None:
        """Serialize and append one event to the JSONL file."""
        line = event.model_dump_json()
        self._file.write(line + "\n")
        self._file.flush()
        self._events.append(event)

    def events(self) -> list[TraceEvent]:
        """Return all events written in this session (in order)."""
        return list(self._events)

    def event_types_seen(self) -> list[str]:
        return [e.event_type for e in self._events]

    def close(self) -> None:
        if not self._file.closed:
            self._file.close()

    @property
    def path(self) -> Path:
        return self._path

    # ------------------------------------------------------------------
    # Context manager
    # ------------------------------------------------------------------

    def __enter__(self) -> "TraceWriter":
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()


# ---------------------------------------------------------------------------
# Convenience factory — build a TraceEvent from keyword args + timing
# ---------------------------------------------------------------------------


def make_event(
    *,
    trace_id: str,
    task_id: str,
    event_type: EVENT_TYPES,
    decision: str = "",
    payload: dict[str, Any] | None = None,
    parent_span_id: str | None = None,
    variant_group_id: str | None = None,
    language_profile: dict[str, Any] | None = None,
    raw_hash: str = "",
    normalized_hash: str = "",
    model_version: str = "none",
    prompt_commit: str = "none",
    parser_version: str = "0.1.0-hardcoded",
    policy_bundle_hash: str = "",
    tool_schema_hash: str = "",
    data_snapshot_id: str = "",
    latency_ms: float = 0.0,
) -> TraceEvent:
    return TraceEvent(
        trace_id=trace_id,
        task_id=task_id,
        event_type=event_type,
        decision=decision,
        payload=payload or {},
        parent_span_id=parent_span_id,
        variant_group_id=variant_group_id,
        language_profile=language_profile or {},
        raw_hash=raw_hash,
        normalized_hash=normalized_hash,
        model_version=model_version,
        prompt_commit=prompt_commit,
        parser_version=parser_version,
        policy_bundle_hash=policy_bundle_hash,
        tool_schema_hash=tool_schema_hash,
        data_snapshot_id=data_snapshot_id,
        latency_ms=latency_ms,
        timestamp=datetime.now(_tz.utc),
    )


# ---------------------------------------------------------------------------
# Replay reader — read a JSONL trace back as TraceEvent objects (Week 7)
# ---------------------------------------------------------------------------


def read_trace(path: Path) -> list[TraceEvent]:
    """
    Read a Bronze JSONL trace file back into TraceEvent objects.
    Used by replay tests and the Silver-layer transform (Week 7).
    """
    events: list[TraceEvent] = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                events.append(TraceEvent.model_validate_json(line))
    return events
