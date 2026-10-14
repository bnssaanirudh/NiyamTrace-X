# NiyamTrace-X final paper validation kit (2026-10-11)

This package is **not a new model training project**. It targets the remaining paper weaknesses and must not be interpreted as evidence that the vulnerabilities are already fixed.

**Notebook 15** CPU: frozen October 11 paired-data diagnosis, group-cluster intervals, exact McNemar, 48 Granite regressions. **Runs immediately.**

**Notebook 16** CPU: native production security after GitHub patch. Defaults to `PENDING`; set `NTX_RUN_NATIVE_TESTS=1` and `NTX_REPO_REF=<patched branch>` once Antigravity has implemented native negative tests; commit and logs must be verified. A green reference harness does not count.

**Notebook 17** CPU: blank independent multilingual authorization cases, blinded 2-rater form and adjudication/scoring; creates NO human labels or natural cases. Provide `NTX_NATURAL_CASES`, `NTX_ANNOTATOR_A`, `NTX_ANNOTATOR_B`, `NTX_ADJUDICATED`, `NTX_HOLDOUT_PREDICTIONS` after collecting them. To claim an untouched heldout set, freeze `17_PROPOSED_SPLIT_REVIEW_THEN_FREEZE.csv` as `17_FROZEN_SPLIT.csv` **before** collecting labels/inference. Do not evaluate on post-hoc selected cases.

**Notebook 18** CPU analysis of official benchmark **after** Antigravity implements the gate in real official runner. No files -> BLOCKED. Provide `NTX_OFFICIAL_BENCHMARK_CSV` after native official task run.

## Running on Colab
Upload **the full kit ZIP** and the desired notebook. Execute Notebook 15 first; the first setup cell can prompt to upload the full kit ZIP. No GPU or paid API keys required for Notebook 15, 16 test runner, 17 scoring, 18 offline scoring. Actual official benchmark/model inference could need T4 or heavier depending on harness.

## Evidence boundaries
Oct 11 `paired_variant_cases.csv` is archived system-output/reference SQLite simulation, not production safety proof. It holds 2 model directions × 360 cases × 6 variants = 4320 rows (not 4320 independent cases). Confidence intervals do not establish zero risk. This source should be cited with the archive hash in `evidence/EVIDENCE_PROVENANCE.json`. No results were artificially produced when notebooks were assembled. Store failures, not just successes.
