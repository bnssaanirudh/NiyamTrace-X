# NiyamTrace-X Current Research Status — 2026-09-16

## Strongly supported by retained evidence

- Frozen 2,000-case multilingual internal evaluation for Qwen3.5-122B and GPT-OSS-120B.
- Frozen runtime source and recovered raw per-case evidence.
- Frozen-log ablation separating base, Anchor Lock, clarification recovery, and full composition.
- Anchor Lock v3 post-freeze metamorphic hardening on 10,248 critical attacks plus clean controls.
- Verified Execution Broker V2 as an isolated/reference transaction-first design with 1,320 randomized scenarios.
- Group-clustered bootstrap and exact interval/statistical recomputation.
- Current paper/source/build lineage and evidence audits.

## Partial / diagnostic evidence

- Hosted tau3 QUICK pilot: six trajectories across Qwen and GPT-OSS; useful external signal but far too small for a broad benchmark claim.
- Local T4/open-weight AgentDojo/tau3 runs: partial/diagnostic because of context limits, timeouts, and checkpoint/runtime compatibility issues.
- Three-family closure attempts: retained for reproducibility and debugging, but did not complete a defensible three-independent-family study.

## Not established

- Full BFCL benchmark generalization.
- Full AgentDojo benchmark generalization.
- Agent-SafetyBench/MLCL broad transfer.
- >=3 independent model-family external generalization.
- Production-grade complete mediation / non-bypassable execution path.

## Important system boundary

Verified Execution Broker V2 is evidence for a reference execution design, not proof that the current public runtime has complete non-bypassable mediation. The public/legacy executor integration remains a systems-engineering gap and should not be described as solved unless a later repository change and corresponding integration test demonstrate it.
