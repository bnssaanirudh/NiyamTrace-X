# NiyamTrace-X — Results merged with targeted recovery evidence

## Newly added evidence

The uploaded targeted-recovery package contributes **6 valid τ³ QUICK trajectories**:

| Model | Airline | Retail | Telecom | Mean |
|---|---:|---:|---:|---:|
| Qwen | 1.0 | 0.0 | 0.0 | 0.333 |
| GPT-OSS | 1.0 | 1.0 | 0.0 | 0.667 |

Overall QUICK reward across these six trajectories: **0.500**.

These are benchmark-native τ³ rewards and are preserved in the merged result set.
However, this is **PARTIAL external evidence**, not a completed τ³ generalization claim:
only one task per domain/model was evaluated and only Qwen and GPT-OSS completed.

## Evidence-state changes

- Frozen multilingual internal effectiveness: **SUPPORTED**.
- Anchor Lock V3 hardening: **SUPPORTED**.
- τ³ stateful external transfer: **PARTIAL** (previously MISSING).
- BFCL-v4: **MISSING**.
- AgentDojo: **MISSING**.
- GLM τ³ recovery: **INFRA_FAILURE**.
- External validation across ≥3 independent model families: **MISSING**.

## Important recovery context

The recovery preflight shows HTTP 402 provider-budget failures for Qwen, GPT-OSS and GLM.
AgentDojo recovery therefore produced no valid scored cases.
GLM τ³ recovery produced zero evaluated trajectories.
Those failed attempts are retained in the package for provenance but are not counted as evidence.

## Files

- `merged/merged_unified_evidence.csv` — old supported evidence plus the six recovered τ³ rows.
- `merged/tau3_recovered_quick_results.csv` — domain/model τ³ summary.
- `merged/updated_claim_evidence_checklist.csv` — claim states after this merge.
- `merged/recovery_failures_retained.csv` — failed recovery attempts retained for audit.
- `master_original/` — unmodified prior master results.
- `recovery_addition/` — unmodified uploaded recovery package/results.
