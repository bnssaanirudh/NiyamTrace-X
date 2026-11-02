# NiyamTrace-X — paper reproducibility and evidence index

**Index date:** 2026-11-02. **Scope:** navigation, provenance, run capture, and defensible claim boundaries. This is **not** a new benchmark run, independent replication, security audit, or paper-acceptance record.

## Canonical locations

| Concern | Repository-root path |
|---|---|
| Active implementation and tests | `niyamtrace/` |
| Original experiment notebooks | `experiments/` and `research/notebooks/` |
| Archived NTX-24/24B evidence | `results/NTX24_NTX24B_Supervisor_Evidence_Report_2026-10-13.md` |
| NTX-16–23 public evidence status | `research/results/NTX16_23_PUBLIC_EVIDENCE_STATUS.md` |
| Older reproducibility baseline | `niyamtrace/provenance/FINAL_REPRODUCIBILITY_MANIFEST.md` |
| This dated evidence index | `paper/reproducibility/2026-11-02/EVIDENCE_REGISTER.csv` |
| Claim-to-source mapping | `paper/reproducibility/2026-11-02/CLAIM_EVIDENCE.csv` |
| Logging/epoch protocol | `paper/reproducibility/2026-11-02/LOGGING_PROTOCOL.md` |

Historical frozen evidence stays in place; no ZIP, trace, or prior manuscript has been renamed by this package. A notebook being present does not prove that the model was run again or that its outputs are valid.

## Evidence categories

- **RECORDED:** A report or saved output exists; verify methods and provenance before claiming a result.
- **REPLAY:** CPU/policy reanalysis of existing frozen model outputs, **not** fresh model inference.
- **DIAGNOSTIC:** Synthetic smoke/integration evidence, not a production guarantee.
- **SOURCE_ONLY:** Notebook or script exists without a verified saved execution.
- **BLOCKED / INFRA_FAILURE:** Missing official results or execution errors; no positive score.
- **HISTORICAL:** Prior manifest for an earlier commit; not an updated audit.
- **INDEPENDENTLY_REPRODUCED:** Reserved for externally rerun and independently reviewed evidence; not assigned here.

## Cross-chat recovery and unmerged results

The [cross-chat artifact reconciliation](CROSS_CHAT_ARTIFACT_RECONCILIATION.md) compares recoverable prior ChatGPT/Library research records with main and the open GitHub recovery PR #2. The [missing-artifact register](CROSS_CHAT_MISSING_ARTIFACTS.csv) records the exact filenames and whether an item is already on PR #2, missing only by name, or genuinely unverified. The Oct 28 manuscript and most frozen/paired/native findings are already preserved in PR #2, not in main; do not duplicate or overstate their merge status.

**CI receipt:** GitHub Actions [run 41478741827](https://github.com/bnssaanirudh/NiyamTrace-X/actions/runs/41478741827) passed the isolated **Paper evidence integrity and tooling** job. The overall workflow failed on inherited Ruff lint findings and skipped downstream tests/benchmark. Paper evidence validation is not a substitute for complete source CI or fresh model inference.

## Precisely scoped results

- NTX-24 recorded **240 original model outputs**: 120 per model, from Qwen2.5-3B and Granite-3.3-2B on generated multilingual cases. NTX-24B is a typed-parser replay **of the same 240 outputs**, not a second sample.
- In NTX-24B, the text-grounded **reference harness** recorded **0/104** unauthorized non-ALLOW effects/model and **13/16** legitimate completions/model. The ungated arm recorded 61/104 Qwen and 60/104 Granite unsafe effects. These data do **not** establish integrated non-bypassable production security or human-gold multilingual accuracy.
- The stored native benchmark-v3 report records **200/200 runtime errors**, including "'coroutine' object is not iterable". Its numeric accuracy field is **not** a valid 200-case model accuracy estimate.
- The NTX-16–23 public status report classifies independent annotation/adjudication and official gate-in-path external scoring as **blocked**.

## Commands

Run a file inventory and hash report from repository root (Python 3.11+, standard library only):

~~~bash
python niyamtrace/scripts/paper_audit.py --repo-root . --register paper/reproducibility/2026-11-02/EVIDENCE_REGISTER.csv --output-dir paper_audit_out
~~~

Run tests with a reproducible execution log from the canonical package directory:

~~~bash
cd niyamtrace
python scripts/paper_log_run.py --name canonical-tests --kind test --output-dir ../paper_runs -- python -m pytest tests -q
~~~

For CPU replay specify `--kind replay --source-run ACTUAL_ORIGINAL_RUN_ID`. For real model inference supply `--kind inference` and keep the model revision and underlying raw responses. To hash outputs, repeat `--artifact PATH` for actual result files.

These tools generate **new** logs when executed and record the true process outcome; the package does not fabricate missing logs, run tests by itself, or create model-training epochs from inference cases.

## Before paper submission

1. Resolve notebook-to-raw-result mappings, SHA-256s, model revisions, seed/split, policy/registry versions and source commit.
2. Check error, timeout, refused and missing case denominators; separate inference from replays and reference harness from native broker.
3. Verify raw source licensing, permissions, independent bilingual annotation and adjudication whenever such claims are made.
4. Attach complete official external benchmark exports before publishing official scores; retain unsuccessful attempts as failures.
5. Match each manuscript figure/table to versioned raw case-level files and regenerating scripts; recompute grouping-aware confidence intervals.
6. Run the actual tests, lint, reproducibility and security review. This documentation change is not proof they pass.
