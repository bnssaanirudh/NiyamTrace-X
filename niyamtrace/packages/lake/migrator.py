"""
packages/lake/migrator.py — Trace Migrator (Bronze Layer)

Upgrades old JSONL traces to the current schema version.
Supports migration from v0 (missing schema_version field) to v1.0.

Usage:
    python -m packages.lake.migrator --dir traces/bronze
"""

from __future__ import annotations

import json
import logging
import shutil
from pathlib import Path
from typing import Any

from packages.contracts.schema import TraceEvent
from packages.lake.writer import CURRENT_SCHEMA_VERSION, _DEFAULT_TRACES_DIR

logger = logging.getLogger(__name__)

class TraceMigrator:
    """Migrates Bronze JSONL trace files to the current schema."""

    def __init__(self, traces_dir: Path | None = None) -> None:
        self.traces_dir = traces_dir or _DEFAULT_TRACES_DIR

    def migrate_all(self) -> dict[str, int]:
        """
        Migrate all JSONL files in the traces directory.
        Returns a summary dict with counts of migrated vs skipped files.
        """
        if not self.traces_dir.exists():
            logger.info("No traces directory found at %s", self.traces_dir)
            return {"migrated": 0, "skipped": 0, "errors": 0}

        results = {"migrated": 0, "skipped": 0, "errors": 0}

        for trace_file in self.traces_dir.glob("*.jsonl"):
            try:
                migrated = self.migrate_file(trace_file)
                if migrated:
                    results["migrated"] += 1
                else:
                    results["skipped"] += 1
            except Exception as e:
                logger.error("Failed to migrate %s: %s", trace_file.name, e)
                results["errors"] += 1

        return results

    def migrate_file(self, trace_file: Path) -> bool:
        """
        Migrates a single trace file if it's on an older schema version.
        Returns True if the file was modified, False if already up to date.
        """
        needs_migration = False
        events: list[dict[str, Any]] = []

        # Read events as raw dicts to inspect without Pydantic validation
        with trace_file.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                evt = json.loads(line)
                
                # Check schema version
                ver = evt.get("schema_version")
                if not ver or ver != CURRENT_SCHEMA_VERSION:
                    needs_migration = True
                    evt = self._upgrade_event(evt)
                
                events.append(evt)

        if not needs_migration:
            return False

        # Write to temporary file, then atomic rename
        temp_file = trace_file.with_suffix(".jsonl.tmp")
        try:
            with temp_file.open("w", encoding="utf-8") as f:
                for evt in events:
                    # Validate against current schema before writing
                    validated = TraceEvent(**evt)
                    f.write(validated.model_dump_json() + "\n")
            
            # Backup original just in case
            backup_file = trace_file.with_suffix(".jsonl.bak")
            shutil.copy2(trace_file, backup_file)
            
            # Replace original
            temp_file.replace(trace_file)
            logger.info("Migrated %s to schema v%s", trace_file.name, CURRENT_SCHEMA_VERSION)
            return True
        except Exception:
            if temp_file.exists():
                temp_file.unlink()
            raise

    def _upgrade_event(self, evt: dict[str, Any]) -> dict[str, Any]:
        """Upgrade a single event dict to the current schema version."""
        current_ver = evt.get("schema_version", "0")
        
        # v0 -> v1.0
        if current_ver == "0":
            evt["schema_version"] = "1.0"
            # In v0, tool_call was a single dict. MultiToolContract changed it to tool_calls (list)
            # We migrate old tool_proposed/simulated/executed events if needed.
            payload = evt.get("payload", {})
            if "tool_call" in payload:
                payload["tool_calls"] = [payload.pop("tool_call")]
            
        return evt

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    import argparse
    parser = argparse.ArgumentParser(description="Migrate NiyamTrace Bronze traces.")
    parser.add_argument("--dir", type=str, help="Path to traces directory")
    args = parser.parse_args()
    
    traces_dir = Path(args.dir) if args.dir else None
    migrator = TraceMigrator(traces_dir)
    res = migrator.migrate_all()
    print(f"Migration complete: {res}")
