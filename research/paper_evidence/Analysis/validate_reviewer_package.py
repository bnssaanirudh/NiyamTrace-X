"""Validate the reviewer-facing NiyamTrace-X retained evidence index.

Checks file availability, selected CSV counts, known key results, and manuscript hash.
This is an integrity/consistency check, NOT new inference or gold-label verification.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
EVIDENCE = ROOT / "research" / "paper_evidence"
EXPECTED_MANUSCRIPT_SHA256 = (
    "65513cafa7f2023cc8e6cf59a7a06915bd7484dc04edb26586fb58bfc3b85458"
)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def check(cond: bool, message: str, failures: list[str]) -> None:
    if not cond:
        failures.append(message)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    failures: list[str] = []
    index = read_csv(EVIDENCE / "REVIEWER_DATA_INDEX.csv")
    check(len(index) >= 10, "Reviewer data index missing expected rows", failures)
    allowed_status = {"RETAINED_RECOMPUTED", "INFRA_FAILURE", "BLOCKED", "SOURCE_ONLY"}
    for row in index:
        evidence_id = row["evidence_id"]
        check(row["status"] in allowed_status, f"{evidence_id}: invalid status", failures)
        for field in ("primary_path", "summary_path", "original_evidence_archive"):
            p = (ROOT / row[field]).resolve()
            check(
                p.is_relative_to(ROOT) and p.is_file(),
                f"{evidence_id}: missing/outside repository in {field}: {row[field]}",
                failures,
            )

    data = EVIDENCE / "Data"
    frozen = read_csv(data / "Frozen_Case_Metrics.csv")
    stage = read_csv(data / "Frozen_Stage_Metrics.csv")
    paired = read_csv(data / "Paired_Case_Metrics.csv")
    variants = read_csv(data / "Paired_Variant_Summary.csv")
    native = read_csv(data / "Native_Controlled_Metrics.csv")
    external = read_csv(data / "External_Intent_Case_Metrics.csv")
    external_summary = read_csv(data / "External_Intent_Summary.csv")
    all_protocol_summary = read_csv(data / "External_Intent_All_Protocols_Summary.csv")
    summary = json.loads((data / "Verified_Paper_Results.json").read_text(encoding="utf-8"))

    check(len(frozen) == 4000, f"Frozen request rows={len(frozen)}, expected 4000", failures)
    check(
        Counter(row["model"] for row in frozen)
        == {"Qwen3.5-122B": 2000, "GPT-OSS-120B": 2000},
        "Frozen model denominators unequal to 2000 each",
        failures,
    )
    check(len(stage) == 8, f"Frozen stage rows={len(stage)}, expected 8", failures)
    for row in stage:
        observed = sum(
            case[row["stage"]] == case["gold"]
            for case in frozen if case["model"] == row["model"]
        )
        check(observed == int(row["correct"]), f"Frozen correct mismatch for {row['model']}/{row['stage']}", failures)
        check(int(row["n"]) == 2000, "Frozen stage n not 2000", failures)
        check(abs(float(row["accuracy"]) - observed / 2000) < 1e-10, "Frozen stage accuracy mismatch", failures)

    check(len(paired) == 4320, f"Paired method rows={len(paired)}, expected 4320", failures)
    check(len(variants) == 12, "Expected 12 paired direction/variant summary rows", failures)
    unique_pairs = {(x["direction"], x["id"]) for x in paired}
    check(len(unique_pairs) == 720, f"Paired original pairs={len(unique_pairs)}, expected 720", failures)
    for v in variants:
        arm = [x for x in paired if x["direction"] == v["direction"] and x["variant"] == v["variant"]]
        check(len(arm) == int(v["n"]) == 360, f"Paired arm {v['direction']}/{v['variant']} n mismatch", failures)
        correct = sum(x["decision"] == x["expected"] for x in arm)
        check(correct == int(v["correct"]), f"Paired arm correctness mismatch {v['direction']}/{v['variant']}", failures)
        check(sum(x["unsafe_case"] == "True" for x in arm) == int(v["unsafe_cases"]), f"Paired arm unsafe count mismatch {v['direction']}/{v['variant']}", failures)
        check(sum(
            x["exact_completion"] == "True" and x["expected"] == "ALLOW"
            for x in arm
        ) == int(v["exact_completions"]), f"Paired arm completion mismatch {v['direction']}/{v['variant']}", failures)

    check(len(native) == 96, f"Native per-model rows={len(native)}, expected 96", failures)
    check(Counter(x["model"] for x in native) == {"Qwen": 48, "Granite": 48}, "Native denominators are not 48/model", failures)
    qwen = [row for row in native if row["model"] == "Qwen"]
    check(sum(int(row["unsafe_rows"]) for row in qwen) == 5, "Native Qwen unsafe row count is not 5", failures)
    check(sum(int(row["unsafe_rows"]) > 0 for row in qwen) == 3, "Native Qwen unsafe cases not 3", failures)
    check(sum(row["authorized_completion"] == "True" for row in qwen) == 3, "Native Qwen authorized completions not 3", failures)

    check(len(external) == 672, f"External selected rows={len(external)}, expected 672", failures)
    check(len(all_protocol_summary) == 8, "Expected 8 selected external model/dataset/protocol arms", failures)
    for arm in all_protocol_summary:
        subset = [
            row for row in external
            if row["model"] == arm["model"]
            and row["dataset"] == arm["dataset"]
            and row["protocol"] == arm["protocol"]
        ]
        check(len(subset) == int(arm["n"]), f"All-protocol n mismatch for {arm['model']}/{arm['dataset']}/{arm['protocol']}", failures)
        check(sum(row["correct"] == "True" for row in subset) == int(arm["correct"]), f"All-protocol correct mismatch for {arm['model']}/{arm['dataset']}/{arm['protocol']}", failures)
        check(sum(row["valid"] == "True" for row in subset) == int(arm["valid"]), f"All-protocol valid mismatch for {arm['model']}/{arm['dataset']}/{arm['protocol']}", failures)
        check(abs(float(arm["accuracy_all_attempts"]) - int(arm["correct"]) / int(arm["n"])) < 1e-9, f"All-protocol accuracy field mismatch for {arm['model']}/{arm['dataset']}/{arm['protocol']}", failures)
    check(len(external_summary) == 4, "External dataset summary must contain four arms", failures)
    for arm in external_summary:
        subset = [
            row for row in external
            if row["model"] == arm["model"]
            and row["dataset"] == arm["dataset"]
            and row["protocol"] == arm["protocol"]
        ]
        check(len(subset) == int(arm["n"]), f"Selected intent n mismatch {arm['model']}/{arm['dataset']}", failures)
        check(sum(row["correct"] == "True" for row in subset) == int(arm["correct"]), f"Selected intent correct mismatch {arm['model']}/{arm['dataset']}", failures)
        check(sum(row["valid"] == "True" for row in subset) == int(arm["valid"]), f"Selected intent validity mismatch {arm['model']}/{arm['dataset']}", failures)

    check(summary["native"]["Qwen"]["unsafe_effect_cases"] == 3, "Verified native Qwen unsafe count differs", failures)
    check(summary["native"]["Qwen"]["unsafe_business_rows"] == 5, "Verified native Qwen unsafe row count differs", failures)
    check(summary["preflight"]["native_correct"] == 48, "Known-candidate control summary changed", failures)

    figures = [f"figure_{i}_{label}.pdf" for i, label in [
        (1, "frozen_reference"), (2, "paired_utility"),
        (3, "native_effects"), (4, "native_diagnostics"),
        (5, "language_scope"), (6, "ntx24b_by_language"),
    ]]
    for filename in figures:
        check((ROOT / "paper" / "current" / "images" / filename).is_file(), f"Missing paper figure {filename}", failures)
    for filename in ("table_01_frozen.tex", "table_02_paired.tex", "table_03_native.tex"):
        check((ROOT / "paper" / "current" / "tables" / filename).is_file(), f"Missing LaTeX table {filename}", failures)

    manuscript = ROOT / "paper" / "current" / "main.pdf"
    check(sha256(manuscript) == EXPECTED_MANUSCRIPT_SHA256, "Oct28 preserved paper PDF SHA mismatch", failures)

    result = {
        "status": "PASS" if not failures else "FAIL",
        "run_kind": "static_retained_data_review_only",
        "model_inference_performed": False,
        "independent_labels_verified": False,
        "expected_source": "Oct28 recovered evidence branch",
        "reviewer_index_rows": len(index),
        "frozen_rows": len(frozen),
        "paired_method_rows": len(paired),
        "paired_unique_model_requests": len(unique_pairs),
        "native_model_attempts": len(native),
        "external_selected_rows": len(external),
        "figure_pdfs_checked": len(figures),
        "failures": failures,
    }
    output = json.dumps(result, indent=2) + "\n"
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(output, encoding="utf-8")
    sys.stdout.write(output)
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
