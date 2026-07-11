"""
packages/lake/transform.py — JSONL → Parquet Silver-Layer Transform (Week 7)

Reads Bronze JSONL trace files from the traces/ directory and writes
flattened TraceEvent rows to traces/silver/ as Parquet files.

Usage as a module:
    from packages.lake.transform import SilverTransform
    transform = SilverTransform()
    transform.run()

Usage as a CLI:
    python -m packages.lake.transform

Status: IMPLEMENTED (Week 7)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

# Default paths (relative to repo root)
_REPO_ROOT = Path(__file__).parent.parent.parent.parent
_DEFAULT_BRONZE_DIR = _REPO_ROOT / "traces"
_DEFAULT_SILVER_DIR = _REPO_ROOT / "traces" / "silver"


def _flatten_event(event_dict: dict[str, Any]) -> dict[str, Any]:
    """
    Flatten a TraceEvent dict into a row suitable for columnar storage.
    Nested payload is serialized back to a JSON string for Parquet compatibility.
    """
    flat: dict[str, Any] = {}

    # Top-level scalar fields
    scalar_fields = [
        "trace_id", "parent_span_id", "task_id", "variant_group_id",
        "event_type", "latency_ms", "raw_hash", "normalized_hash",
        "model_version", "prompt_commit", "parser_version",
        "policy_bundle_hash", "tool_schema_hash", "data_snapshot_id",
        "decision",
    ]
    for field in scalar_fields:
        flat[field] = event_dict.get(field, None)

    # Timestamp as ISO string
    ts = event_dict.get("timestamp")
    flat["timestamp"] = str(ts) if ts else None

    # Flatten language_profile top-level keys
    lang_profile = event_dict.get("language_profile") or {}
    flat["lang_primary"] = lang_profile.get("primary_lang", None)
    flat["lang_code_switched"] = lang_profile.get("code_switched", None)
    flat["lang_script"] = lang_profile.get("script", None)
    flat["lang_confidence"] = lang_profile.get("confidence", None)

    # Payload as JSON string (not exploded — too schema-variable)
    payload = event_dict.get("payload") or {}
    flat["payload_json"] = json.dumps(payload)

    # Convenience: extract gate verdict from payload if present
    flat["gate_verdict"] = payload.get("verdict", None)
    flat["gate_reason_code"] = payload.get("reason_code", None)

    return flat


class SilverTransform:
    """
    Transforms Bronze JSONL trace files into Silver Parquet files.

    Each Bronze file (one per trace run) becomes one or more rows in Silver.
    All events from a trace are combined into a single Parquet file per trace.
    """

    def __init__(
        self,
        bronze_dir: Path | None = None,
        silver_dir: Path | None = None,
    ) -> None:
        self.bronze_dir = bronze_dir or _DEFAULT_BRONZE_DIR
        self.silver_dir = silver_dir or _DEFAULT_SILVER_DIR

    def run(self, verbose: bool = True) -> int:
        """
        Transform all Bronze JSONL files into Silver Parquet.
        Returns the number of files processed.
        """
        try:
            import pyarrow as pa
            import pyarrow.parquet as pq
        except ImportError:
            raise ImportError(
                "pyarrow is required for Silver transform. "
                "Install with: pip install 'niyamtrace[data]'"
            )

        self.silver_dir.mkdir(parents=True, exist_ok=True)
        jsonl_files = list(self.bronze_dir.glob("*.jsonl"))

        if not jsonl_files:
            if verbose:
                print(f"No JSONL files found in {self.bronze_dir}")
            return 0

        processed = 0
        for jsonl_path in jsonl_files:
            trace_id = jsonl_path.stem
            rows: list[dict[str, Any]] = []

            with jsonl_path.open("r", encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        event_dict = json.loads(line)
                        rows.append(_flatten_event(event_dict))
                    except json.JSONDecodeError as exc:
                        if verbose:
                            print(f"  WARN: skipping malformed line in {jsonl_path.name}: {exc}")

            if not rows:
                continue

            # Convert to Arrow table
            table = pa.Table.from_pylist(rows)
            out_path = self.silver_dir / f"{trace_id}.parquet"
            pq.write_table(table, out_path)
            processed += 1

            if verbose:
                print(f"  Transformed {jsonl_path.name} → silver/{trace_id}.parquet ({len(rows)} events)")

        if verbose:
            print(f"\nSilver transform complete: {processed} files written to {self.silver_dir}")
        return processed

    def read_silver(self, trace_id: str) -> list[dict[str, Any]]:
        """
        Read a Silver Parquet file back as a list of row dicts.
        Used by metrics and tests.
        """
        try:
            import pyarrow.parquet as pq
        except ImportError:
            raise ImportError("pyarrow is required for Silver read.")

        path = self.silver_dir / f"{trace_id}.parquet"
        if not path.exists():
            raise FileNotFoundError(f"Silver file not found: {path}")
        table = pq.read_table(path)
        return table.to_pylist()


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


if __name__ == "__main__":
    transform = SilverTransform()
    count = transform.run(verbose=True)
    sys.exit(0 if count >= 0 else 1)
