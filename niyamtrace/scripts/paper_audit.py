#!/usr/bin/env python3
"""Inventory registered paper evidence without changing experimental data."""
import argparse
import csv
import hashlib
import json
import zipfile
from pathlib import Path

def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", type=Path, default=Path("."))
    ap.add_argument("--register", type=Path, required=True)
    ap.add_argument("--output-dir", type=Path, default=Path("paper_audit_out"))
    args = ap.parse_args()
    root = args.repo_root.resolve()
    register = args.register if args.register.is_absolute() else root / args.register
    output = args.output_dir if args.output_dir.is_absolute() else root / args.output_dir
    output.mkdir(parents=True, exist_ok=True)
    records = []
    with register.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            rel = row["path"]
            candidate = (root / rel).resolve()
            status = "MISSING"
            sha = ""
            size = ""
            details = ""
            if not candidate.is_relative_to(root):
                status = "OUTSIDE_REPOSITORY"
            elif candidate.is_file():
                try:
                    sha = digest(candidate)
                    size = candidate.stat().st_size
                    status = "PRESENT"
                    if candidate.suffix in (".json", ".ipynb"):
                        with candidate.open(encoding="utf-8") as f:
                            json.load(f)
                        details = "valid JSON"
                    elif candidate.suffix == ".zip":
                        with zipfile.ZipFile(candidate) as z:
                            bad_member = z.testzip()
                        if bad_member:
                            status, details = "INVALID_ZIP", bad_member
                        else:
                            details = "ZIP CRC checks passed"
                except (OSError, ValueError, json.JSONDecodeError, zipfile.BadZipFile) as exc:
                    status, details = "INVALID", str(exc)
            records.append({"evidence_id": row["evidence_id"], "path": rel,
                            "declared_state": row["evidence_state"], "file_status": status,
                            "sha256": sha, "bytes": size, "validation": details})
    target = output / "evidence_integrity.csv"
    with target.open("w", encoding="utf-8", newline="") as f:
        fields = ["evidence_id", "path", "declared_state", "file_status",
                  "sha256", "bytes", "validation"]
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(records)
    print(json.dumps({"output": str(target), "files": len(records),
                      "status_counts": {s: sum(r["file_status"] == s for r in records)
                                        for s in sorted(set(r["file_status"] for r in records))}},
                     indent=2))
    return 0 if all(r["file_status"] == "PRESENT" for r in records) else 1

if __name__ == "__main__":
    raise SystemExit(main())
