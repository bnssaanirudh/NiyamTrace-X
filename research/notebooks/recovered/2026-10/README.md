# NiyamTrace-X — October 2026 recovery index

This directory contains recovered **original notebook sources** from the project's historical ChatGPT Library, committed on 2026-10-25. These were not regenerated from notebook titles.

## Recovery scope

- 3 standalone experiments: `NTX_Standalone_[1-3]_*.ipynb`
- 3 live-provider experiments: `NTX_LIVE_[1-3]_*.ipynb`
- 1 Granite paired regression audit: `15_Granite_48_Paired_Regression_Audit.ipynb`
- 1 corrected 32-case native pilot source: `17_NiyamTraceX_NATIVE_SOURCE_32_PILOT_TODAY_FIXED.ipynb`
- 2 NTX-25 prospective experiment notebooks: original and `_FIXED`
- 1 Q1 evidence completion notebook: `NTX_Q1_Evidence_Completion.ipynb`
- 9 standalone Q1 extension notebooks: `NTX_Q1_16` through `NTX_Q1_24`

**These are 20 source notebooks.** File presence does not imply that every experiment completed, that benchmark labels are independently reviewed, or that native authorization is production safe. The NTX-25 preliminary output archive contains model-load errors and must not be represented as a fully completed external inference run.

### Important data exclusions

The 32-case pilot notebook source refers to private pilot outputs and annotation files. **Those private outputs and the original private diagnostic notebooks 21 and 22 are intentionally not published.** Do not publish those without separate inspection and authorization. The source contains no saved notebook cell outputs.

### Additional packages still to recover as separate standalone files

- `NiyamTraceX_Q1_Experiment_Suite_2026-10-04_ROOTFIX.zip` — contains nine numbered notebooks 00–08, code and configs, but has not been unpacked and added to this branch.
- Three integrated October 13 manuscript source archives for Scientific Reports, ESWA and Frontiers — not yet uploaded as versioned manuscript directories.
- NTX-25 output ZIP — available in original historical Library; should only be published with source-accurate `model_load_errors.json`, `quality_gates.json` and provenance limitations, not claimed as completed model inference.
- Exact frozen 120B per-case records, if eventually released, need reproducibility/version/privacy review.
- Human-reviewed gold labels and official gate-in-path scores remain unavailable or blocked in existing project status records.

## Evaluation guidance

Keep generated reference results, synthetic SQLite effects, model outputs, and official external task success in separate evidence categories. Failed and incomplete runs remain failures/incomplete, not successful benchmark claims.

This recovery adds historical files only. It does not modify the active `niyamtrace/` implementation or certify the research paper for submission.
