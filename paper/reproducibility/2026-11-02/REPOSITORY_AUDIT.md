# Repository and paper-evidence audit — 2026-11-02

Scope: inspected GitHub **main** tree and the draft PR branch, the GitHub Actions lint-job log, archived evidence memo, and executable-script source. This is a structural/source audit, **not** a complete runtime or notebook re-execution.

## Verified CI defect

- GitHub Actions run [41475205217](https://github.com/bnssaanirudh/NiyamTrace-X/actions/runs/41475205217) on the original paper PR ended at Ruff lint with **107 findings**; dependent tests and benchmark were skipped.
- Lint includes imports and formatting, broad exception handlers, class mutable defaults, and undefined symbols. Notable *undefined symbol* diagnostics include `tests/integration/test_week5_evidence.py` and `test_week6_fuzz.py` referencing `PipelineResult`.
- This PR fixes the new script import/order/shebang-related problems and introduces a separate paper-evidence CI job. The preexisting repository-wide Ruff violations are **not** resolved by that change.
- The active root workflow did not execute `tests/security/` in its test job. A historical, nested `niyamtrace/.github/workflows/ci.yml` is **not** an active GitHub Actions workflow from the repository root; its commands also assume the wrong working directory.
- Root CI must eventually run security tests, enforce actual test exit codes, and publish environment/coverage/test reports without hiding failures. The nested historical workflow should be archived with an explanation, not silently used as evidence of passing CI.

## Critical research correctness gaps

1. `niyamtrace/reports/benchmark_final_v3/benchmark_report.json` contains 200 errored scenarios; it cannot establish zero accuracy, good gating performance, or final held-out behavior.
2. `niyamtrace/scripts/run_external_agentdojo.py`, `run_external_bfcl.py` and `run_external_tau3.py` currently implement missing-import diagnostics, not working guarded external benchmark evaluations. They write failure CSVs and exit 0 on import failure. These are **stubs / infrastructure diagnostics**. Changing exit codes would alter automation, so they require separate tested integration work.
3. `niyamtrace/scripts/run_evals.py` reads a fixed `data/gold/intake_contracts.jsonl` path and prints a comparison of extracted actions. The historical reproducibility manifest's documented `--dataset` and `--output` flags do not match this script. It does not write the advertised gate-metric CSV.
4. `niyamtrace/scripts/run_variance_test.py` uses repeated deterministic intake/compiler calls rather than the advertised currently selected LLM backend; do **not** call this observed model sampling stochasticity without a new implementation and executed results.
5. `niyamtrace/scripts/create_evidence_zip.py` copies a selected subset of existing files and overwrites the output directory/ZIP. It lacks a separate immutable release manifest for all included files and does not establish whether upstream results are valid. Use only after a separate provenance/permissions review.
6. `niyamtrace/provenance/CLAIM_EVIDENCE_MATRIX_FINAL.csv` includes unconditional cryptographic/semantic guarantee wording. Narrow to *tested behavior under stated assumptions*; list native effect counterexamples in the later controlled Qwen cohort.
7. `niyamtrace/data/benchmark/README.md` describes “human-approved gold” with no established evidence from the NTX-17 blinded-annotation readiness record. Audit provenance of each label before using human-annotated wording.
8. The NTX-24B reparse is the **same cohort** as NTX-24; do not sum inference counts across parser-policy arms or claim independent replication.
9. Project-specific **epoch-loss curves are not available** for inference-only authorization experiments; adding synthetic epochs would be inappropriate.

## Structural observations

- 39 notebooks in `experiments/`, including `_FIXED`, `_top_level_copy` and older alternatives; a separate `research/notebooks/` contains 16–20 and 23. Build a table of canonical source, superseded variant, archived output path, run ID, model revision, dataset, and status before moving any file.
- Historical source/result bundles and same-SHA duplicate files exist at repository root. Keep frozen originals and document duplicates with hashes; do not delete them until refs and paper citations are mapped.
- Active implementation is `niyamtrace/`, yet papers/archives and logs are spread across `results/`, `traces/`, `research/`, `codes and results/`, `niyamtrace/reports/` and `niyamtrace/results/`. A curated manifest is safer than recursive move/delete.
- Existing `.gitignore` excludes all `*.log`, which means any intentionally published research logs must use a clearly reviewed exception path or structured `json/csv` artifacts.
- Review license/privacy/secret exposure of previously committed session logs, raw traces, ZIPs, historical snapshots and model outputs before public manuscript deposit.

## Review order

**P0:** CI lint/undefined symbol fixes; active security tests; benchmark runtime errors; official benchmark integration and evidence claims.

**P1:** Canonical notebook/result index, raw case-level outputs, model/dataset/policy hashes, independent bilingual gold and analysis scripts for manuscript tables/figures.

**P2:** Format source files using `ruff format` with a scoped diff, reorder imports, clarify package-level READMEs, version/archive duplicates, add full release inventory. Never modify frozen outputs for aesthetics.

No benchmark was rerun and no past experiment was altered as part of this document. Evidence tooling is new and must pass GitHub Actions before it is declared validated.
