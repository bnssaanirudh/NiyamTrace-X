# NiyamTrace-X Experiment Timeline — AMD MI300X to 2026-09-16

## Phase 0 — AMD MI300X / ROCm runtime establishment

The earliest retained execution campaign targeted an AMD Instinct MI300X with a ROCm vLLM container. The retained bundle README targets Ubuntu 24.04, MI300X 192 GB HBM, ROCm 7.2.4, and a local OpenAI-compatible vLLM endpoint. Recovered session logs preserve environment checks, model revision pinning, benchmark generation, runtime patches, smoke tests, failures, and reruns.

Key preserved facts from this phase include:
- vLLM ROCm container version 0.28.0 in the retained logs;
- Qwen/Qwen3.5-122B-A10B-FP8 revision `a099dee70ccfcd8d5dda56aaa0b60cb8ecadabc9`;
- generation/validation of `NiyamTrace-Bench-3-v3` with 10,000 rows and 2,500 multilingual groups;
- a matched multilingual 500-case early run that reached 97.6% decision accuracy with zero remaining unsafe ALLOWs, but still had false blocks/unnecessary clarification and therefore was not the final frozen paper evidence.

The raw session history is retained under `amd_mi300x_history/` so that debugging decisions and superseded runs remain auditable.

## Phase 1 — Core semantic/security experiments

1. Stage 01 — Semantic Anchor Stress.
2. Stage 02 — SIL / IIEA formal ablations.
3. Stage 03 — Verified Execution Broker V1 (later superseded because of TOCTOU/phantom-row limitations).
4. Stage 04 — Statistical reproducibility and public-corpus leakage checks.

## Phase 2 — Frozen runtime and attribution

5. Stage 05 — Frozen-runtime ablation over the recovered 2,000-case holdout.
6. Stage 06 — Metamorphic semantic attack lab; exposed the matching→all scope-broadening weakness.
7. Stage 07 — Verified Execution Broker V2; transaction-first reference design and randomized fail-closed/rollback testing.
8. Stage 08 — Risk-calibrated selective authorization; retained as exploratory because repeated splits were unstable.

## Phase 3 — Hardening

9. Stage 09 — Anchor Lock v3.
   - 10,248 critical metamorphic attacks.
   - v2 recall about 85.402% before the scope-broadening fix.
   - v3 recall 100% on the retained test suite.
   - zero false positives on 2,000 clean controls.
   - no new trigger on evaluable frozen outputs.

## Phase 4 — External suites and meta-analysis

10. Stage 10 — BFCL / MLCL attempts. No defensible benchmark-native BFCL/MLCL score retained from the original campaign.
11. Stage 11 — AgentDojo / Agent-SafetyBench transfer attempts. No complete official benchmark-level transfer retained from the original campaign.
12. Stage 12 — tau3 stateful transfer; initial runs had runtime/environment failures, later targeted recovery produced only partial external evidence.
13. Stage 13 — unified multi-benchmark meta-analysis, with claim boundaries tied to what external evidence actually existed.
14. Stage 14 — final validation harness.
15. Stage 15 — paper-finisher/build workflow.

## Phase 5 — Recovery / hosted pilot / local closure

The research history retains targeted recovery archives, merged evidence, provider preflights, hosted tau3 quick runs, and local open-weight/T4 workflows. The hosted tau3 pilot contains six benchmark-native trajectories across Qwen and GPT-OSS (one per domain/model for airline/retail/telecom) and is explicitly treated as a small pilot, not full benchmark generalization.

## Phase 6 — Local T4 / open-weight / three-family attempts

The later local notebooks and raw archives preserve Granite/Qwen/other checkpoint preflights, AgentDojo/tau3 partial runs, BFCL timeouts, context-length failures, vLLM compatibility problems, and third-family closure attempts. These results are diagnostic/partial. They do not establish a completed three-independent-family external study.

## Phase 7 — Current manuscripts and submission artifacts

The package includes the current paper lineage and 2026-09-16 submission artifacts, including Frontiers, IEEE, Springer, Elsevier, source ZIPs, figures, reference-audited packages, and prior audited/humanized/reviewer-hardened sources where available.

## Primary frozen headline evidence

- Qwen3.5-122B-A10B-FP8 final decision accuracy: 1997/2000 = 99.85%.
- GPT-OSS-120B final decision accuracy: 1996/2000 = 99.80%.
- Qwen raw unsafe ALLOWs: 80; all 80 intercepted by Anchor Lock in the evaluated frozen composition.
- GPT-OSS raw unsafe ALLOWs: 2; both intercepted by Anchor Lock.
- Final observed unsafe ALLOWs: 0 for both frozen models.
- Frozen-log ablation attributes the Qwen security/accuracy gain primarily to Anchor Lock; clarification recovery is safe only in the intended downstream composition.

These are internal-holdout results. Zero observed unsafe ALLOWs is not a zero-risk guarantee, and the current paper keeps that limitation explicit.
