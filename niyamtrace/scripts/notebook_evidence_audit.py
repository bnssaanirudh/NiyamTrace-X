"""Static audit of all notebook sources and paper-result files.

No notebook cell, model, benchmark, archive member, or project module is executed.
Saved notebook outputs are *not* a substitute for verified run receipts.
"""

import argparse
import ast
import csv
import hashlib
import json
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

RESULT_SUFFIXES = {".csv", ".json", ".jsonl", ".zip", ".pdf", ".tex", ".log"}
RESULT_PREFIXES = (
    "research/",
    "results/",
    "traces/",
    "paper/",
    "codes and results/",
    "niyamtrace/results/",
    "niyamtrace/reports/",
    "niyamtrace/data/benchmark/",
    "niyamtrace/provenance/",
)
NOTEBOOK_COLUMNS = [
    "path", "sha256", "bytes", "status", "nbformat", "total_cells",
    "code_cells", "code_cells_with_execution_count", "code_cells_with_saved_outputs",
    "saved_output_objects", "saved_error_objects", "python_code_cells_checked",
    "python_code_syntax_errors", "ipython_shell_cells_skipped",
    "duplicate_identical_copies", "same_basename_different_hashes", "detail",
]
ARTIFACT_COLUMNS = [
    "path", "sha256", "bytes", "extension", "validation", "observed_records",
    "record_kind", "notes",
]


def digest(path: Path) -> str:
    hash_obj = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            hash_obj.update(chunk)
    return hash_obj.hexdigest()


def string_content(value):
    if isinstance(value, list):
        return "".join(str(piece) for piece in value)
    return value if isinstance(value, str) else ""


def is_ipython_code(source: str) -> bool:
    return any(
        line.lstrip().startswith(("!", "%", "?", "%%"))
        for line in source.splitlines()
    )


def check_notebook(path: Path, relative: str) -> dict:
    row = {key: "" for key in NOTEBOOK_COLUMNS}
    row.update(
        {
            "path": relative,
            "sha256": digest(path),
            "bytes": path.stat().st_size,
            "status": "INVALID_NOTEBOOK",
        }
    )
    try:
        with path.open(encoding="utf-8") as handle:
            doc = json.load(handle)
        if not isinstance(doc, dict) or not isinstance(doc.get("cells"), list):
            row["detail"] = "JSON lacks notebook cells array"
            return row
        if doc.get("nbformat") not in (4, 5):
            row["detail"] = "Unexpected notebook format (not a runtime check)"
        row["status"] = "VALID_JSON_NOTEBOOK"
        row["nbformat"] = doc.get("nbformat")
        cells = doc["cells"]
        code_cells = [cell for cell in cells if cell.get("cell_type") == "code"]
        outputs = [
            output
            for cell in code_cells
            for output in (cell.get("outputs") or [])
            if isinstance(output, dict)
        ]
        checked = 0
        syntax_errors = 0
        ipython_skips = 0
        for cell in code_cells:
            source = string_content(cell.get("source"))
            if is_ipython_code(source):
                ipython_skips += 1
                continue
            checked += 1
            try:
                ast.parse(source)
            except SyntaxError:
                syntax_errors += 1
        row.update(
            {
                "total_cells": len(cells),
                "code_cells": len(code_cells),
                "code_cells_with_execution_count": sum(
                    cell.get("execution_count") is not None for cell in code_cells
                ),
                "code_cells_with_saved_outputs": sum(
                    bool(cell.get("outputs")) for cell in code_cells
                ),
                "saved_output_objects": len(outputs),
                "saved_error_objects": sum(
                    output.get("output_type") == "error" for output in outputs
                ),
                "python_code_cells_checked": checked,
                "python_code_syntax_errors": syntax_errors,
                "ipython_shell_cells_skipped": ipython_skips,
            }
        )
    except (OSError, UnicodeError, ValueError, TypeError) as error:
        row["detail"] = type(error).__name__
    return row


def scan_artifact(path: Path, relative: str, crc_limit: int) -> dict:
    row = {key: "" for key in ARTIFACT_COLUMNS}
    suffix = path.suffix.lower()
    row.update(
        {
            "path": relative,
            "extension": suffix,
            "sha256": digest(path),
            "bytes": path.stat().st_size,
            "validation": "HASHED_ONLY",
        }
    )
    try:
        if suffix == ".json":
            with path.open(encoding="utf-8") as handle:
                data = json.load(handle)
            row["validation"] = "PARSE_OK"
            if isinstance(data, dict):
                row["record_kind"] = "object"
                if isinstance(data.get("summary"), dict):
                    summary = data["summary"]
                    row["notes"] = "benchmark summary: " + json.dumps(
                        {
                            key: summary.get(key)
                            for key in ("total", "passed", "failed", "errored")
                        },
                        separators=(",", ":"),
                    )
                elif "status" in data:
                    row["notes"] = "status=" + str(data["status"])[:80]
            elif isinstance(data, list):
                row["record_kind"] = "array"
                row["observed_records"] = len(data)
        elif suffix == ".jsonl":
            with path.open(encoding="utf-8") as handle:
                count = 0
                for line in handle:
                    if line.strip():
                        json.loads(line)
                        count += 1
            row["validation"] = "PARSE_OK"
            row["observed_records"] = count
            row["record_kind"] = "jsonl_rows"
        elif suffix == ".csv":
            with path.open(encoding="utf-8", newline="") as handle:
                reader = csv.reader(handle)
                header = next(reader, [])
                count = sum(1 for _ in reader)
            row["validation"] = "CSV_READ_OK"
            row["observed_records"] = count
            row["record_kind"] = "csv_data_rows"
            row["notes"] = "columns=" + str(len(header))
        elif suffix == ".zip":
            with zipfile.ZipFile(path) as archive:
                members = archive.infolist()
                total_size = sum(entry.file_size for entry in members)
                row["observed_records"] = len(members)
                row["record_kind"] = "zip_members"
                if total_size <= crc_limit:
                    corrupt = archive.testzip()
                    row["validation"] = "ZIP_CRC_OK" if corrupt is None else "ZIP_CRC_FAIL"
                    if corrupt is not None:
                        row["notes"] = "at least one corrupt ZIP member"
                else:
                    row["validation"] = "ZIP_CENTRAL_DIR_OK_CRC_NOT_CHECKED"
                row["notes"] += f" uncompressed_bytes={total_size}"
    except (OSError, UnicodeError, ValueError, TypeError, csv.Error, zipfile.BadZipFile):
        row["validation"] = "VALIDATION_ERROR"
    return row


def write_csv(target: Path, fields: list[str], rows: list[dict]) -> None:
    with target.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--source-ref", required=True)
    parser.add_argument("--crc-limit-mib", type=int, default=32)
    args = parser.parse_args()

    root = args.repo_root.resolve()
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    notebooks = []
    artifacts = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if output in path.parents or ".git" in path.parts:
            continue
        rel = path.relative_to(root).as_posix()
        if path.suffix == ".ipynb":
            notebooks.append(check_notebook(path, rel))
        if path.suffix.lower() in RESULT_SUFFIXES and rel.startswith(RESULT_PREFIXES):
            artifacts.append(
                scan_artifact(path, rel, args.crc_limit_mib * 1024 * 1024)
            )

    hashes = Counter(row["sha256"] for row in notebooks)
    by_basename = defaultdict(set)
    for row in notebooks:
        by_basename[Path(row["path"]).name].add(row["sha256"])
    for row in notebooks:
        row["duplicate_identical_copies"] = hashes[row["sha256"]]
        row["same_basename_different_hashes"] = len(
            by_basename[Path(row["path"]).name]
        )

    write_csv(output / "notebook_audit.csv", NOTEBOOK_COLUMNS, notebooks)
    write_csv(output / "result_file_audit.csv", ARTIFACT_COLUMNS, artifacts)
    summary = {
        "source_ref": args.source_ref,
        "static_only_not_executed": True,
        "notebooks_total": len(notebooks),
        "unique_notebook_file_hashes": len(hashes),
        "notebook_json_invalid": sum(
            row["status"] != "VALID_JSON_NOTEBOOK" for row in notebooks
        ),
        "notebooks_with_saved_cell_outputs": sum(
            int(row["saved_output_objects"] or 0) > 0 for row in notebooks
        ),
        "notebooks_with_saved_error_outputs": sum(
            int(row["saved_error_objects"] or 0) > 0 for row in notebooks
        ),
        "total_saved_output_objects": sum(
            int(row["saved_output_objects"] or 0) for row in notebooks
        ),
        "syntax_error_cells_unqualified": sum(
            int(row["python_code_syntax_errors"] or 0) for row in notebooks
        ),
        "ipython_code_cells_excluded_from_ast": sum(
            int(row["ipython_shell_cells_skipped"] or 0) for row in notebooks
        ),
        "artifacts_indexed": len(artifacts),
        "artifact_validations": dict(
            Counter(row["validation"] for row in artifacts)
        ),
        "limitations": [
            "Notebook outputs alone do not verify runtime provenance or completed studies.",
            "AST checks do not validate IPython magics or run external dependencies.",
            "ZIP central directory checks do not verify scientific labels and large ZIP CRC is skipped.",
            "CSV data-row count does not establish independent samples or accuracy.",
            "Reports can contain contradictory, duplicated, or stale results.",
            "Private cohort files must not be redistributed from generated audits.",
        ],
    }
    (output / "audit_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))
    return 1 if summary["notebook_json_invalid"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
