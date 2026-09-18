# NiyamTrace-X — Complete Research History

This package is the GitHub-ready research archive for **NiyamTrace-X**.

It intentionally contains the full research path rather than only the final
paper: notebooks, successful results, failed external-benchmark attempts,
recovery evidence, local-T4 runs, provenance manifests, and the audited
IEEE/Springer/Elsevier manuscripts.

## Start here

- `EXPERIMENT_TIMELINE.md` — chronological experiment map.
- `provenance/audited_2026-09-14/RESULT_EVIDENCE_AUDIT.csv` — final claim-to-evidence audit.
- `provenance/FILE_SHA256_MANIFEST_COMPLETE.csv` — hashes for the entire package.
- `provenance/NOTEBOOK_INDEX_COMPLETE.csv` — notebook inventory.
- `provenance/RESULT_INDEX_COMPLETE.csv` — result/evidence inventory.
- `SECURITY.md` — secret-handling warning for historical notebooks.

## Repository structure

```text
notebooks/
  stage_01_15/                 core research notebooks
  external_validation/        hosted benchmark notebooks
  closure_and_local_validation/
                               free-tier, local-vLLM, and T4 workflows

results/
  stage_results/               original stage ZIPs
  frozen_evidence/             frozen runtime/raw evidence
  final_merged/                recovery/merged evidence
  extracted/                   GitHub-friendly CSV/PNG/JSON extracts
  local_t4_latest/             newest local-T4 run

paper/
  pdfs/                        audited and historical paper PDFs
  source/                      LaTeX sources
  source_archives/             original audited source ZIPs

provenance/
  audited_2026-09-14/          claim/evidence audit and T4 pilot summary
  FILE_SHA256_MANIFEST_COMPLETE.csv
  NOTEBOOK_INDEX_COMPLETE.csv
  RESULT_INDEX_COMPLETE.csv

archive/
  paper_evolution/
  notebook_and_closure_packages/
  original_run_archives/
```

## Reproducibility

Most notebooks install or declare their own runtime dependencies. External
benchmarks additionally depend on the current upstream BFCL/EvalScope,
AgentDojo, tau2-bench, Hugging Face model availability, vLLM compatibility,
GPU memory, and provider/runtime quotas.

The repository deliberately keeps infra failures and incomplete runs. Do not
silently convert a failed benchmark into a score of zero.

## Current claim boundary

The final manuscripts use only the evidence supported by the audited evidence
map. The newest local-T4 evidence is partial and diagnostic; it does **not**
close the >=3-independent-family external-generalization claim.

## License

No software/content license is imposed by this packaging step. Add the license
appropriate for the project before making the repository public.
