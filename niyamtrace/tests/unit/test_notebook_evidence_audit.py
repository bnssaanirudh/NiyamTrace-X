"""Static notebook and results inventory tests, with no model execution."""

import csv
import json
import zipfile

from scripts.notebook_evidence_audit import (
    check_notebook,
    main,
    scan_artifact,
)


def test_notebook_syntax_and_saved_outputs(tmp_path):
    notebook = {
        "nbformat": 4,
        "nbformat_minor": 5,
        "metadata": {},
        "cells": [
            {"cell_type": "code", "source": ["x=2\n"], "execution_count": 1,
             "outputs": [{"output_type": "stream", "text": ["2\n"]}]},
            {"cell_type": "code", "source": ["x =\n"], "execution_count": None,
             "outputs": []},
            {"cell_type": "code", "source": ["%matplotlib inline\n"], "execution_count": None,
             "outputs": []},
        ],
    }
    f = tmp_path / "test.ipynb"
    f.write_text(json.dumps(notebook), encoding="utf-8")
    row = check_notebook(f, f.name)
    assert row["status"] == "VALID_JSON_NOTEBOOK"
    assert row["code_cells"] == 3
    assert row["code_cells_with_execution_count"] == 1
    assert row["saved_output_objects"] == 1
    assert row["python_code_syntax_errors"] == 1
    assert row["ipython_shell_cells_skipped"] == 1


def test_corrupt_notebook(tmp_path):
    f = tmp_path / "bad.ipynb"
    f.write_text("{broken", encoding="utf-8")
    row = check_notebook(f, f.name)
    assert row["status"] == "INVALID_NOTEBOOK"


def test_result_inspections(tmp_path):
    csv_path = tmp_path / "metrics.csv"
    csv_path.write_text("id,value\n1,4\n2,5\n", encoding="utf-8")
    assert scan_artifact(csv_path, csv_path.name, 1024)["observed_records"] == 2

    report = tmp_path / "benchmark_report.json"
    report.write_text(
        json.dumps({"summary": {"total": 20, "errored": 20, "passed": 0}}),
        encoding="utf-8",
    )
    assert '"errored":20' in scan_artifact(report, report.name, 1024)["notes"]

    archive = tmp_path / "results.zip"
    with zipfile.ZipFile(archive, "w") as handle:
        handle.writestr("results.txt", "example")
    assert scan_artifact(archive, archive.name, 1024)["validation"] == "ZIP_CRC_OK"
