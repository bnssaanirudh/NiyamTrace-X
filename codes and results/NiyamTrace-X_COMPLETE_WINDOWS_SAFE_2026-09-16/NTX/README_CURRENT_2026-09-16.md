# NiyamTrace-X — Complete Codes, Notebooks, Results, and Research History

**Coverage:** AMD MI300X experimental setup and early runs → frozen runtime evidence → Q1 stages 01–15 → Wave-3 / recovery → hosted and local external validation → T4/open-weight attempts → three-family closure attempts → current 2026-09-16 manuscript/submission artifacts.

This package was assembled to preserve the complete research trail, including successful experiments, superseded implementations, failed/incomplete benchmark attempts, recovery runs, and current manuscript artifacts. Failed runs are retained as failures rather than being converted into scores.

## Start here

1. `EXPERIMENT_TIMELINE_EXTENDED_2026-09-16.md` — chronological AMD-to-current map.
2. `CURRENT_RESEARCH_STATUS_2026-09-16.md` — current evidence and claim boundary.
3. `provenance/current_2026_09_16/PACKAGE_MANIFEST_SHA256.csv` — hash of every file in this package.
4. `provenance/current_2026_09_16/NOTEBOOK_VALIDATION.csv` — JSON validation for all notebooks.
5. `provenance/current_2026_09_16/ZIP_INTEGRITY.csv` — ZIP integrity audit.
6. `provenance/current_2026_09_16/SECRET_SCAN_COMBINED.md` — secret-scan status.
7. `CHAT_AND_BRANCH_ARTIFACT_COVERAGE.md` — what was recoverable from the main and branch work.

## Major directories

- `amd_mi300x_history/` — MI300X bundle README and recovered command/session logs from the AMD phase.
- `notebooks/stage_01_15/` — core experiment notebooks from the complete-history baseline.
- `notebooks/external_validation/` — external benchmark notebooks.
- `notebooks/closure_and_local_validation/` — local/open-weight/T4 and closure workflows.
- `notebooks/post_2026_09_14_recovered/` — additional notebook copies recovered from the saved Library in this assembly pass.
- `results/frozen_evidence/` — frozen runtime source + recovered frozen per-case evidence.
- `results/stage_results/` — stage result archives, including failures/incomplete external stages.
- `results/extracted/` — extracted CSV/JSON/PNG evidence suitable for audit.
- `results/local_t4_latest/` — latest local-T4 diagnostic outputs preserved in the original history package.
- `results/post_2026_09_14_raw_archives/` — current conversation-mounted raw result archives and later three-family/local attempts.
- `paper/current_2026_09_16/` — current Frontiers/IEEE/Springer/Elsevier PDFs, source ZIPs, figures, and submission packages available at assembly time.
- `github_snapshot/` — pinned public-repository commit and restore scripts.
- `archive/` — historical paper/notebook/result packages preserved byte-for-byte where available.

## Scientific claim boundary

The strongest internal evidence remains the frozen 2,000-case multilingual holdout plus frozen-log ablation, Anchor Lock v3 hardening, and the Verified Execution Broker V2 reference implementation. External validation remains partial: hosted tau3 provides a small pilot; local T4/open-weight results are diagnostic; BFCL/AgentDojo broad benchmark generalization and >=3 independent-family generalization are not established.

The package therefore preserves both the positive findings and the unresolved gaps. Use the claim/evidence audit files before quoting headline numbers.

## Security

The 2026-09-14 baseline archive already carried a secret scan with sanitized historical metadata. This assembly additionally scans the newly added AMD logs, notebooks, result ZIP members, and current source packages for common OpenAI/OpenRouter/Groq/Google/Hugging Face/GitHub token prefixes. See the combined report in `provenance/current_2026_09_16/`.
