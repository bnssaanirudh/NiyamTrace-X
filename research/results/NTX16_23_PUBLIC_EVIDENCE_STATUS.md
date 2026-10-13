# Notebooks 16–23: public evidence and run status

This index distinguishes executed results from templates, smoke checks, and notebooks without saved outputs. It records only aggregates suitable for public release. Per-case traces and the private legacy diagnostic cohort are excluded.

| Notebook | Publicly recorded result | Evidence boundary |
|---|---|---|
| 16 — Production native security closure | On branch commit `a8f94c869636cd399a26c4b52eddb6b15d555915`, three targeted security/integration test groups are recorded PASS; the gate status is `CANDIDATE_REVIEW`. | Candidate result pending independent review. The related open PR is draft; this is not a merged production claim. |
| 17 — Blinded multilingual authorization gold | Readiness is blocked: two independent completed annotations, adjudicated gold, and frozen holdout predictions are absent. | Templates/readiness only; no human-label score. |
| 18 — Official gate-in-path evaluation | Official benchmark report is BLOCKED because no verified task-level AgentDojo/tau run/export is recorded. A separate Oct. 10 Qwen native probe against repo commit `651e87ef452c80008d4f73c8f2de21321e21fa50` recorded two vulnerable scenarios (3 row mutations each), plus passing rollback/authorization controls. | Native synthetic SQLite probe only; not an official benchmark score. This probe exposes failures in that source snapshot. |
| 19 — Source-native synthetic smoke | Notebook source is available; no saved execution output was found. The notebook describes four hand-authored synthetic fixtures. | Source only; results not supplied. |
| 20 — Native broker repair | Retained local verification reports 361 passed, 1 skipped, 0 failed; 34 native adversarial tests and 9/9 native evidence probes passed. | Synthetic engineering tests with SQLite; no live-model inference, human authorization evaluation, Colab execution, or PostgreSQL verification. |
| 21 — Qwen live Colab | No standalone saved output was found. The Qwen aggregate in `23_CONTROLLED_COHORT_AGGREGATES.csv` is from notebook 23's recorded 48-case cohort, not a saved run of notebook 21. | Aggregate only; original notebook withheld because it embeds private diagnostic material. |
| 22 — Granite live Colab | No standalone saved output was found. The Granite aggregate in `23_CONTROLLED_COHORT_AGGREGATES.csv` is from notebook 23's recorded 48-case cohort, not a saved run of notebook 22. | Aggregate only; original notebook withheld because it embeds private diagnostic material. |
| 23 — Full pipeline, public copy | On the 48 author-generated controlled cases: Qwen recorded 48/48, 35 model-output errors, 10 native-correct, 3 authorized nonempty completions, and 3 unsafe-effect cases affecting 5 business rows; Granite recorded 48/48, 43 model-output errors, 0 native-correct, 0 authorized nonempty completions, and 0 unsafe-effect cases. | These are controlled model outputs, not human-gold accuracy or an official external benchmark. The separate 32-case legacy diagnostic is omitted from this public notebook and summary. |

## Provenance

The Notebook 16–18 validation kit and candidate outputs originate from the open draft PR `paper-closure/native-security-and-benchmarks`; the PR remains unmerged. Notebook 20 counts and scope come from its retained verification summary. Notebook 23 is a public controlled-cohort copy with the separate legacy cases, raw trace files, and fresh-label verifier removed; its aggregate counts come from `ACTUAL_LIVE_MODELS/RESULTS_TABLE.csv`. The original notebooks 21 and 22 contain private diagnostic material and are not included in this public addition. Raw per-case Qwen/Granite traces, human-label pilot files, and legacy diagnostic inputs/results are excluded.

