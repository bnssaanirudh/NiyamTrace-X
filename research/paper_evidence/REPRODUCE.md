# Reproduce NiyamTrace-X retained evidence

This guide is for peer reviewers wishing to recompute **saved output analysis**. No API keys, GPUs, external account, running ERP, or paid inference service is required for these steps. It does **not** rerun original LLM generation.

## Version and requirements

- Use the October 28 evidence **release snapshot** checked out from [draft PR #2](https://github.com/bnssaanirudh/NiyamTrace-X/pull/2). Pin an exact commit when citing.
- Python 3.11 or later with the standard library for the three archived verification scripts.
- Available disk space for the compressed [curated evidence archive](NiyamTraceX_Manuscript_Evidence_2026-10-28.zip) and extracted members; do not commit the extracted copies.
- Optional: a PDF reader or LaTeX toolchain for viewing/compiling the separately preserved [current paper](../../paper/current/README.md). Figures already exist as PDFs.
- The archive has an internal `SHA256.json` covering its curated entries; the repository also includes [PUBLICATION_MANIFEST.csv](PUBLICATION_MANIFEST.csv).

## Commands from repository root

~~~bash
# 1. Extract original curated evidence (preserve original ZIP)
python -m zipfile -e research/paper_evidence/NiyamTraceX_Manuscript_Evidence_2026-10-28.zip reproduced_evidence

# 2. Recalculate case, paired, native, effect and source-test record counts
python -X utf8 reproduced_evidence/Analysis/reproduce_results.py

# 3. Recalculate historical synthetic and reference experiments
python -X utf8 reproduced_evidence/Analysis/reproduce_history.py

# 4. Independently reaggregate the NTX-24B saved parser/method rows
python -X utf8 research/paper_evidence/verify_ntx24b.py

# 5. Validate the reviewer-friendly CSVs, totals, file paths and manuscript SHA
python -X utf8 research/paper_evidence/Analysis/validate_reviewer_package.py
~~~

If any command fails, preserve the stdout/stderr and exact source commit; do not edit archived raw data to force a pass. The existing independent [GitHub Actions retained-record job](https://github.com/bnssaanirudh/NiyamTrace-X/actions/runs/41480562701) already executed steps 1–4 and passed, using the Oct 28 recovery evidence at that time. Step 5 is the new lightweight reviewer metadata/CSV verification and should be assessed by its own CI job; it is not a fresh model-validation result.

## Where each file comes from

| Data category | Source and intended interpretation |
|---|---|
| `Reproducibility/Frozen/` | 2,000 generated gold requests and retained model output per large-model checkpoint |
| `Reproducibility/Paired/` | 720 fixed primary requests evaluated under six different methods, 4,320 method rows |
| `Reproducibility/Native_Controlled/` | 48 author-generated controlled requests per small-model arm and matching SQLite effects/traces |
| `Reproducibility/Controlled_Candidate_Preflight/` | 48 known-candidate non-LLM checks, 12 legitimate actions |
| `Reproducibility/Source/` | The historical evaluated source snapshot; distinct from active `niyamtrace/` |
| `Reproducibility/Historical/` | Earlier rule, anchor, broker, red-team and open-weight experiments, with separate denominators |
| `Reproducibility/External/` | Selected public-intent tests, **not official agent authorization benchmarks** |
| `Data/` | Derived tables and diagnostics from curated raw files |

Use [DATA_DICTIONARY.md](DATA_DICTIONARY.md) to interpret columns and [RESULTS_AND_FIGURES.md](RESULTS_AND_FIGURES.md) to match the manuscript to raw records, derived tables and figure files.

## What is *not* established by these commands

A zero exit code proves that scripts' **specified assertions** passed against retained files. It does **not** imply (a) independent correctness of gold labels, (b) no duplicate/template leakage, (c) new end-to-end inference, (d) full production security, (e) equivalence to current source code, or (f) official benchmark generalization. Replaying 240 NTX-24 generations across 8 method/parser choices produces 1,920 evaluation rows, not 1,920 new LLM samples.

## Limitations and unresolved work

| Status | Item | Consequence for publication |
|---|---|---|
| **OBSERVED FAILURE** | Qwen native request-polarity bypass: 3 unauthorized commit cases / 5 modified rows | Disclose and make negative evidence available; don't replace with reference-replay zeroes |
| **INVALID RUN** | Native 200-case report contains 200 coroutine runtime errors | Cannot calculate model/gate accuracy from these cases |
| **BLOCKED** | Independent bilingual human annotation / adjudicated gold | No claims of human-label agreement/independent gold performance |
| **BLOCKED** | Official guarded AgentDojo / BFCL / τ3 task-level run | No published official transfer score |
| **UNVERIFIED** | NTX25 full new GPU results | CPU smoke or model-load failures are not completed GPU inference |
| **CORRUPTED SOURCE** | `research/notebooks/23_Full_Pipeline_Public_Controlled.ipynb` is unreadable JSON | Restore real source from verified original, [issue #4](https://github.com/bnssaanirudh/NiyamTrace-X/issues/4) |
| **CI RED** | Preexisting repository-wide Ruff issues; normal tests skipped | Archived XML test receipt is not a current CI pass |
| **LIMITED EXTERNAL RELEASE** | Private participant/pilot inputs and two private NB21/22 notebooks withheld | No public distribution or unsupported independent annotation claims |
| **PARTIAL FILE QA** | Large historical ZIP CRC not tested by static scanner; some external CSVs zero data rows | Check per-artifact receipts and explicitly annotate empty/failed outputs |

The repository's [external dataset provenance](Data/External_dataset_provenance.json), [model revisions](Data/External_model_revisions.json), and [historical notebook index](../NOTEBOOK_CATALOG.md) are available for reviewers. External datasets remain governed by original data distributors; no assertion of redistribution permission is made.

## Optional: compile the paper

From `paper/current` (requires an installed Springer Nature LaTeX toolchain): `pdflatex main`, `bibtex main`, then `pdflatex main` twice. Static reference/figure checks had no unresolved labels in the recovered author package, but this guide does not state that the PDF has been freshly rebuilt byte-for-byte. The October 28 PDF and source remain unchanged.
