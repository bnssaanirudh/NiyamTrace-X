# Publication coverage audit — 28 October 2026

Baseline: the author-supplied `Request_grounded_authorization_for_agents__1_ (2).pdf` and matching ZIP. GitHub `main` was inspected at `3f8467b5e79ffd973dd323b6c5cb8ca72c5c8239`; the existing recovery branch was inspected at `7c30ac26f2a60bef7a58339dfa2970ec9f4bcc53`.

## Initial finding

The repository did not contain the complete current manuscript and a clearly accessible reproduction package for its central claims. It had older paper archives, early Q1 experiments, six native/security notebooks, aggregate native results, NTX-24/24B archives, and a separate recovery branch with 34 additional notebooks. Those sources were substantial but did not form a navigable publication release for the attached paper.

## Restored publication surface

| Requirement | Publication location | Scope |
|---|---|---|
| Exact current manuscript | `paper/current/` | PDF, LaTeX, 29-entry bibliography, all supplied figures/tables, and template files |
| Original author upload | `paper/releases/2026-10-28/` | Exact source ZIP, with hash receipt |
| Frozen records, paired effects, native commits, control | `research/paper_evidence/NiyamTraceX_Manuscript_Evidence_2026-10-28.zip` | Saved records, source fingerprints, synthetic snapshots, and audited scripts |
| Readable result tables | `research/paper_evidence/Data/` | Case-level and aggregate CSV/JSON files |
| Fresh verification receipts | `research/paper_evidence/verification/` | Recomputed retained-record reports and manuscript dependency checks |
| Later supporting notebooks | `research/notebooks/recovered/2026-10/paper_support/` | NTX-24/24B, TopClass NLP, independent retest, and safety/generalization audit sources |
| Existing result archives | `results/` | NTX-24 and NTX-24B retained archives |
| Navigation and traceability | Root README, `research/NOTEBOOK_CATALOG.md`, claim/evidence CSV | Explicit cohort and execution boundaries |

## Limits that an upload cannot resolve

- Independent human-language validation and official gate-in-path external benchmarking are not established by these archives.
- Source availability and a notebook's existence do not prove completed inference. NTX-25's failed-generation attempt remains a failure.
- The native experiment was not repeated with the corrected typed parser. NTX-24B replay does not replace the reported native failures.
- The current manuscript retains the 374-group zero-event-bound denominator without the short explanatory sentence requested in the earlier review. The evidence corpus contains 500 groups, of which 126 are expected-ALLOW groups and 374 are non-ALLOW groups.
- No claim of journal acceptance, general production safety, or equality between the evaluated source snapshot and later application code is made.

The PDF and LaTeX are preserved exactly as supplied. Repository recovery does not silently rewrite the paper's conclusion, funding declaration, author statements, or remaining scientific clarifications.

Two files of unreported private-cohort aggregates are excluded from the curated evidence archive. Synthetic controlled records are published with their original scientific bytes. Credential-prefix screening found no matches after correcting a false positive caused by `sk-` inside `task-` identifiers; no log content was redacted.
