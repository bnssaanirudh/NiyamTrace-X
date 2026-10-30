# NiyamTrace-X

Research code and retained evidence for **NiyamTrace-X: An Agent-Based Multilingual Tool for Evaluating Request-Grounded Authorization**.

NiyamTrace-X studies whether multilingual requests retain their authorization limits through interpretation, policy checks, and database writes. This repository preserves successful results, failed runs, superseded methods, and the native execution failures reported in the paper.

## Start here

| Resource | Location |
|---|---|
| Current author-supplied manuscript | [PDF](paper/current/main.pdf) · [LaTeX](paper/current/main.tex) · [bibliography](paper/current/references.bib) |
| Exact uploaded source package | [28 October 2026 manuscript ZIP](paper/releases/2026-10-28/Request_grounded_authorization_for_agents.zip) |
| Results, case-level evidence, snapshots, and analysis | [Paper evidence and reproduction guide](research/paper_evidence/README.md) |
| Paper claims and supporting artifacts | [Claim-to-evidence map](research/paper_evidence/CLAIM_EVIDENCE_MAP.csv) |
| Notebook families and execution status | [Notebook catalog](research/NOTEBOOK_CATALOG.md) |
| What was missing and what was restored | [Publication coverage audit](docs/PUBLICATION_COVERAGE_2026-10-28.md) |
| Platform implementation | [Code README](niyamtrace/README.md) · [architecture](niyamtrace/docs/architecture.md) |

## What the evidence shows

These cohorts measure different outcomes and must not be pooled.

| Evaluation | Retained finding | Boundary |
|---|---|---|
| Frozen multilingual reference | 1,997/2,000 correct Qwen verdicts; 1,996/2,000 GPT-OSS verdicts; zero unsafe final verdicts observed | Generated reference decisions, not native commits |
| Paired interpretation comparison | Granite correctness decreases from 336/360 to 288/360 under full intersection | No measured additional safety benefit in this cohort |
| Native live-model execution | Qwen makes three unauthorized commits affecting five synthetic invoice rows; Granite completes no authorized operations | The evaluated native path misses request polarity |
| Known-candidate control | 48/48 verdicts correct; 12/12 authorized operations completed | Correct semantic inputs supplied without a language model |
| NTX-24B schema replay | 13/16 authorized completions and zero observed unauthorized effects among 104 non-ALLOW cases per model in the grounded reference arm | Reuses NTX-24 generations; no fresh inference or native-production validation |

The repository does not establish general production safety, independent human-language validation, or official AgentDojo/BFCL/tau gate-in-path benchmark success. The evaluated source snapshot is retained separately from later application code. Zero observed unsafe events is a finite-cohort result.

## Reproduce the reported records

The [evidence guide](research/paper_evidence/README.md) describes the retained-record checks. They require Python's standard library and do not download models or run inference.

```bash
python -m zipfile -e research/paper_evidence/NiyamTraceX_Manuscript_Evidence_2026-10-28.zip reproduced_evidence
python -X utf8 reproduced_evidence/Analysis/reproduce_results.py
python -X utf8 reproduced_evidence/Analysis/reproduce_history.py
python -X utf8 research/paper_evidence/verify_ntx24b.py
```

For application setup and its current tests, use the [implementation README](niyamtrace/README.md). Passing application tests does not by itself demonstrate preservation of a user's prohibition through a live model.

## Repository organization

```text
paper/current/                  Current PDF, LaTeX, references, figures, and tables
paper/releases/                 Exact author-supplied manuscript source packages
research/paper_evidence/        Reproduction archive, readable tables, and verification receipts
research/notebooks/             Controlled native and security notebooks
research/notebooks/recovered/   Historical and later recovered notebook sources
results/                       NTX-24 and NTX-24B retained result archives
experiments/                   Original numbered Q1 experiment notebooks
niyamtrace/                    Application, policies, tests, and runtime implementation
codes and results/             September research-history archive and provenance
```

Notebook creation, completed inference, replay, and validated evidence are separate statuses. Private participant requests and private diagnostic notebooks are not part of the public publication package.

The manuscript is a research artifact; this repository does not imply journal acceptance or publication. See [CITATION.cff](CITATION.cff) for repository citation metadata and the manuscript bibliography for its cited literature.
