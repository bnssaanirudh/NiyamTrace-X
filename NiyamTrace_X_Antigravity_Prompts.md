# NiyamTrace-X — Antigravity Completion Prompts

**Repository:** `bnssaanirudh/NiyamTrace-X`  
**Primary objective:** Convert the current research prototype into a paper-consistent, reproducible, end-to-end assurance system without fabricating benchmark results or weakening existing safety boundaries.

## How to use this file

Run the prompts **in order**. Each prompt is designed to be given to Antigravity as a separate task. Do not skip validation prompts. For every task:

- Work on the current `main` branch state unless explicitly creating a feature branch is required.
- Inspect the repository before editing.
- Never invent benchmark numbers, successful runs, passing tests, or paper claims.
- Preserve existing frozen research artifacts.
- Do not rewrite or delete historical experiment evidence unless a prompt explicitly asks for archival cleanup.
- Prefer additive, testable changes.
- After implementation, run the relevant tests and report exact pass/fail counts.
- If a benchmark cannot run because of hardware, credentials, package incompatibility, timeout, context length, or rate limits, record it as an **infrastructure failure**, not a model result.
- Keep the scientific claim boundary explicit: internal authorization evidence, external semantic evidence, benchmark-harness evidence, and production-mediation evidence are different categories.

---

# Prompt 1 — Establish a Canonical Repository Baseline

You are working on the repository `bnssaanirudh/NiyamTrace-X`.

Before changing code, perform a complete repository baseline audit.

Tasks:

1. Inspect:
   - `README.md`
   - `.github/workflows/ci.yml`
   - `niyamtrace/apps/gateway/main.py`
   - `niyamtrace/apps/gateway/pipeline.py`
   - `niyamtrace/packages/gate/`
   - `niyamtrace/packages/auth/`
   - `niyamtrace/packages/tools/`
   - `niyamtrace/packages/evidence/`
   - `niyamtrace/tests/`
   - current research-status markdown files
   - current result/evidence checklists
2. Identify:
   - duplicate implementations,
   - stale comments,
   - stale documentation links,
   - mismatches between README claims and retained evidence,
   - paths that are historical copies rather than canonical runtime code,
   - currently failing CI stages.
3. Produce `docs/CANONICAL_RUNTIME_BASELINE.md` containing:
   - canonical code paths,
   - canonical policy file,
   - canonical benchmark/result sources,
   - historical-only paths,
   - current known limitations,
   - exact current commit SHA,
   - CI status.
4. Do not change behavior yet.
5. Do not delete any evidence.
6. Finish with a concise “baseline verdict” stating what is actually implemented and what remains research-only.

Acceptance criteria:
- No functional source code changes.
- New baseline document exists.
- Every claim in the document is backed by an inspected path.
- No benchmark number is copied unless its provenance file is identified.

---

# Prompt 2 — Fix CI and Make the Repository Green

The latest NiyamTrace-X CI run is blocked at lint and therefore skips tests and benchmarks.

Make the repository CI-clean without changing runtime semantics.

Tasks:

1. Run Ruff on the canonical `niyamtrace/` codebase.
2. Fix:
   - unused imports,
   - unsorted imports,
   - formatting problems,
   - trivial lint violations,
   - dead variables where safe.
3. Do not use unsafe auto-fixes unless you inspect each resulting semantic change.
4. Run:
   - unit tests,
   - integration tests,
   - regression tests,
   - replay tests,
   - security tests.
5. Update `.github/workflows/ci.yml` so `tests/security/` is executed.
6. Preserve benchmark execution after test success.
7. Add a CI artifact containing:
   - pytest summary,
   - Ruff summary,
   - benchmark summary if it runs.
8. If tests reveal real behavioral defects, fix them rather than weakening assertions.
9. Do not change thresholds merely to force green CI.

Acceptance criteria:
- `ruff check .` passes inside `niyamtrace/`.
- All locally runnable tests pass.
- `tests/security/` is included in CI.
- Existing scientific outputs are unchanged.
- Report exact number of tests passed, failed, skipped, and xfailed.

---

# Prompt 3 — Correct Authentication Context Propagation

The gateway currently reduces the authenticated principal to one arbitrary role before passing context into the pipeline. This is not sufficient for robust authorization.

Refactor authentication context handling.

Tasks:

1. Inspect `packages/auth/models.py`, JWT verification, gateway request handling, pipeline request objects, and policy evaluation.
2. Change the pipeline so the full authenticated principal is available during authorization:
   - subject,
   - tenant_id,
   - all roles,
   - all scopes.
3. Do not select a role using `next(iter(principal.roles))`.
4. Add a stable authorization-context model if necessary.
5. Preserve a deterministic primary display role only for logging/UI if needed, but do not use it as the authorization source.
6. Ensure caller-supplied request text cannot override authenticated identity, roles, scopes, or tenant.
7. Add tests proving:
   - forged request fields cannot change actor identity,
   - multiple roles are preserved,
   - empty-role users fail closed where appropriate,
   - tenant information reaches the gate,
   - scopes reach the gate.

Acceptance criteria:
- Full principal context reaches authorization.
- No security decision depends on arbitrary frozenset iteration order.
- Existing valid requests remain functional.
- New tests cover principal propagation.

---

# Prompt 4 — Implement Real RBAC, Scope, and Tenant Checks in NiyamGate

The current gate checks target identity, temporal bounds, attributes, cardinality, and evidence, but role/scope/tenant enforcement must be explicit and testable.

Implement authorization-context checks as first-class gate checks.

Required checks:

1. `actor_role_authorization`
   - action/tool must be allowed for at least one authenticated role.
2. `scope_authorization`
   - required action scopes must be present.
3. `tenant_isolation`
   - protected resource tenant must match authenticated principal tenant unless policy explicitly allows cross-tenant administration.
4. Existing target/entity containment remains separate.

Requirements:

- Add machine-readable reason codes:
  - `ROLE_NOT_PERMITTED`
  - `SCOPE_NOT_PERMITTED`
  - `TENANT_BOUNDARY_VIOLATION`
- Do not reuse unrelated errors such as `SELECTOR_MISSING_VENDOR_ID`.
- Update policy configuration so tool permissions are explicit.
- Ensure authorization checks apply consistently to:
  - `archive_invoices`
  - `block_user_access`
  - `update_credit_limit`
  - `suspend_vendor`
- Fix the existing unauthorized-role regression test so it asserts the exact reason code.
- Add positive and negative tests for each tool.

Acceptance criteria:
- An unauthorized role is blocked for the correct reason.
- A missing scope is blocked for the correct reason.
- Cross-tenant access is blocked.
- Authorized same-tenant cases still pass.
- Tests cannot pass accidentally due to another unrelated gate failure.

---

# Prompt 5 — Refactor Target-Identity Containment to Be Tool-Aware

`check_target_identity_containment()` must not assume every tool uses `VENDOR_ID`.

Redesign target containment around tool capability metadata.

Tasks:

1. Inspect all registered tools and their argument schemas.
2. Define per-tool identity selectors, for example:
   - invoices → `vendor_id`
   - user access → `user_id`
   - credit limit → `vendor_id`
   - vendor suspension → `vendor_id`
3. Move target-containment configuration into the policy/tool capability layer rather than hard-coded intent-specific branching.
4. Validate:
   - tool arguments,
   - contract slots,
   - predicted record identities.
5. Fail closed when the contract does not contain required target identity.
6. Add tests for mismatched target IDs for every executable tool.
7. Add tests for multi-entity actions if supported.
8. Preserve existing reason codes where they are semantically correct, but introduce tool-generic codes if needed.

Acceptance criteria:
- `block_user_access` does not fail because a `VENDOR_ID` is absent.
- Identity checks are correct for all executable tools.
- The gate can explain exactly which identity field mismatched.

---

# Prompt 6 — Repair Multi-Tool Simulation and Authorization Semantics

The pipeline currently aggregates all simulated deltas and may evaluate each individual tool call against the combined delta.

Refactor multi-tool handling.

Required architecture:

For each proposed tool call `t_i`:

1. Validate schema.
2. Simulate separately:
   `predicted_delta_i = simulate(t_i)`
3. Gate separately:
   `decision_i = gate(contract, t_i, predicted_delta_i, principal, evidence)`
4. Store per-tool authorization artifacts.

Then:

5. Compute a composition-level combined delta only after all individual tool checks.
6. Run composition checks for:
   - total cardinality,
   - cross-tool conflicts,
   - duplicate target mutation,
   - incompatible state transitions,
   - policy limits across the full request.
7. If any individual call or composition check fails, execute nothing.
8. Trace every per-tool and composition decision.

Add tests for:
- two valid independent tools,
- one valid + one invalid tool,
- conflicting mutations,
- duplicate target mutation,
- total request cardinality exceeding policy,
- multi-tool rollback behavior.

Acceptance criteria:
- No individual tool is evaluated using an unrelated tool's delta.
- Composition policy is explicit.
- Partial execution cannot occur when one tool fails authorization.

---

# Prompt 7 — Make Tool Execution Transactional and Atomic

Current tool implementations may commit individually. That can create partial effects in a multi-tool request.

Refactor execution so the broker owns the transaction.

Tasks:

1. Remove direct `conn.commit()` responsibility from individual tool implementations.
2. Tools should:
   - simulate,
   - apply mutations to an already-open transaction,
   - return actual delta,
   - never independently commit.
3. Create a transaction boundary covering the entire approved request.
4. On any failure:
   - rollback all mutations,
   - record failure reason,
   - emit no success result.
5. Add crash/failure injection tests after:
   - first tool,
   - intermediate tool,
   - before commit.
6. Verify that all states return to pre-request values after rollback.

Acceptance criteria:
- All-or-nothing execution.
- No direct tool-level commit.
- Transaction tests prove rollback correctness.
- Single-tool requests still work.

---

# Prompt 8 — Integrate Verified Execution Broker V2 Into the Canonical Runtime

There is already strong research evidence for a transaction-first Verified Execution Broker V2, but it is not yet the non-bypassable production path.

Integrate its principles into canonical runtime code.

Required flow:

1. Receive a gate-approved execution capability.
2. Begin write transaction **before final state validation**.
3. Verify:
   - certificate integrity,
   - actor identity,
   - tenant,
   - roles/scopes,
   - tool identity,
   - canonical argument hash,
   - authorized targets,
   - authorized fields,
   - policy hash,
   - evidence hash/reference,
   - expected state snapshot/version,
   - expiry,
   - nonce.
4. Recompute current effect inside transaction.
5. Compare current predicted effect to the authorized effect.
6. Execute mutation.
7. Compute actual delta.
8. Require:
   `actual_delta == authorized_predicted_delta`
   or fail closed and rollback.
9. Persist nonce consumption atomically with commit.
10. Commit only after every check passes.

Important:
- Do not simply copy notebook code blindly.
- Adapt the verified broker concept into production-quality canonical modules.
- Keep reference experiment code intact for provenance.

Acceptance criteria:
- Canonical runtime uses the broker for every mutation.
- Direct executor invocation is no longer a valid commit path.
- Replays fail.
- stale snapshot fails.
- policy change fails.
- argument tampering fails.
- target tampering fails.
- actor/tool mismatch fails.
- crash-before-commit rolls back.

---

# Prompt 9 — Make EffectCertificate Production-Meaningful

The current `EffectCertificate` contains placeholders and is not fully bound to execution.

Redesign it as a real authorization-to-commit artifact.

Certificate must bind at least:

- trace_id
- request/task id
- authenticated subject
- tenant_id
- roles/scopes hash or normalized representation
- action/intent
- tool name
- canonical tool arguments hash
- authorized target IDs
- authorized fields
- predicted delta hash
- state snapshot/version
- policy bundle hash
- evidence provenance hash
- issued_at
- expires_at
- nonce
- certificate version

Requirements:

1. Canonical serialization.
2. Deterministic hash/signature.
3. `seal()` and `verify()` must cover all security-sensitive fields.
4. Any post-seal mutation must invalidate verification.
5. Certificate verification must occur inside the transaction-first broker.
6. Nonce must be single-use.
7. Add comprehensive tamper tests for every bound field.
8. Remove placeholder values like:
   - `"DEFAULT-POLICY"`
   - `"evidence-1"`
   - fake before/after hashes.

Acceptance criteria:
- Certificate contains real runtime provenance.
- Tampering any protected field fails verification.
- Broker rejects unsigned/unsealed certificates.
- Replay is rejected.

---

# Prompt 10 — Reconcile Evidence Retrieval and Paper Claims

The runtime now appears to include an `EvidenceRetriever` and deterministic NLI path, but documentation/comments still describe the evidence path as a stub in places.

Audit and reconcile this.

Tasks:

1. Trace the evidence flow from request to gate.
2. Determine exactly:
   - what retrieval corpus is used,
   - what ACL checks are enforced,
   - how evidence is ranked,
   - how the NLI verdict is produced,
   - what failure modes exist,
   - whether the evidence decision is security-critical.
3. Remove stale “always SUPPORT” comments if no longer true.
4. Preserve an explicit test-only stub path if needed, but make it impossible to confuse with production mode.
5. Add tests for:
   - SUPPORT,
   - CONTRADICT,
   - INSUFFICIENT,
   - no accessible evidence,
   - poisoned evidence,
   - role-restricted evidence,
   - cross-tenant evidence.
6. Update:
   - README,
   - architecture documentation,
   - implementation status,
   - paper implementation-boundary notes.
7. Do not claim learned NLI if the implementation is deterministic/rule-based.

Acceptance criteria:
- Documentation matches code.
- Production mode cannot silently fall back to unconditional SUPPORT.
- Evidence provenance is carried into the EffectCertificate.

---

# Prompt 11 — Harden Retrieval Against Prompt Injection and Poisoning

Strengthen the evidence subsystem.

Threats to test:

- malicious instructions inside retrieved documents,
- hidden override text,
- poisoned policy snippets,
- conflicting evidence,
- role-inaccessible content,
- stale policy evidence,
- duplicate adversarial chunks,
- Unicode/control-character tricks.

Requirements:

1. Treat retrieved content as **data**, never executable instructions.
2. Add provenance and trust metadata per chunk.
3. Add policy-document allowlisting or signed bundle provenance where appropriate.
4. Require security-relevant policy decisions to come from trusted policy sources.
5. Make retrieved evidence unable to override authenticated principal information.
6. Add security tests with explicit expected outcomes.
7. Record poisoning detection/failure reasons in trace events.

Acceptance criteria:
- Prompt injection inside retrieved evidence cannot grant authority.
- Untrusted evidence cannot override trusted policy.
- Tests cover the attack cases above.

---

# Prompt 12 — Clean and Normalize Policy Architecture

The repository contains more than one apparent policy compiler/loader path.

Perform a policy architecture cleanup.

Tasks:

1. Identify:
   - canonical policy loader,
   - canonical compiler,
   - legacy duplicate policy compiler(s),
   - canonical YAML policy.
2. Choose one production path.
3. Migrate all callers.
4. Deprecate or remove duplicate code only when safe.
5. Ensure policy hash is derived from canonical normalized policy content.
6. Add schema validation for policy YAML.
7. Fail closed on invalid/missing production policy.
8. Do not silently fall back to permissive defaults in production mode.
9. Add policy-version and policy-hash trace fields.

Acceptance criteria:
- One canonical policy-loading path.
- Invalid policy cannot silently produce a permissive runtime.
- Policy hash is stable and reproducible.
- Tests cover malformed, missing, stale, and changed policies.

---

# Prompt 13 — Add End-to-End Security Regression Suite

Create a focused end-to-end suite testing the complete canonical path:

`authenticated request → semantic contract → evidence → simulation → gate → certificate → broker → commit`

Add cases for:

- valid authorized request,
- wrong entity,
- wrong tenant,
- unauthorized role,
- missing scope,
- temporal widening,
- matching→all scope widening,
- negation loss,
- unauthorized field mutation,
- cardinality threshold,
- insufficient evidence,
- contradictory evidence,
- certificate tampering,
- stale state,
- replay,
- changed policy,
- altered tool arguments after authorization,
- direct executor bypass,
- multi-tool partial-failure rollback,
- prompt injection in retrieved evidence.

Requirements:

- Each test must assert exact reason code.
- Security tests should fail closed.
- Tests should verify database state after rejected requests.
- Add these tests to CI.

Acceptance criteria:
- Direct execution bypass test fails because bypass is impossible.
- Every blocked request leaves external state unchanged.
- Every allowed request produces an auditable trace and valid certificate.

---

# Prompt 14 — Build a Canonical Reproducibility Manifest

Create a machine-readable provenance manifest for the final paper.

Produce:

`provenance/FINAL_REPRODUCIBILITY_MANIFEST.json`

Include:

- git commit SHA,
- policy hash,
- tool registry hash,
- dataset version/hash,
- frozen holdout hash,
- model identifiers and revisions,
- runtime configuration,
- random seeds,
- environment/package lock hash,
- raw result files,
- derived table files,
- figure files,
- statistical-analysis scripts,
- external benchmark result files,
- known failed/incomplete runs,
- manuscript source revision.

Also produce:

`provenance/FINAL_REPRODUCIBILITY_MANIFEST.md`

explaining how every major table/figure can be regenerated.

Acceptance criteria:
- No table value exists only in prose.
- Every headline metric maps to raw evidence.
- Failed benchmark runs are explicitly marked as failure/incomplete, not dropped silently.

---

# Prompt 15 — Direct τ³ Integration: Guarded vs Unguarded

This is a publication-critical experiment.

Integrate NiyamTrace-X directly into the τ³/tau-bench style stateful environment so proposed effectful actions pass through the canonical authorization path before environment mutation.

Design paired evaluation:

### Condition A — Unguarded
Agent interacts with benchmark environment normally.

### Condition B — NiyamTrace-X guarded
Same task/model/seed, but every effectful tool call passes through:

`semantic contract → evidence/policy → simulation → NiyamGate → EffectCertificate → Verified Execution Broker → environment`

Metrics:

- native task reward,
- task success,
- unsafe authorization rate,
- blocked unsafe-action count,
- false-block rate,
- clarification/escalation rate,
- tool-call count,
- latency overhead,
- rollback/fail-closed rate,
- divergence between predicted and actual effect,
- security failures by category.

Requirements:

- Same tasks and seeds for paired comparison.
- Do not classify environment/infrastructure failures as model failures.
- Start with a small smoke run.
- Expand only when the integration is stable.
- Save case-level JSONL/CSV.
- Save model/config provenance.
- Do not claim benchmark-level generalization from a tiny pilot.

Acceptance criteria:
- Benchmark actions actually pass through NiyamTrace-X.
- At least one reproducible guarded/unguarded paired run works end-to-end.
- Raw traces are retained.

---

# Prompt 16 — Expand τ³ Across Independent Model Families

After Prompt 15 works reliably, extend the paired evaluation to at least three genuinely independent model families.

Use only models that are actually available in the environment.

Requirements:

1. Verify family independence and exact model revision.
2. Keep decoding settings fixed where possible.
3. Use identical task subsets across models.
4. Record:
   - completed cases,
   - failures,
   - timeouts,
   - context errors,
   - infrastructure errors.
5. Do not replace failed third-family runs with invented numbers.
6. Report model-family results separately before pooled summaries.
7. Use bootstrap confidence intervals over tasks when sample size is adequate.
8. Use paired analysis for guarded vs unguarded outcomes.

Target output:
- `results/external_tau3_guarded/`
- `results/external_tau3_guarded/per_case.csv`
- `results/external_tau3_guarded/summary.csv`
- `results/external_tau3_guarded/failures.csv`
- `results/external_tau3_guarded/provenance.json`

Acceptance criteria:
- At least three independent families complete a defensible task set, or the repository explicitly records why that target remains incomplete.

---

# Prompt 17 — Direct AgentDojo Integration

Integrate NiyamTrace-X into AgentDojo so effectful actions are mediated rather than merely evaluated beside the benchmark.

Priority threat:
**prompt injection and malicious tool-use redirection**

Paired conditions:

- unguarded agent,
- NiyamTrace-X guarded agent.

Record:

- benchmark utility/success,
- attack success,
- unsafe authorization,
- unsafe action prevented,
- false block,
- escalation/clarification,
- attack type,
- policy reason,
- semantic failure type,
- latency.

Requirements:

- Preserve AgentDojo-native scoring.
- Add NiyamTrace-specific safety metrics separately.
- Route each proposed action through the canonical production gate/broker.
- Never convert a harness failure into a NiyamTrace safety success.
- Save all raw traces.

Acceptance criteria:
- The guarded condition truly mediates benchmark actions.
- At least one full suite/domain completes before expanding.
- Report attack success and utility together.

---

# Prompt 18 — BFCL as Compatibility, Not Core Safety Evidence

Run BFCL only after the canonical tool interface is stable.

Purpose:
measure function/tool-call compatibility, not claim NiyamTrace-X security from BFCL alone.

Tasks:

1. Fix prior timeout/runtime issues if possible.
2. Run official/native scoring.
3. Record:
   - valid score,
   - tool-call formatting failures,
   - timeout rate,
   - unsupported-call rate.
4. Optionally pass BFCL-produced calls through NiyamTrace-X where meaningful, but keep:
   - BFCL function-call correctness
   separate from
   - NiyamTrace authorization safety.
5. Store failed runs.

Acceptance criteria:
- No synthetic substitute is called “BFCL score”.
- If no official score is produced, status remains `MISSING` or `INFRA_FAILURE`.

---

# Prompt 19 — Build a Human-Written Multilingual Authorization Benchmark

The existing 2,000-case benchmark is controlled and generator-derived. Create a smaller independent human-written benchmark.

Target languages/surfaces:

- English
- Hindi / Romanized Hindi
- Telugu script
- Romanized Telugu
- code-switched forms where natural

Target example count:
Start with 200–500 carefully annotated cases rather than maximizing quantity.

Each case must contain:

- natural request,
- language,
- intended action,
- plausible interpretations,
- critical slots,
- authenticated authorization context,
- expected authorization decision,
- allowed effect set,
- unsafe alternative effects,
- ambiguity label,
- annotator notes.

Process:

1. Define annotation guide first.
2. Do not auto-generate all examples from the same templates.
3. Use independent/manual writing wherever possible.
4. Add dual review for security-critical labels if feasible.
5. Measure inter-annotator agreement if multiple annotators are available.
6. Keep this benchmark separate from training/tuning.
7. Run frozen NiyamTrace-X without changing thresholds after seeing the test labels.

Acceptance criteria:
- Clear train/dev/test separation if any tuning occurs.
- Human-written test set remains untouched by model/policy tuning.
- Results are reported separately from the 2,000-case synthetic holdout.

---

# Prompt 20 — Re-run the Core Internal Study on the Final Runtime

After the canonical runtime is hardened, perform a controlled non-regression study.

Important:
Do not overwrite the historical v2 frozen experiment.

Create a **new final-runtime study**.

Compare:

- historical frozen v2,
- final canonical runtime.

Measure:

- decision accuracy,
- unsafe ALLOW,
- false block,
- clarification rate,
- escalation rate,
- semantic accuracy,
- runtime errors,
- latency,
- certificate failures,
- broker failures,
- predicted-vs-actual delta fidelity.

Use the same frozen 2,000 cases if technically valid, clearly labeling this as a post-hoc runtime replay/non-regression study.

Acceptance criteria:
- Historical numbers remain preserved.
- New numbers use a new experiment identifier.
- Differences are explained, not hidden.

---

# Prompt 21 — Re-run Verified Execution Broker Validation Through Production Code

The old 1,320-scenario VEB V2 experiment tested a reference implementation.

Recreate those scenario classes against the **actual integrated canonical broker**.

Scenario families should include at least:

- valid execution,
- argument tampering,
- certificate/signature tampering,
- policy change,
- predicted-target tampering,
- replay,
- stale snapshot,
- expiry,
- actor mismatch,
- tool mismatch,
- crash before commit,
- phantom-row/state race,
- multi-tool partial failure.

Run randomized repetitions comparable to the earlier 1,320-case study.

Store:

- per-case input,
- expected outcome,
- actual outcome,
- commit/rollback state,
- reason code,
- database pre/post hashes,
- seed.

Acceptance criteria:
- The production broker matches or improves the reference broker's fail-closed behavior.
- Any failure is retained and analyzed.
- Do not claim “1,320/1,320” unless the production code actually achieves it.

---

# Prompt 22 — Statistical Analysis Package

Create one reproducible statistical analysis pipeline consuming only frozen CSV/JSON artifacts.

Include:

- exact accuracy,
- unsafe-ALLOW rate,
- false-block rate,
- Wilson/Clopper-Pearson intervals where suitable,
- grouped/bootstrap intervals for semantic-group dependence,
- paired McNemar tests,
- paired guarded-vs-unguarded task analysis,
- bootstrap confidence intervals,
- family-level breakdown,
- language-level breakdown,
- attack-category breakdown,
- latency distribution,
- failure-category analysis.

Rules:

- Do not treat four translations of one semantic group as independent when estimating group-level uncertainty.
- Do not pool unrelated benchmark tasks without explanation.
- Do not use significance tests when sample size is clearly inadequate.
- Report zero events as “zero observed”, not zero underlying risk.

Outputs:

- `analysis/final_statistics.py`
- `results/final_statistics/*.csv`
- publication-ready tables
- publication-ready figures
- `analysis/STATISTICAL_METHODS.md`

Acceptance criteria:
- Running one command regenerates final result tables from raw retained evidence.

---

# Prompt 23 — Repository Claim Audit

Perform a claim-by-claim audit of all public-facing text.

Inspect:

- README,
- docs,
- manuscript sources,
- result summaries,
- project reports,
- comments that describe implementation status.

Build:

`provenance/CLAIM_EVIDENCE_MATRIX_FINAL.csv`

Columns:

- claim_id
- exact_claim
- location
- evidence_state
- supporting_file
- supporting_experiment
- commit
- allowed_wording
- prohibited_overclaim
- notes

Evidence states:

- `SUPPORTED`
- `PARTIAL`
- `DIAGNOSTIC_ONLY`
- `INFRA_FAILURE`
- `MISSING`
- `SUPERSEDED`

Fix statements such as “comprehensive BFCL/AgentDojo/τ³ benchmarking” unless supported by completed retained evidence.

Acceptance criteria:
- Every headline README/paper claim has a provenance entry.
- Unsupported claims are softened or removed.
- Historical failed work remains documented.

---

# Prompt 24 — Repository Cleanup Without Losing Research Provenance

The repository contains large duplicated snapshots and historical copies.

Clean organization carefully.

Goals:

1. Keep one obvious canonical source tree.
2. Preserve frozen evidence.
3. Preserve historical notebooks needed for provenance.
4. Move redundant copies into clearly labeled archival structure if safe.
5. Add:
   - `CANONICAL_PATHS.md`
   - `ARTIFACT_INDEX.md`
6. Remove broken documentation links.
7. Do not delete unique raw evidence.
8. Do not rewrite git history.
9. Consider Git LFS only if appropriate and supported; do not break existing artifact access.

Suggested structure:

```text
niyamtrace/                 # canonical runtime
tests/ or niyamtrace/tests/ # canonical tests
experiments/                # canonical reproducible experiments
results/
  frozen_internal/
  anchor_v3/
  broker/
  external/
provenance/
paper/
archive/
```

Acceptance criteria:
- A reviewer can find canonical code, raw results, analysis, and paper artifacts quickly.
- Duplicate artifact provenance remains traceable.

---

# Prompt 25 — Final Paper/Code Consistency Audit

After all technical and experimental work is complete, perform a final paper-code alignment audit.

Compare every manuscript implementation claim against the final runtime.

Verify:

- authentication path,
- RBAC,
- scopes,
- tenant isolation,
- semantic authorization,
- evidence retrieval,
- policy checks,
- simulation,
- per-tool authorization,
- composition authorization,
- EffectCertificate,
- transaction-first broker,
- replay resistance,
- stale-state handling,
- rollback,
- actual-vs-predicted effect check,
- complete mediation boundary,
- external benchmark integration.

Create:

`paper/FINAL_CODE_PAPER_AUDIT.md`

For every mismatch:
- either fix the code,
- or narrow the manuscript claim.

Never broaden a claim just because the intended design exists.

Acceptance criteria:
- No known contradiction remains between paper and canonical runtime.
- Limitations section accurately reflects unresolved items.

---

# Prompt 26 — Generate Final Submission Evidence Package

Create a final submission-ready evidence bundle.

Required folders/files:

```text
submission_evidence/
  README.md
  provenance_manifest.json
  claim_evidence_matrix.csv
  environment.txt
  commit.txt
  policy_hash.txt
  tool_registry_hash.txt
  internal_results/
  anchor_v3/
  broker/
  external_tau3/
  external_agentdojo/
  bfcl/
  massive_mtop/
  statistical_analysis/
  ci/
  failures/
```

Requirements:

- Copy or reference canonical artifacts only.
- Keep infrastructure failures.
- Include checksums for every file.
- Generate a top-level manifest.
- Ensure no secret, API key, token, credential, or private personal data is included.
- Verify archive extraction works.
- Produce one ZIP.

Acceptance criteria:
- Another researcher can understand what evidence supports each major claim without browsing the entire development repository.

---

# Prompt 27 — Final Q1 Reviewer Simulation

Act as three independent reviewers of the final NiyamTrace-X paper and repository:

### Reviewer A — LLM Agent Security
Focus on:
- novelty,
- threat model,
- prompt injection,
- unsafe authorization,
- comparison to agent-security literature.

### Reviewer B — Systems Security
Focus on:
- complete mediation,
- TOCTOU,
- capabilities,
- transaction semantics,
- replay,
- rollback,
- tenant isolation,
- provenance.

### Reviewer C — Empirical ML / NLP
Focus on:
- internal vs external validity,
- multilingual generalization,
- benchmark construction,
- leakage,
- statistics,
- ablations,
- model-family diversity.

For each reviewer provide:

- 5 strongest aspects,
- 10 major concerns,
- 10 minor concerns,
- likely acceptance/rejection reason,
- exact changes required.

Then produce a prioritized rebuttal/fix plan.

Do not defend unsupported claims. Treat criticism as a search for genuine weaknesses.

---

# Prompt 28 — Final Readiness Decision

Perform a final go/no-go audit.

Score 0–100:

- novelty,
- technical correctness,
- implementation completeness,
- security boundary,
- empirical evidence,
- external validity,
- statistical rigor,
- reproducibility,
- repository quality,
- manuscript consistency.

Then classify every remaining issue as:

- `BLOCKER`
- `MAJOR`
- `MINOR`
- `OPTIONAL_EXTENSION`

A submission is **GO** only if:

- canonical CI is green,
- security tests pass,
- direct executor bypass is closed,
- role/scope/tenant checks are explicit,
- transaction-first broker is integrated,
- claim/evidence matrix has no unsupported headline claim,
- manuscript limitations match actual system state,
- at least one true direct external guarded evaluation has completed.

If those conditions are not met, return **NO-GO** and identify the minimum fixes required.

---

# Recommended execution order

Use this order:

```text
1  Baseline audit
2  CI cleanup
3  Principal propagation
4  RBAC/scope/tenant
5  Tool-aware target containment
6  Multi-tool authorization
7  Atomic transactions
8  Broker integration
9  EffectCertificate
10 Evidence reconciliation
11 Retrieval security
12 Policy architecture
13 End-to-end security tests
14 Reproducibility manifest
15 Direct τ³ integration
16 Multi-family τ³
17 Direct AgentDojo
18 BFCL
19 Human multilingual benchmark
20 Final-runtime internal replay
21 Production-broker randomized study
22 Statistical pipeline
23 Claim audit
24 Repo cleanup
25 Paper/code consistency
26 Evidence ZIP
27 Reviewer simulation
28 Final GO/NO-GO
```

---

# Expected final research position

The final paper should support only claims that are directly evidenced.

A strong final framing is:

> NiyamTrace-X preserves security-relevant semantic uncertainty through authorization, restricts execution to effects compatible with the surviving interpretations and authenticated policy, and binds approved effects to a transaction-first execution path. Internal multilingual evaluation, adversarial metamorphic testing, direct guarded external-agent evaluation, and execution-boundary validation are reported separately so that semantic robustness, agent utility, and systems-security guarantees are not conflated.

Do **not** claim universal agent safety, perfect multilingual understanding, zero underlying failure probability, or production security beyond what the final integrated runtime and retained evidence demonstrate.
