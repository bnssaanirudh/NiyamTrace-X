# NiyamTrace-X — reviewer reading and reproduction guide

**Manuscript snapshot:** October 28, 2026. **Evidence branch:** `archive/niyamtrace-oct-2026-research-recovery` (draft [PR #2](https://github.com/bnssaanirudh/NiyamTrace-X/pull/2)). The repository's default `main` branch does **not** yet contain this complete review package. Cite or inspect a specific commit, not a moving branch, for reproducibility.

## Five-minute orientation

| Reviewer question | Go directly to |
|---|---|
| What is the manuscript? | [Rendered PDF](paper/current/main.pdf) · [LaTeX](paper/current/main.tex) · [reference database](paper/current/references.bib) |
| Which data generated the manuscript's five tables and six figures? | [Table/figure traceability](research/paper_evidence/RESULTS_AND_FIGURES.md) · [machine-readable data index](research/paper_evidence/REVIEWER_DATA_INDEX.csv) |
| What does each CSV column mean? | [Data dictionary](research/paper_evidence/DATA_DICTIONARY.md) |
| How do I reproduce the saved calculations? | [Reproduction protocol](research/paper_evidence/REPRODUCE.md) |
| Where are the original case records, model generations, DB snapshots, source hashes? | [Curated evidence ZIP](research/paper_evidence/NiyamTraceX_Manuscript_Evidence_2026-10-28.zip) · [archive contents](research/paper_evidence/README.md) |
| How do I check file integrity? | [SHA-256 publication manifest](research/paper_evidence/PUBLICATION_MANIFEST.csv) · [provenance statement](research/paper_evidence/provenance.json) |
| Which notebooks are available? | [All-source notebook catalog](research/NOTEBOOK_CATALOG.md) · [static audit and integrity exceptions](https://github.com/bnssaanirudh/NiyamTrace-X/blob/paper-evidence-format-2026-11-02/paper/reproducibility/2026-11-02/COMPLETE_NOTEBOOK_RESULT_AUDIT.md) |
| What failed and what is still incomplete? | [Known limitations](research/paper_evidence/REPRODUCE.md#limitations-and-unresolved-work) · [native error report](niyamtrace/reports/benchmark_final_v3/benchmark_report.json) · [independent gold readiness](research/results/17_READINESS.json) · [official transfer status](research/results/18_OFFICIAL_GATE_REPORT.json) |

**Interpretation rule:** A **reference verdict** is a model/policy decision. A **reference effect** is evaluated against a synthetic oracle. A **native commit** is a SQLite state change produced in a specific tested application source. They are different endpoints and must never be combined into one “safety accuracy.”

## Which findings should I evaluate first?

| Study and evidence tier | Observed result | Important qualification |
|---|---|---|
| Frozen **reference verdicts** | Qwen3.5-122B 1,997/2,000 (99.85%); GPT-OSS-120B 1,996/2,000 (99.80%) | Generated holdout; **1,042/2,000 Qwen outputs marked cached**, not fully new inference |
| Paired **reference effects** | Granite anchors 336/360 correct vs full intersection 288/360; exact completions 152/162 vs 104/162 | Negative utility effect; 360 requests per direction, repeated under six methods |
| Native **controlled SQLite** | Qwen 3 unsafe commits affecting **five business rows** among 48 attempts; 3/12 authorized tasks completed | Negative counterexample. Not superseded by high reference decision accuracy |
| Native **known-candidate** control | 48/48 correct and 12/12 authorized completions | Inputs supplied correctly; **not live-model accuracy** |
| NTX-24B **reference parser replay** | 13/16 authorized completions and 0/104 observed unsafe non-ALLOW effects per model under grounded reference arm | Same 240 generations as NTX-24; not an independent sample or native deployment |
| Official benchmark and independent human gold | **Not established / BLOCKED** | Do not cite these as scored outcomes |

For full denominators and other historical controlled experiments, see [traceability map](research/paper_evidence/RESULTS_AND_FIGURES.md).

## Read the evidence in the right order

1. Read Tables 1–5 in the [manuscript](paper/current/main.pdf), using [table index](research/paper_evidence/RESULTS_AND_FIGURES.md) to open *case-level* and *summary* CSVs.
2. Inspect **raw retained records and synthetic before/after database snapshots** inside the [curated ZIP](research/paper_evidence/NiyamTraceX_Manuscript_Evidence_2026-10-28.zip); the root-level `Data/` directory contains convenience **derived** data, not every original.
3. Execute the three **retained-record** verifier commands in the [reproduction protocol](research/paper_evidence/REPRODUCE.md) on an unmodified copy of the evidence bundle. Inspect failures rather than suppressing them.
4. Distinguish the actual evaluated source snapshot *inside that ZIP* from later `niyamtrace/` code; do not assume the two are byte-identical.
5. Check the [limitations and exception register](research/paper_evidence/REPRODUCE.md#limitations-and-unresolved-work) before assessing scientific scope.

## Complete machine-readable inventories

- [All 144 notebook files, SHA-256 hashes, structural validity and saved-cell-output counts](research/paper_evidence/REVIEWER_NOTEBOOK_INTEGRITY.csv).
- [All 1,239 checked source/result artifacts, SHA-256 hashes, record counts and ZIP integrity states](research/paper_evidence/REVIEWER_RESULT_FILE_INTEGRITY.csv).
- [Curated notebook-to-study/result/status matrix](research/paper_evidence/REVIEWER_STUDY_STATUS.csv): links key experimental notebooks to the retained evidence or the explicit blocker.

The inventories are a **dated snapshot** of the recovered October evidence tree. There are 86 distinct notebook byte hashes among 144 paths; duplicates are retained for audit rather than counted as separate experiments. The inventory also preserves 47 zero-row CSV files (46 one-byte placeholders). Empty files are not valid completed benchmark scores.



The public evidence contains curated author-generated controlled fixtures, released model-response records, derived analysis CSVs, historical diagnostics, and synthetic SQLite state snapshots. It does **not** provide participants' private text, the private original NB21/NB22 diagnostics, complete independent bilingual adjudicated gold labels, or official gate-in-path AgentDojo/BFCL/τ scores. External MASSIVE and MTOP data must be obtained from their respective original distributors under applicable license terms; this repository provides [dataset revision and file hashes](research/paper_evidence/Data/External_dataset_provenance.json) and [class mappings](research/paper_evidence/Data/External_class_manifest.json).

**Known source issue:** `research/notebooks/23_Full_Pipeline_Public_Controlled.ipynb` is not a valid UTF-8 notebook; [issue #4](https://github.com/bnssaanirudh/NiyamTrace-X/issues/4). Its separate aggregate data remains preserved; do not count it as an executable notebook until it is restored from authenticated bytes.

## Integrity and status

The full-retained-record verification was reproduced in [GitHub Actions, run 41480562701](https://github.com/bnssaanirudh/NiyamTrace-X/actions/runs/41480562701) without running fresh models. The subsequent static inventory counted 144 notebook paths (86 distinct byte hashes; one unreadable) and 1,239 research-related evidence files; [audit report](https://github.com/bnssaanirudh/NiyamTrace-X/blob/paper-evidence-format-2026-11-02/paper/reproducibility/2026-11-02/COMPLETE_NOTEBOOK_RESULT_AUDIT.md). General repository CI still fails preexisting Ruff lint checks. Neither evidence verification nor code formatting proves general production security.

**This is a research reproducibility release, not a product certification, journal acceptance notice, or confirmation of never-observed failures.**
