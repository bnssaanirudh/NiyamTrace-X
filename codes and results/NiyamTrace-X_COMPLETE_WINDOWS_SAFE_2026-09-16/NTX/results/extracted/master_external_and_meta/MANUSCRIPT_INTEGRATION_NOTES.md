# NiyamTrace-X manuscript integration notes

Only claims marked SUPPORTED below should be promoted into the main paper.

- **SUPPORTED** — Frozen multilingual internal effectiveness (Frozen 2,000-case evidence)
- **SUPPORTED** — Anchor Lock V3 closes the matching→all metamorphic gap (Stage 1)
- **MISSING** — External function-calling generalization on BFCL V4 (Stage 2 official BFCL)
- **MISSING** — Official MLCL multilingual transfer (Stage 2 MLCL gate)
- **MISSING** — Prompt-injection security transfer on AgentDojo (Stage 3 AgentDojo)
- **MISSING** — Agent-SafetyBench official scored transfer (Stage 3 Agent-SafetyBench)
- **MISSING** — Stateful customer-service transfer on τ³ (Stage 4 τ³)
- **MISSING** — External validation across ≥3 model families (Stage 5 coverage)

## Interpretation rules
- Do not merge unlike benchmark metrics into one global accuracy number.
- BFCL effect-relation analysis is a post-hoc NTX-compatible proxy unless a benchmark-specific policy/effect mapper is supplied.
- AgentDojo official security/utility and τ³ official rewards remain benchmark-native metrics.
- Agent-SafetyBench is paper-eligible only after its official scorer completes.
- MLCL is not reconstructed from the paper; use an official/released source only.