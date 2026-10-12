# NiyamTrace-X targeted paper-closure verification (11 October 2026)

## Automated verification performed in this package

- Notebook 15 ran **end to end** on the archived October 11 case-level table, SHA-256 pinned in `evidence/EVIDENCE_PROVENANCE.json`. It checked all 4,320 records, exact pairings, 360 records per variant per primary model, and 48 Granite disagreements.
- Granite: anchors 93.33% vs full 80.00% (360 identical request IDs; 48 anchor-correct/full-incorrect, zero reverse); exact paired McNemar p=7.11e-15. Cluster bootstrap (100 semantic groups, 5,000 draws) estimates full-minus-anchors accuracy gap -13.33 percentage points, with percentile CI around [-17.17,-8.67] pp. This is exploratory uncertainty, not independent natural authorization evidence.
- Qwen: anchors and full 62.78% on the same cohort, no different decisions.
- In this simulated-reference effect harness the anchor/full arms recorded 0 unsafe cases each in 360 observations, implying a nonzero one-sided uncertainty limit; this is not proof of production safety.
- Notebooks 16–18 passed **their no-input/PENDING-mode smoke checks**: native patched-repo security tests remain unexecuted, no human gold labels were invented, and no official gated agent scores were invented. Their code paths that require future source patches, human labels and official benchmark exports were not executed here.

## Current go/no-go

**NO-GO for claiming production authorization enforcement or independent-candidate superiority.** Fix native attacks in source, demonstrate passing post-patch tests with trace/snapshot provenance, independently annotate natural multilingual authorization requests, and run one genuinely official gate-in-path benchmark. Preserve original negative outcomes in the manuscript until reproducible closure. See `engineering/ANTIGRAVITY_PAPER_CLOSURE_PROMPTS.md`.

## Expected workflow

1. Run Notebook 15 immediately (or use the precomputed exported results included in `outputs/`).
2. Open Antigravity on the GitHub repo; paste Prompt A then B. Push a **new branch/PR** (not main) and rerun Notebook 16 with `NTX_RUN_NATIVE_TESTS=1` and `NTX_REPO_REF=<branch>`.
3. Collect de-identified natural cases and two independent consenting fluent annotators. **Freeze split before labels and inference.** Use Notebook 17.
4. Implement ONE official benchmark tool adapter in Antigravity (Prompt D), run real guarded/unguarded paired stateful tasks, and validate outputs with Notebook 18. The audit alone does not run AgentDojo or tau3.
5. Only after results are verified, update source LaTeX and supplement with a case-by-case claim evidence ledger.

## Post-Patch Engineering Verification Status (Branch `paper-closure/native-security-and-benchmarks`)

- **Prompt A & B (Native Security & CI):** Completed and verified.
  - Removed hardcoded production HMAC fallback; strictly required protected deployment secret (`NIYAMTRACE_GATE_SECRET` or secret file), raising `SecurityError` if missing or default.
  - Bound every executor (`ERPExecutor`) and tool invocation (`ToolImplementation.execute()`) to signed arguments, policy, tenant, action, snapshot, and expiration via `verify_tool_authorization_binding`.
  - Replaced process-local nonce tracking with atomic, persistent single-use capability consumption (`ConsumedCapability` table in SQLite/Postgres DB) atomically recorded within the write transaction.
  - Closed direct executor and tool registry bypass vectors.
  - Ambiguous / missing calendar years strictly blocked with `CLARIFY` / `TEMPORAL_AMBIGUOUS_UNANCHORED`.
  - 19 real SQLite regression probes in `tests/security/test_native_mediation_regressions.py` PASS with zero unexpected row mutations.
  - Full test suite passes: 484 passed, 1 skipped.
  - Exported structured evidence to `niyamtrace/artifacts/PRODUCTION_FIX_EVIDENCE.json` with trace SHA-256 and DB pre/post SHA-256 hashes.
  - Notebook 16 audit (`audit_notebook_16.py`) passes with `status: CANDIDATE_REVIEW`, `mandatory_native_probe_status: CANDIDATE_PASS_REQUIRES_INDEPENDENT_REVIEW`, and 0 issues.
- **Prompt C (Granite 48 Failure Investigation):** Completed and verified.
  - Script `niyamtrace/scripts/audit_notebook_15.py` executed against SHA-256 verified `paired_variant_cases.csv`.
  - Confirmed 48 Granite regressions (ALLOW -> CLARIFY due to missing candidate ambiguity), exact McNemar p = 7.11e-15, and 1,000-iteration cluster bootstrap intervals.
  - Exported to `outputs/` (`15_full_cohort_summary.csv`, `15_paired_significance.csv`, `15_regression_case_ids.csv`, `15_cluster_bootstrap.csv`, `15_AUDIT_MANIFEST.json`).
- **Prompt D (Official Benchmark Interceptor):** Completed and hardened.
  - Implemented `niyamtrace/packages/bench/official_adapter.py` providing `OfficialBenchmarkGateInterceptor`.
  - Interceptor routes all tool calls through `NiyamGate.evaluate()`; rejects unauthorized/unanchored mutations before native executor can be invoked.
  - Accurately logged `status: BLOCKED` in `outputs/18_OFFICIAL_GATE_REPORT.json` due to uninstalled external packages (`agentdojo`/`tau_bench`) without fabricating numbers.
