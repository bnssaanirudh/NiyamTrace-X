# NiyamTrace-X — Antigravity + GitHub paper-closure engineering tasks

**Base repo:** https://github.com/bnssaanirudh/NiyamTrace-X
**Audit revision (main on 2026-10-11):** `651e87ef452c80008d4f73c8f2de21321e21fa50`
**Do not edit main directly.** Create `paper-closure/native-security-and-benchmarks`; keep all old experimental archives unchanged.
**One branch/PR with reviewable commits is preferred.** Nothing here establishes that an attack is patched until its native tests pass.

## Instructions for Antigravity — paste each numbered prompt separately

### Prompt A. Mandatory source-native execution mediation (highest priority)

You are working in `bnssaanirudh/NiyamTrace-X`. Inspect these real paths first:
`niyamtrace/packages/gate/executor.py`, `niyamtrace/packages/gate/broker.py`,
`niyamtrace/apps/gateway/pipeline.py`, `niyamtrace/packages/contracts/schema.py`,
`niyamtrace/packages/gate/gate.py`, `niyamtrace/tests/security/test_e2e_broker.py`,
`niyamtrace/tests/integration/test_simulate_execute_atomicity.py`.

Known native attacks against commit `651e87e`: direct executor bypass changed 3 rows; caller-created self-sealed certificate changed 3 rows; natural request "Archive March invoices for vendor 4421" (no explicit year) changed 3 rows. Existing broker code calls `cert.verify()` on an origin-untrusted seal. Existing `ERPExecutor.execute(tool_call)` takes no mandatory authorization capability.

Task: design a single mandatory execution boundary so no accessible write path calls registry tools without a server-issued, context-bound, single-use authorization. Use a trust root not constructible by user input. Check subject, tenant, action, canonical tool+arguments, policy version/hash, snapshot/state binding, expiry, unique nonce/replay, and effect set, and enforce atomic commit/rollback if actual effects exceed authorization. Deny if security-critical calendar year is missing or merely hallucinated; allow explicit defensible relative-year resolution only with logged reference-date semantics and preserved original scope. Ensure legitimate authorized commits still succeed. Identify and close ALL registry/direct executor write paths, including mock/demo endpoints. Don't merely place a wrapper on the gateway while leaving the executor callable.

Add negative tests under `niyamtrace/tests/security/test_native_mediation_regressions.py` using real SQLite and real repository tools: unauthorized direct call; forged/self-issued seal; tampered signature; wrong subject; wrong tenant; wrong action/args; expired; replayed; stale snapshot; revoked policy; ambiguous year; rollback; and positive authorized commit. For each, record before/after database SHA-256, changed row count, source SHA, trace hash, and whether native executor was reached. No mocks of broker/executor in these attacks. Report if any test remains blocked; do not mark it PASSED. Include deterministic fixtures and no network paid keys.

### Prompt B. Reproducible native CI and evidence export

Fix dependency installation and CI around `niyamtrace/pyproject.toml` and root `.github/workflows/ci.yml`; note that `pydantic-settings`, `sqlalchemy[asyncio]`, `greenlet` and pytest native dependencies must install correctly on Python 3.11/3.12. Lock tool/dev dependencies or provide reproducible constraints and logs. Run existing tests plus new native regressions. Do not weaken tests to obtain green CI.

Emit `niyamtrace/artifacts/PRODUCTION_FIX_EVIDENCE.json`, immutable `traces/` and `before_after/` snapshots, runner source and its hash. JSON contract:
`{"repo_commit":"40 lowercase hex","probes":[{"id":"SEC-01_DIRECT_EXECUTOR_MEDIATION","status":"PASS","actual_native_executor":true,"rows_mutated":0,"before_db_sha256":"64 hex","after_db_sha256":"64 hex","trace_sha256":"64 hex"}]}`.
Mandatory ids: SEC-01_DIRECT_EXECUTOR_MEDIATION, SEC-02_CERTIFICATE_ORIGIN_BINDING, SEC-03_MISSING_YEAR, SEC-04_PAIRED_BROKER_POSITIVE, SEC-REPLAY, SEC-STALE_STATE, SEC-WRONG_TENANT, SEC-POLICY_REVOKE. Positive commit must mutate authorized expected rows; negatives mutate zero rows. Bind evidence to Git HEAD, command, fixtures and logs. Commit code and tests; store logs as CI artifacts if too large. Open PR; do not auto-merge.

### Prompt C. Granite 48-case failure investigation and safe ablations

Use frozen `paired_variant_cases.csv` from the accompanying evidence package (SHA pinned in `EVIDENCE_PROVENANCE.json`). The 360-case Granite cohort had anchor accuracy 93.33% vs full 80.00%, 48 regressions, no improvements; all were ALLOW_MATCH or ALLOW_ALL changed to CLARIFY with reason `independent_candidate_missing`. Analyze failure at preferred-model proposal, independent interpretation candidate generation, parser-validity, and discrepancy with gold semantic interpretations. **Do not pass gold labels into runtime.** Compare anchor, full, independently generated candidate sets and oracle upper bound (oracle explicitly diagnostic only). Include false refusal/safe completion and zero-event confidence intervals. Do not modify the frozen results to make full look better. Keep alternate variants exploratory and perform final evaluation on a newly sealed human-adjudicated holdout. Prefer simple anchored mediation if independent candidates remain harmful.

### Prompt D. One official gate-in-path benchmark with stateful tool interception

Choose a single official benchmark first, AgentDojo or tau2/tau3 as compatible with the actual NiyamTrace-X tool domain. Check official version, license, task IDs and score API. Build an adapter where ALL real write calls are intercepted at the registry/broker and enforced by the patched production gate. Run paired gated/ungated tasks with same starting state, same frozen model ID/prompt, model revision, task IDs and official scorer. Log every attempted call, decision, before/after state hashes, auth context, tool effect, task success and unsafe mutations. **If the official benchmark cannot faithfully route actions through NiyamTrace-X's production path, mark unsupported and do not claim an official gated score.** Export `official_gate_in_path_results.csv` with EXACT columns listed in Notebook 18; include native traces, official scorer logs, hashes and failures. Never describe readiness/import tests as official evaluations.

## Required final PR checklist

- Branch with pinned commit; source diff includes native executor AND broker trust-boundary fix.
- Negative real SQLite tests all PASS with 0 unauthorized rows; authorized positive commit still functions.
- Frozen Granite comparison reproduced, 48 regressions disclosed, case-level failure categories included.
- Official task score only if real official scorer+tool hooks run and export contract passes.
- No empty placeholders, demo/synthetic numbers, or smoke fixtures represented as journal evidence.
- Update article and supplementary claims *only after evidence exists*; list all unfinished work honestly.

## What to upload to Colab / GitHub

The entire kit ZIP can be unpacked in Colab. Notebooks 15-18 are in `notebooks/` and original Oct 11 case-level CSV + source hash are in `evidence/`. The first notebook runs without GPU. Set environment variables before Notebook 16 for a patched branch; Notebook 17 requires human raters; Notebook 18 requires the official adapter output. Upload human data only if privacy and participant consent permit. Store large raw evidence in a release/Drive archive and commit checksums + compact tables to GitHub rather than pushing secrets and private respondent texts.
