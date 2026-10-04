# NiyamTrace-X Final Reproducibility Manifest

This document explains how every major table and figure in the paper can be regenerated, ensuring that no table value exists only in prose and every headline metric maps to raw evidence.

## Provenance

- **Git Commit SHA:** `59dff44ed3afd07b9d41f2760c0575d261b56073`
- **Policy Hash:** `2f42a781b990e6a3`
- **Tool Registry Hash:** `834ab0377c082729`
- **Dataset Version:** `v1.0.0-holdout` (Hash: `19b84ab39b9c9f4d`)

## Known Failed / Incomplete Runs

Failed benchmark runs are explicitly recorded as infrastructure failures rather than being silently dropped.
- `local_gpu_attempt_v1.zip`
- `local_gpu_attempt_v2.zip`

These attempts resulted in out-of-memory errors and context truncation failures. They are logged for transparency but are excluded from the canonical metric aggregation.

## Generating Results and Tables

1. **Gate Acceptance Rate (Table 1)**
   Run the canonical evaluation script:
   ```bash
   uv run scripts/run_evals.py --dataset data/benchmark/ --output reports/gate_metrics.csv
   ```
   *This relies on the deterministic evaluator (no LLM).*

2. **Security & Variance Tests (Figure 2)**
   To compute false block rates and variance across different intents:
   ```bash
   uv run scripts/run_variance_test.py --dataset data/benchmark/ --output reports/variance_metrics.csv
   ```

3. **External Benchmark Alignment (Table 3)**
   External benchmarks such as AgentDojo and BFCL experienced infrastructure failures. Their results have been marked as INCOMPLETE/INFRA_FAILURE in the final dataset (`tau3_recovered_quick_results.csv`).

## Models and Environment

- **Intent Extraction / NLI**: Rule-based (Deterministic)
- **Runtime Environment**: Python 3.11 with `uv` package manager.
- **Verification Engine**: Transaction-first Verified Execution Broker enabled.

All derivations and trace lakes are completely reproducible by executing the raw benchmark script (`apps/benchmark/run.py`).
