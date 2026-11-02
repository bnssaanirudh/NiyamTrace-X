"""Focused tests for paper evidence tooling (no model or API required)."""
import csv
import json
import subprocess
import sys
from pathlib import Path

from scripts.paper_audit import check_evidence, sha256_file


def test_integrity_reports_present_and_missing(tmp_path):
    root = tmp_path
    (root / "evidence.json").write_text('{"ok": true}', encoding="utf-8")
    register = root / "register.csv"
    with register.open("w", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(output, fieldnames=["evidence_id", "path", "evidence_state"])
        writer.writeheader()
        writer.writerow({"evidence_id": "a", "path": "evidence.json", "evidence_state": "RECORDED"})
        writer.writerow({"evidence_id": "b", "path": "missing.json", "evidence_state": "BLOCKED"})
        writer.writerow({"evidence_id": "c", "path": "../outside.txt", "evidence_state": "BLOCKED"})
    rows = check_evidence(root.resolve(), register)
    assert [row["file_status"] for row in rows] == [
        "PRESENT", "MISSING", "OUTSIDE_REPOSITORY"
    ]
    assert rows[0]["sha256"] == sha256_file(root / "evidence.json")


def test_invalid_json_does_not_pass(tmp_path):
    (tmp_path / "bad.json").write_text("{", encoding="utf-8")
    reg = tmp_path / "register.csv"
    reg.write_text("evidence_id,path,evidence_state\na,bad.json,RECORDED\n", encoding="utf-8")
    assert check_evidence(tmp_path.resolve(), reg)[0]["file_status"] == "INVALID"


def test_real_run_capture(tmp_path):
    script = Path(__file__).resolve().parents[2] / "scripts" / "paper_log_run.py"
    result = subprocess.run(
        [
            sys.executable, str(script), "--name", "smoke", "--kind", "test",
            "--output-dir", str(tmp_path), "--", sys.executable, "-c", "print('actual run')",
        ],
        capture_output=True, text=True, check=False,
    )
    assert result.returncode == 0, result.stderr
    run_dir = next(tmp_path.iterdir())
    metadata = json.loads((run_dir / "metadata.json").read_text(encoding="utf-8"))
    assert metadata["exit_code"] == 0
    assert metadata["kind"] == "test"
    assert "actual run" in (run_dir / "run.log").read_text(encoding="utf-8")


def test_replay_requires_source_run(tmp_path):
    script = Path(__file__).resolve().parents[2] / "scripts" / "paper_log_run.py"
    result = subprocess.run(
        [sys.executable, str(script), "--name", "bad", "--kind", "replay",
         "--output-dir", str(tmp_path), "--", sys.executable, "-c", "pass"],
        capture_output=True, text=True, check=False,
    )
    assert result.returncode != 0
    assert "requires --source-run" in result.stderr
