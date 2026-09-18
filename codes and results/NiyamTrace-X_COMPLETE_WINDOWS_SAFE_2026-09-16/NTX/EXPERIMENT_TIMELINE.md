# Experiment and artifact timeline

This repository is a chronological record of the NiyamTrace-X research program.

## Phase A — Core semantics and execution
1. **Stage 01 — Semantic Anchor Stress**
   - anchor corruption / clean controls.
2. **Stage 02 — SIL / IIEA ablations**
   - formal synthetic validation of intersection and anchor effects.
3. **Stage 03 — Execution Broker V1**
   - early execution-broker prototype.
4. **Stage 04 — Statistical reproducibility**
   - clustered/bootstrap reproducibility work.

## Phase B — Frozen-runtime attribution
5. **Stage 05 — Frozen-runtime ablation**
   - Qwen and GPT-OSS base/anchor/clarification/full comparisons.
6. **Stage 06 — Metamorphic semantic attack lab**
   - detector robustness and the matching→all weakness.
7. **Stage 07 — Verified Execution Broker V2**
   - randomized capability/tamper/replay/staleness tests.
8. **Stage 08 — Risk-calibrated authorization**
   - exploratory selective-authorization experiment.

## Phase C — Hardening and external validation
9. **Stage 09 — Anchor Lock V3**
   - closes the matching→all gap in the tested metamorphic suite.
10. **Stages 10–12 — External suites**
    - BFCL / MLCL attempts, AgentDojo / Agent-SafetyBench transfer, tau3.
11. **Stage 13 — Unified multi-benchmark meta-analysis.**
12. **Stages 14–15 — final validation / paper-finisher workflows.**

## Phase D — Recovery and closure
- targeted recovery runs;
- merged evidence package;
- multi-provider free-tier experiments;
- local open-weight / T4 experiments.

## Phase E — latest local-T4 pilot and audited papers
- newest T4 package is under `results/local_t4_latest/`;
- final audited claim/evidence map is under `provenance/audited_2026-09-14/`;
- audited IEEE, Springer, and Elsevier sources are under `paper/source/`.

## Scientific status

The repository preserves failures as well as successes. In particular, the
latest local-T4 run is **partial diagnostic evidence**, not proof of broad
three-family external generalization. The frozen 2,000-case experiments,
Anchor Lock V3 hardening, and VEB V2 reference-broker experiments remain the
strongest supported evidence. See the audited evidence map before quoting any
headline number.
