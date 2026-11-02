# NiyamTrace-X: all-notebook and retained-results audit (2026-11-02)

## Verified scope

Audited GitHub recovery branch `archive/niyamtrace-oct-2026-research-recovery`, tree `8d3482c07dfa9eeeb34c982a706f35fbfb72cb7a`. Static scanner: `niyamtrace/scripts/notebook_evidence_audit.py` on this draft PR. Primary [GitHub Actions scan](https://github.com/bnssaanirudh/NiyamTrace-X/actions/runs/41480883525). The downloadable workflow artifact `complete-notebook-and-result-audit` contains `notebook_audit.csv`, `result_file_audit.csv` and `audit_summary.json`.

This scanner **does not execute notebooks**, call model APIs, or train/test the native application. JSON parsing and ZIP checks do not validate scientific labels or claims.

## Notebook audit

| Measure | Verified |
|---|---:|
| Total notebook file paths | **144** |
| Unique complete file SHA-256 hashes | **86** |
| Extra byte-identical notebook paths | **58** |
| Readable notebook JSON | **143** |
| Invalid notebook JSON/encoding | **1** |
| Code cells across the readable notebook paths | **1,692** |
| Code cells with stored execution counts | **0** |
| Stored notebook output objects | **0** |
| Conventional Python code cells passing AST parsing | **1,680** |
| Notebook cells using IPython/shell syntax excluded from AST | **12** |
| Python AST syntax errors among conventionally checked cells | **0** |

Important: saved notebook cell output is not a prerequisite for a previously executed scientific study. These sources are deliberately distributed without their saved outputs, so **separate raw run exports** must establish execution and result provenance. Do not claim 144 independent studies or 86 independent experimental cohorts.

**Broken file:** `research/notebooks/23_Full_Pipeline_Public_Controlled.ipynb` is not readable as UTF-8 JSON. Checked raw size is **330,059 bytes**, first 32 bytes hex `59aae78a782daee9dc6ad79da2eb69bada2b8a08a76a5b6891e9dca2e9edd75d`. A separate CI check found neither UTF-8, UTF-16, UTF-16-LE, nor UTF-16-BE decodes to notebook JSON. Preserve this original blob; restore only a verified source copy and first check for private participant/diagnostic content. Its public controlled output table remains available at `research/results/23_CONTROLLED_COHORT_AGGREGATES.csv`.

**Version ambiguity:** Four notebook basenames (`NTX_Q1_01` through `NTX_Q1_04`) have two different bytes/hashes across historical folders, even though several copies within each version are exact duplicates. Use source SHA and run ID to choose the version underlying the manuscript; never overwrite historical originals by name.

## Result-file audit

Scanned **1,239** selected research/result/report/archives files across GitHub PR #2's recovery tree.

| File category | Count / finding |
|---|---:|
| CSV files successfully read | **297** |
| JSON files parsed | **775** |
| JSONL files parsed | **11** |
| ZIPs with passing CRC | **87** |
| ZIP central directory valid but CRC not fully checked (large uncompressed size) | **2** |
| PDF/TeX files hashed, without semantic review | **67** |
| CSV files containing zero data rows | **47** |
| Of the above, one-byte empty CSV placeholders | **46** |

The 47 zero-data-row CSVs largely occupy old BFCL, AgentDojo, tau and recovery directories. Treat these as **empty/template/incomplete** until the run manifest specifies otherwise; an empty CSV is not a completed scored benchmark. The remaining header-only zero-row file is an early anchor external template.

The two ZIPs left without full CRC in the static scan were `NiyamTrace-X_GitHub_Complete_Research_History_2026-09-14.zip` and `NiyamTraceX_Manuscript_Evidence_2026-10-28.zip`. The latter was **separately extracted and successfully used** in the archived result reproduction checks. All 87 smaller ZIPs scanned passed CRC. Across selected artifacts, file hashes reveal repeated historical copies; retain one canonical pointer plus archived provenance before considering deletion.

## Independent execution of existing retained-record verifier scripts

[GitHub Actions run 41480562701](https://github.com/bnssaanirudh/NiyamTrace-X/actions/runs/41480562701) **passed its dedicated `Recompute retained manuscript results (no inference)` job**, including:

1. `reproduced_evidence/Analysis/reproduce_results.py` — retained frozen, paired, native-controlled, known-candidate effects and provenance checked.
2. `reproduced_evidence/Analysis/reproduce_history.py` — historical anchor, formal effect-set, metamorphic, broker and selected external-intent records checked.
3. `research/paper_evidence/verify_ntx24b.py` — 1,920 replay method rows re-aggregated, referencing the **same original 240 NTX-24 generations**.

This is a **real rerun of the saved-evidence calculations**, not a new language-model experiment, new annotation, native application runtime test, or third-party benchmark.

## Key reproduced retained findings (different cohorts)

| Study | Retained finding | Evidence boundary |
|---|---|---|
| Frozen large model reference | Qwen3.5-122B 1,997/2,000; GPT-OSS-120B 1,996/2,000 final reference decisions correct | Frozen reference; Qwen 1,042/2,000 cached outputs |
| Q1-01 anchor stress | 16,794/16,800 constructed tests correct | Early generated stress distribution |
| Q1-02 | 50,000 constructed formal test cases | Not independent natural-language generalization |
| Broker V2 | 1,320 isolated scenarios | Reference mechanism tests |
| Anchor Lock V3 | 10,248 retained adversarial cases | Retrospective post-hardening |
| Paired study | 4,320 arm-method rows over 720 model-request pairs | Repeated paired rows, not 4,320 independent requests |
| Granite paired ablation | `anchors` 336/360 correct; `full` 288/360 | Negative 48-case regression requiring disclosure |
| Native controlled Qwen | 10/48 verdicts correct; 3/12 authorized completions; **3 unsafe-effect cases changing 5 database rows** | Native source snapshot, author-generated controls, not production guarantee |
| Native controlled Granite | 0/48 native-correct; 43 model-output errors | Unsafe-event absence is confounded by noncompletion |
| Known-candidate control | 48/48 native-correct, 12/12 authorized completions | Supplied known candidates; no live inference in this arm |
| NTX-24B reference replay | 13/16 authorized completions and 0/104 observed non-ALLOW unsafe effects per model | Reuses NTX-24 frozen outputs; reference SQLite gate, not repaired native executor |
| Selected MASSIVE/MTOP external-intent diagnostics | Qwen 44/120 and 31/48; Granite 36/120 and 27/48 | Intent classification, not official AgentDojo/BFCL/tau gate scores |
| Native 200-case v3 report | **200/200 error** ('coroutine' object is not iterable) | Invalid accuracy evaluation, not a model score |
| Human-label readiness / official external evaluation | **BLOCKED** | Adjudicated bilingual gold and official gate-in-path scores missing |

Archived passed tests (e.g. an old 364-pass/one-skip report) are not equivalent to current full CI. The existing root CI still fails lint before the unit/integration/security jobs; the isolated evidence-tooling and retained-record reproduction jobs passed.

## Priority repair list

**P0:** Restore valid Notebook 23 from an actual verified public-safe source; keep the corrupted blob and checksum. Fix current CI lint/undefined names and rerun native security tests. Correct the 200-case benchmark's coroutine issue, then run it again with original denominators.

**P1:** Produce a notebook-to-raw-output matrix with actual source commits, split/seed, parser/policy, model revision, case-level effects and manifest hashes. Reconcile different historical Q1-01..04 versions and 47 empty CSVs. Add missing Oct 4 ROOTFIX sources only if original bytes are available. Keep NTX-25 failures as failures; do not infer successful full GPU inference from CPU smoke.

**P2:** Publish/version remaining October paper format variants only after comparing source/hash and privacy; preserve licensed and intentionally withheld diagnostic cohorts privately. Generate epochs only for actual new training runs.

**No historical scientific results or private raw participant records were edited in this audit.**
