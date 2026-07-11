"""
packages/lake/metrics.py — Gold-Layer DuckDB Analytics (Week 7)

Reads Silver Parquet files into a DuckDB in-memory database and exposes
query functions for the NiyamTrace dashboard.

Metric functions:
  gate_verdict_counts()          — ALLOW/BLOCK/ESCALATE distribution
  cross_lingual_divergence_rate()— fraction of variant groups with verdict_flip
  avg_latency_by_event()         — avg latency_ms per event_type
  evidence_verdict_distribution()— SUPPORT/CONTRADICT/INSUFFICIENT counts
  recent_traces()                — last N unique trace_ids with summary
  trace_summary(trace_id)        — full event list for one trace

Status: IMPLEMENTED (Week 7)
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).parent.parent.parent.parent
_DEFAULT_SILVER_DIR = _REPO_ROOT / "traces" / "silver"


def _load_duckdb(silver_dir: Path):
    """
    Load all Parquet files in silver_dir into a DuckDB in-memory database.
    Returns a duckdb.DuckDBPyConnection.
    """
    try:
        import duckdb
    except ImportError:
        raise ImportError("duckdb is required for Gold metrics. pip install duckdb")

    conn = duckdb.connect(database=":memory:")
    parquet_files = list(silver_dir.glob("*.parquet"))

    if not parquet_files:
        # Create empty table with known schema
        conn.execute(
            """
            CREATE TABLE events (
                trace_id VARCHAR,
                task_id VARCHAR,
                variant_group_id VARCHAR,
                event_type VARCHAR,
                latency_ms DOUBLE,
                decision VARCHAR,
                gate_verdict VARCHAR,
                gate_reason_code VARCHAR,
                lang_primary VARCHAR,
                lang_code_switched BOOLEAN,
                lang_script VARCHAR,
                lang_confidence DOUBLE,
                timestamp VARCHAR,
                payload_json VARCHAR,
                parser_version VARCHAR,
                policy_bundle_hash VARCHAR
            )
            """
        )
        return conn

    # DuckDB can read multiple parquet files directly with a glob pattern
    glob_pattern = str(silver_dir / "*.parquet")
    conn.execute(f"CREATE TABLE events AS SELECT * FROM read_parquet('{glob_pattern}')")
    return conn


class GoldMetrics:
    """
    Gold-layer DuckDB analytics for NiyamTrace.

    Usage:
        metrics = GoldMetrics()
        print(metrics.gate_verdict_counts())
    """

    def __init__(self, silver_dir: Path | None = None) -> None:
        self.silver_dir = silver_dir or _DEFAULT_SILVER_DIR
        self._conn = _load_duckdb(self.silver_dir)

    def gate_verdict_counts(self) -> dict[str, int]:
        """
        Returns ALLOW/BLOCK/ESCALATE counts from gate_decision events.
        Example: {"ALLOW": 12, "BLOCK": 3, "ESCALATE": 1}
        """
        rows = self._conn.execute(
            """
            SELECT gate_verdict, COUNT(*) AS cnt
            FROM events
            WHERE event_type = 'gate_decision'
              AND gate_verdict IS NOT NULL
              AND gate_verdict != ''
            GROUP BY gate_verdict
            ORDER BY cnt DESC
            """
        ).fetchall()
        return {row[0]: row[1] for row in rows}

    def avg_latency_by_event(self) -> dict[str, float]:
        """
        Returns average latency_ms per event_type.
        Example: {"input_received": 0.5, "gate_decision": 1.2, ...}
        """
        rows = self._conn.execute(
            """
            SELECT event_type, ROUND(AVG(latency_ms), 3) AS avg_ms
            FROM events
            WHERE latency_ms IS NOT NULL
            GROUP BY event_type
            ORDER BY event_type
            """
        ).fetchall()
        return {row[0]: float(row[1]) for row in rows}

    def evidence_verdict_distribution(self) -> dict[str, int]:
        """
        Returns SUPPORT/CONTRADICT/INSUFFICIENT counts from retrieval_completed events.
        """
        rows = self._conn.execute(
            """
            SELECT gate_verdict AS verdict, COUNT(*) AS cnt
            FROM events
            WHERE event_type = 'retrieval_completed'
              AND gate_verdict IS NOT NULL
            GROUP BY gate_verdict
            ORDER BY cnt DESC
            """
        ).fetchall()
        return {row[0]: row[1] for row in rows}

    def cross_lingual_divergence_rate(self) -> dict[str, Any]:
        """
        Estimates the cross-lingual divergence rate.

        For variant groups (variant_group_id != NULL), finds groups where
        not all gate verdicts are the same. Returns:
          {
            "divergent_groups": int,
            "total_groups": int,
            "divergence_rate": float,
          }
        """
        rows = self._conn.execute(
            """
            SELECT
                variant_group_id,
                COUNT(DISTINCT gate_verdict) AS unique_verdicts
            FROM events
            WHERE event_type = 'gate_decision'
              AND variant_group_id IS NOT NULL
              AND gate_verdict IS NOT NULL
            GROUP BY variant_group_id
            """
        ).fetchall()

        total = len(rows)
        divergent = sum(1 for row in rows if row[1] > 1)
        rate = divergent / total if total > 0 else 0.0

        return {
            "divergent_groups": divergent,
            "total_groups": total,
            "divergence_rate": round(rate, 4),
        }

    def recent_traces(self, n: int = 20) -> list[dict[str, Any]]:
        """
        Returns the N most recent unique traces with summary info.
        Each dict: {trace_id, task_id, verdict, primary_lang, timestamp}
        """
        rows = self._conn.execute(
            f"""
            SELECT
                trace_id,
                MAX(task_id) AS task_id,
                MAX(CASE WHEN event_type = 'gate_decision' THEN gate_verdict END) AS verdict,
                MAX(lang_primary) AS primary_lang,
                MAX(timestamp) AS last_event_ts
            FROM events
            GROUP BY trace_id
            ORDER BY last_event_ts DESC
            LIMIT {n}
            """
        ).fetchall()
        return [
            {
                "trace_id": row[0],
                "task_id": row[1],
                "verdict": row[2],
                "primary_lang": row[3],
                "timestamp": row[4],
            }
            for row in rows
        ]

    def trace_summary(self, trace_id: str) -> list[dict[str, Any]]:
        """
        Returns all events for a specific trace_id, ordered by timestamp.
        """
        rows = self._conn.execute(
            """
            SELECT
                event_type, decision, latency_ms, gate_verdict,
                gate_reason_code, lang_primary, timestamp, payload_json
            FROM events
            WHERE trace_id = ?
            ORDER BY timestamp ASC
            """,
            [trace_id],
        ).fetchall()
        return [
            {
                "event_type": row[0],
                "decision": row[1],
                "latency_ms": row[2],
                "gate_verdict": row[3],
                "gate_reason_code": row[4],
                "lang_primary": row[5],
                "timestamp": row[6],
                "payload": json.loads(row[7]) if row[7] else {},
            }
            for row in rows
        ]

    def close(self) -> None:
        """Close the DuckDB connection."""
        if self._conn:
            self._conn.close()
