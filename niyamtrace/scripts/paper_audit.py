"""Inspect registered paper evidence and write actual file-integrity results."""

import argparse
import csv
import hashlib
import json
import zipfile
from collections import Counter
from pathlib import Path


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def check_evidence(repo_root: Path, register: Path) -> list[dict]:
    records = []
    with register.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            relative_path = row["path"]
            candidate = (repo_root / relative_path).resolve()
            status, sha, size, detail = "MISSING", "", "", ""
            if not candidate.is_relative_to(repo_root):
                status = "OUTSIDE_REPOSITORY"
            elif candidate.is_file():
                try:
                    sha = sha256_file(candidate)
                    size = candidate.stat().st_size
                    status = "PRESENT"
                    if candidate.suffix in (".json", ".ipynb"):
                        with candidate.open(encoding="utf-8") as file_handle:
                            json.load(file_handle)
                        detail = "valid JSON syntax"
                    elif candidate.suffix == ".zip":
                        with zipfile.ZipFile(candidate) as archive:
                            bad_member = archive.testzip()
                        if bad_member:
                            status, detail = "INVALID_ZIP", bad_member
                        else:
                            detail = "ZIP CRC passed"
                except (OSError, ValueError, zipfile.BadZipFile) as error:
                    status, detail = "INVALID", str(error)
            records.append(
                {
                    "evidence_id": row["evidence_id"],
                    "path": relative_path,
                    "declared_state": row["evidence_state"],
                    "file_status": status,
                    "sha256": sha,
                    "bytes": size,
                    "validation": detail,
                }
            )
    return records


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--register", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=Path("paper_audit_out"))
    args = parser.parse_args()

    root = args.repo_root.resolve()
    register = args.register if args.register.is_absolute() else root / args.register
    output_dir = args.output_dir if args.output_dir.is_absolute() else root / args.output_dir
    records = check_evidence(root, register)
    output_dir.mkdir(parents=True, exist_ok=True)
    report = output_dir / "evidence_integrity.csv"
    columns = [
        "evidence_id",
        "path",
        "declared_state",
        "file_status",
        "sha256",
        "bytes",
        "validation",
    ]
    with report.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(records)
    counts = dict(Counter(row["file_status"] for row in records))
    print(json.dumps({"output": str(report), "files": len(records), "statuses": counts}, indent=2))
    return 0 if records and all(row["file_status"] == "PRESENT" for row in records) else 1


if __name__ == "__main__":
    raise SystemExit(main())
