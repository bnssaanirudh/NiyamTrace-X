# Manuscript-to-data and figure traceability

All relative links in this document resolve from `research/paper_evidence/`. The [manuscript PDF](../../paper/current/main.pdf), [LaTeX](../../paper/current/main.tex), [supplementary retained records](NiyamTraceX_Manuscript_Evidence_2026-10-28.zip) and [full data dictionary](DATA_DICTIONARY.md) should be reviewed together.

## Main results

| Manuscript element | Downloadable derived data | Original / retained source | Computational check |
|---|---|---|---|
| **Table 1:** frozen verdict accuracy by stage | [Case rows](Data/Frozen_Case_Metrics.csv) · [Stage summary](Data/Frozen_Stage_Metrics.csv) | ZIP `Reproducibility/Frozen/` | `Analysis/reproduce_results.py` inside extracted ZIP |
| **Table 2:** paired reference policy/effect ablations | [4,320 method rows](Data/Paired_Case_Metrics.csv) · [12 summary rows](Data/Paired_Variant_Summary.csv) | ZIP `Reproducibility/Paired/` | `Analysis/reproduce_results.py` inside ZIP |
| **Table 3:** native Qwen/Granite + control | [Native per-case rows](Data/Native_Controlled_Metrics.csv) · [Summary JSON](Data/Verified_Paper_Results.json) | ZIP `Reproducibility/Native_Controlled/`, `Reproducibility/Controlled_Candidate_Preflight/`, source and SQL snapshots | `Analysis/reproduce_results.py` + saved effect oracle |
| **Exploratory NTX-24B table / figure:** typed reference parser | [NTX-24B archive](../../results/NTX24B_results.zip) · [Reaggregated counts](verification/ntx24b_results.json) | `case_level.csv`, `metrics.csv`, `per_language.csv` inside NTX-24B ZIP | [verify_ntx24b.py](verify_ntx24b.py) |
| **Selected public-intent diagnostics:** MASSIVE / MTOP | [Per-case](Data/External_Intent_Case_Metrics.csv) · [Summary](Data/External_Intent_Summary.csv) | ZIP `Reproducibility/External/`; [dataset hashes](Data/External_dataset_provenance.json), [class mapping](Data/External_class_manifest.json) | `Analysis/reproduce_results.py` |
| **Additional historical evidence** | [Derived historical JSON](Data/Verified_Historical_Results.json) | ZIP `Reproducibility/Historical/` | `Analysis/reproduce_history.py` inside ZIP |

**Count interpretation:** Two models × 2,000 frozen requests ≠ an 8,000-request ablation study; the same 2,000 per model are replayed across four policies. The paired 4,320 rows are 720 unique model-request pairs evaluated under six variants. NTX-24B contains 1,920 model/parser/arm rows derived from the *same 240* NTX-24 generations. For native cases, `unsafe_rows` counts changed database rows, not unsafe requests.

## Figure source registry

| Figure file preserved with Oct 28 PDF | Result context | Evidence / presentation note |
|---|---|---|
| [figure_1_frozen_reference.pdf](../../paper/current/images/figure_1_frozen_reference.pdf) | Frozen reference mechanism/decisions | [Frozen summary](Data/Frozen_Stage_Metrics.csv) and source snapshot |
| [figure_2_paired_utility.pdf](../../paper/current/images/figure_2_paired_utility.pdf) | Utility and safety of paired methods | [Paired summary](Data/Paired_Variant_Summary.csv) |
| [figure_3_native_effects.pdf](../../paper/current/images/figure_3_native_effects.pdf) | Native effect outcomes | [Native case rows](Data/Native_Controlled_Metrics.csv) |
| [figure_4_native_diagnostics.pdf](../../paper/current/images/figure_4_native_diagnostics.pdf) | Model-output / execution diagnostics | [Native case rows](Data/Native_Controlled_Metrics.csv) |
| [figure_5_language_scope.pdf](../../paper/current/images/figure_5_language_scope.pdf) | Language coverage and scope | [Frozen case rows](Data/Frozen_Case_Metrics.csv); selected [external intent](Data/External_Intent_Case_Metrics.csv) |
| [figure_6_ntx24b_by_language.pdf](../../paper/current/images/figure_6_ntx24b_by_language.pdf) · [PNG](../../paper/current/images/figure_6_ntx24b_by_language.png) | NTX-24B reference parser replay stratification | [NTX-24B ZIP](../../results/NTX24B_results.zip), `per_language.csv` |

**Important figure caveat:** The `paper/current/images/` files are the exact figures preserved from the author-supplied manuscript; the repository additionally contains `Analysis/make_figures.py` inside the evidence archive and a lightweight code copy under `research/paper_evidence/Analysis/`. Do not claim the latter generates *byte-identical* files with the preserved filenames without a separate regeneration/hash comparison. Inspect figure labels and plotted denominators manually before publishing.

## LaTeX source

[Table 1 source](../../paper/current/tables/table_01_frozen.tex) · [Table 2 source](../../paper/current/tables/table_02_paired.tex) · [Table 3 source](../../paper/current/tables/table_03_native.tex).

The manuscript’s full LaTeX remains unchanged in this reviewer organization pass. Historical tables and figures are not re-numbered, and results are not rewritten.

## Methods and limitations reviewers should explicitly check

- **Frozen:** Generated scenarios, cohort grouping, cached outputs, oracle construction and possible template leakage.
- **Paired:** Why independent secondary proposals lower utility in the Granite direction; confidence intervals must cluster by semantic group; repeated method arms are correlated.
- **Native:** The Qwen unsafe business-state changes and model schema/output errors; effect-diff verification in the source snapshot, not later patched application code.
- **NTX-24B:** Reference parser and SQLite implementation vs native broker: zero observed events only in this small constructed distribution.
- **External:** Selected MASSIVE/MTOP classification is not a verified official AgentDojo/BFCL/τ authorization score.
- **Human evaluation:** Independent bilingual adjudication and final held-out evaluation are not available; see [readiness report](../results/17_READINESS.json) and [official benchmark report](../results/18_OFFICIAL_GATE_REPORT.json).

A manuscript narrative about a one-sided zero-event bound for **374 non-ALLOW groups** should state the denominator explicitly: 500 semantic groups − 126 expected-ALLOW groups = 374. This is a count of groups, not the same as 374 requests. The manuscript was preserved exactly, so this explanatory sentence is currently a **requested manuscript correction**, not already inserted.
