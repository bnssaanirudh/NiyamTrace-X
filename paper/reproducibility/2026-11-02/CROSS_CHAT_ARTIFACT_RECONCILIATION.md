# Cross-chat NiyamTrace-X artifact reconciliation — 2026-11-02

**Method.** Compared recoverable prior ChatGPT project summaries and saved ChatGPT Library inventories (Oct 13 and Oct 25) with complete GitHub recursive trees of `main` at `3f8467b5e79ffd973dd323b6c5cb8ca72c5c8239`, open recovery branch `archive/niyamtrace-oct-2026-research-recovery` at `8d3482c07dfa9eeeb34c982a706f35fbfb72cb7a`, and this formatting PR branch. Read the Oct 28 publication evidence README, verification receipts, claim map, result JSON, and earlier Oct 25 audits.

**Coverage warning.** ChatGPT history retrieval provides recoverable records, not a guaranteed export of every message, deleted conversation, original attachment or Colab runtime. Git trees prove file presence, not scientific correctness or byte identity with every historical ZIP. This document makes no assertion of exhaustive lifetime coverage.

## GitHub branch reconciliation

- `main`: 1,700 tracked files, 103 `.ipynb` paths; no `paper/current` directory from Oct 28.
- Open draft [PR #2](https://github.com/bnssaanirudh/NiyamTrace-X/pull/2), recovery branch: 1,799 tracked files (99 paths absent from main), 144 notebooks, 30 PDF files. Current manuscript source, figures/tables, curated evidence ZIP, verified case metrics, recovery notebooks and public demo materials are here and **not lost**.
- Open draft [PR #3](https://github.com/bnssaanirudh/NiyamTrace-X/pull/3): documentation/logging/test/CI edits. It does **not** contain PR #2's files; do not describe them as merged.
- Draft [PR #1](https://github.com/bnssaanirudh/NiyamTrace-X/pull/1) concerns experimental native security closure; do not equate unmerged candidate results with deployed code.

## Important recorded results already recovered in PR #2

| Study | Retained-record finding | Correct claim boundary |
|---|---|---|
| Frozen large-model baseline | Qwen3.5-122B 1,997/2,000 final verdict correct; GPT-OSS-120B 1,996/2,000 | Frozen **reference verdicts**, not native database commits. Qwen retained record reports 1,042/2,000 cached outputs; do not claim all were fresh inference |
| Anchors (Q1-01) | 16,794/16,800 correct; 6/2,400 earlier clean false positives | Controlled generated tests |
| Formal set construction (Q1-02) | 50,000 constructed tests | Not general LLM accuracy |
| Broker V2 (Q1-07) | 1,320 isolated reference scenarios | Reference broker only |
| Anchor Lock V3 (Q1-09) | 10,248 retained attacks | Retrospective hardening, not independent blinded attack evaluation |
| Paired effect study | 4,320 method rows over 720 model-request pairs; Granite full vs anchor regression 336/360 → 288/360 | Related requests / grouped analysis; not independent rows |
| Native controlled | Qwen 10/48 verdict correct, 3/12 authorized completions and 3 unsafe-effect cases affecting 5 business rows; Granite 0/48 native correct and 43 output errors | Author-generated synthetic native SQLite; important **negative** evidence |
| Known-candidate control | 48/48 native-correct, 12/12 authorized completions | Supplied-candidate control, **not** live LLM reliability |
| NTX-24 / NTX-24B | 240 original proposals in NTX-24; typed replay 13/16 completed ALLOW and 0/104 non-ALLOW effects/model | NTX-24B does not add new model inference; isolated reference harness |
| External public-intent | MASSIVE Qwen 44/120, Granite 36/120; MTOP Qwen 31/48, Granite 27/48 | Selected **intent** classification, not official agent-gate benchmark |
| Archived tests | XML receipt reports 364 passed and 1 skipped | Older preserved test report, not a fresh CI run |

**Where:** `research/paper_evidence/README.md`, `Data/Verified_Paper_Results.json`, `Data/Verified_Historical_Results.json`, `CLAIM_EVIDENCE_MAP.csv`, `VERIFICATION_2026-10-28.md`, and `NiyamTraceX_Manuscript_Evidence_2026-10-28.zip` on PR #2. NTX-24/24B original ZIPs and supervisor report are also on main.

## Identified gaps — not verified as uploaded to ANY inspected GitHub branch by exact file/path

| Priority | Named historical artifact or evidence | Current interpretation / action |
|---|---|---|
| P0 | `NTX25_results.zip`, `generations.jsonl`, `model_load_errors.json`, `quality_gates.json`, model revision / sample receipts | Original and FIXED NTX25 source notebooks are recovered on PR #2. CPU smoke covered 1,200 generated fixtures × 4 reference arms and separate fault checks; **no full new T4 inference** was verified. Retrieve actual failed/partial output ZIP only if present, retain true errors, and do not fabricate GPU results |
| P1 | `NiyamTraceX_Q1_Experiment_Suite_2026-10-04_ROOTFIX.zip` and the nine `00_preflight_and_freeze.ipynb` through `08_merge_stats_and_export.ipynb` sources | Oct 4 9-notebook suite is absent as the exact nine standalone filenames. PR #2 `NTX_Q1_16..24` are a **different numbered suite**, not substitutes. Restore original if safely available; label all 9 smoke-validation only |
| P1 | Oct 13 `NiyamTraceX_ScientificReports_NTX24B_Integrated_2026-10-13.pdf`, `NiyamTraceX_ESWA_NTX24B_Integrated_2026-10-13.pdf`, `NiyamTraceX_Frontiers_NTX24B_Integrated_2026-10-13.pdf` | Exact named integrated manuscript variants absent from inspected branches. Oct 28 `paper/current/main.pdf` is a later **different** version; it does not establish preservation of the three Oct 13 outputs |
| P1 | `NiyamTraceX_Scientific_Reports_V1_Humanized_FactChecked.pdf`, `NiyamTraceX_Frontiers_AI_V1_Humanized_FactChecked.pdf` and matching latest editable TeX | Earlier ChatGPT Library recovery identified the PDFs. The older `NTX_Papers_Redrafted_2026-10-13_FIXED.zip` predates them; do not label it a matching source. Check rights and preserve exact variants if recovered |
| P1 | Oct 11/12 corrected 32-case source-native **patched rerun** `NTX17_32_CASE_PATCHED_SOURCE_RERUN_PRIVATE.zip` | Prior report showed 64 mock evaluations and a false-ALLOW vendor/year extraction defect; the uploaded later ZIP was the original source run, not verified patched rerun. Private pilot inputs and participant diagnostics intentionally excluded from public GitHub. Retain as an unresolved private follow-up, not a public dataset |
| P2 | Original Oct 6 live-run output ZIPs such as `NTX_T4_LIVE_BASELINES_20261006_125424.zip`, `NTX_T4_LIVE_REDTEAM_20261006_135548.zip`, `NTX_T4_LIVE_STATEFUL_20261006_142907.zip`, plus `NTX_BASELINES_20261006_083055.zip` | Live notebook sources recovered PR #2; exact output ZIP filenames not found. Earlier archive-member inventories identify them, but equivalent contents inside historical ZIPs need independent checksum checking before declaring lost |
| P2 | `NTX_TOP_NLP_RUN_RESULTS.zip`, `NTX_ZERO_UPLOAD_RESULTS.zip`, `NTX_Q1_Evidence_Package.zip`, `NTX_14_Audit_Outputs.zip`, `NTX_Revised_Oct11_Complete_Package.zip`, `NiyamTrace-X_Updated_T4_Results_FullPackage.zip`, `NiyamTrace-X_FirstSubmission_FullPackage.zip` | Exact historical names absent from inspected branches. May overlap archived historical bundles; require member-hash comparison and provenance before uploading copies |
| P2 | Historical raw `NTX17_Full_Trace_Audit_Report_2026-10-12.zip`, case-level private CSV, complete approval/bookkeeping effect monitoring | Earlier trace-audit note verifies 64 hashes but approval/bookkeeping tables were not monitored. Keep private case-level records out of public repository and surface only independently reviewed public summary |
| P2 | 10-minute all-roles demo named `NiyamTrace_10min_all_six_roles_v3.mp4` | Recovery branch contains a **6-minute** demo video, not this exact named 10-minute recording. Check actual footage and token exposure before public upload |

**Missing experimental evidence rather than just missing files:** independent bilingual annotated/adjudicated human gold; verified official AgentDojo/BFCL/τ3 gate-in-path scores; safe native rerun with corrected parser and request-polarity handling; current-branch full security CI; complete, permission-reviewed experiment receipts.

## Scientific corrections easily forgotten when quoting paper results

- GPT-OSS clarification-only replay has **2** unsafe verdicts, not **6** reported in earlier prose.
- Qwen reference records show `cached=true` for **1,042/2,000**, so “all-new independent model inference” is inaccurate.
- Case-weighted versus equal-group bootstrap intervals estimate different quantities; do not merge them.
- A case-level McNemar test that ignores shared request groups is not the independent-group inference.
- Native 48-case Qwen unsafe business mutations and NTX-24B reference zero events are **not** contradictory: different source snapshots/cohorts/gates.
- The stored native benchmark-v3 `200/200` coroutine errors remain invalid for accuracy reporting.
- PR #2's manuscript still lacks a concise explanation for the **374 non-ALLOW groups** used in one zero-event bound: 500 total groups minus 126 ALLOW groups. This warrants an explicit manuscript sentence.
- October 13 older manuscript copies, Oct 28 current manuscript, and September format variants are **versions**, not independent scientific studies.

## Earlier September/October chat artifacts identified on a second retrieval pass

The cross-chat retrieval also surfaced **additional historical filenames absent as exact paths** from main and PR #2, beyond the Oct 25 inventory. These **are historical claims to verify**, not proof that standalone underlying raw bytes remain available:

- September external multilingual validation: `NTX_External_Multilingual_Validation.ipynb`, `NTX_External_Multilingual_Validation_Notebook.zip`, `NTX_External_Multilingual_Validation_Results_GitHub.zip`, `NiyamTrace-X_External_Validation_GitHub_Ready.zip`. The earlier summary reports MASSIVE 450 and MTOP 300 selected cases, including 278/308 strict grounding on one audit. **Do not replace or add these counts to** PR #2's 120-case MASSIVE and 48-case MTOP selected cohort: these are potentially different source/protocol slices and require original files, labels, model revisions, and actual checksums to reconcile.
- October 12 Granite independent retest: `NTX_Granite48_Retest_Outputs.zip` was previously classified as `archived_only` / byte-identical to the prior study, **not a new GPU trial**. The notebook source `NTX_Granite_48_Independent_Retest.ipynb` is already on PR #2. Prior audit attributes the 48 Granite ALLOW→CLARIFY regressions to invalid secondary Qwen proposals (29 missing `args`, 19 invalid tool); detailed raw rows must be checked before using causal wording.
- Source-notebook names `17_NTX17_SOURCE_VENDOR_FIX_AND_32_CASE_RERUN.ipynb`, `17_NiyamTraceX_UPDATED_Combined_Human_Gold_Colab.ipynb` and `18_NTX17_FRESH_CASES_POLICY_GATE_COLAB.ipynb` are referenced in historical notebook audit records but not present as those exact paths on GitHub. **They mention private material**; do not bulk-publish their notebooks or pilot outputs.
- Additional October 13 journal **format** packages: `NiyamTraceX_ESWA_Multilingual_Expanded_2026-10-13.zip`, `NiyamTraceX_Frontiers_Multilingual_Expanded_2026-10-13.zip`, `NiyamTraceX_ScientificReports_Multilingual_Expanded_2026-10-13.zip`, plus separate `NiyamTraceX_*_NTX24B_Integrated_2026-10-13.zip` source packages and earlier clean LaTeX packages. Exact names are absent from the Git trees inspected. These are **versioned manuscripts**, not new experiments.
- Other September submission-format copies and the October 12 all-in-one PDFs/ZIP have names in prior conversations but are lower-priority archival versions. Verify content hashes against the already published Oct 28 manuscript before storing further duplicates.

## Safe recovery sequence

1. Review/merge PR #2's manuscript and evidence first, after legal/privacy/licensing and secret checks. No duplication into PR #3.
2. Publish any missing **genuine** Oct 4 notebook sources, NTX25 failed-output receipts, and journal manuscript variants under dated immutable archive directories with hashes; mark unrun/failed outputs honestly.
3. Keep participant inputs and NB21/NB22 originals withheld; redact/check any raw logs before public release.
4. Link every result in the main README to the correct method, denominators, source commit and benchmark type; then run CI and a manuscript-version comparison.
5. Retain this registry as **OPEN** until actual bytes and hashes are checked, not merely filename strings.

No missing result values, new model inferences, training epochs, or independent gold annotations were fabricated for this reconciliation.
