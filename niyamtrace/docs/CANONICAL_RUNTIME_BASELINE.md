# NiyamTrace-X — Canonical Runtime Baseline

**Generated:** 2026-10-04  
**Commit SHA:** `59dff44ed3afd07b9d41f2760c0575d261b56073`  
**Repository:** `bnssaanirudh/NiyamTrace-X`

---

## 1. Canonical Code Paths

| Component | Canonical Path | Status |
|-----------|---------------|--------|
| Gateway entrypoint | `apps/gateway/main.py` | ✅ Implemented (Week 2) |
| Pipeline orchestrator | `apps/gateway/pipeline.py` | ✅ Implemented (Week 5) |
| NiyamGate evaluator | `packages/gate/gate.py` | ✅ Implemented (Week 2) |
| Gate policy checks | `packages/gate/policy.py` | ✅ Implemented (Week 2) |
| Shadow simulator | `packages/gate/simulator.py` | ✅ Implemented |
| ERP executor | `packages/gate/executor.py` | ✅ Implemented |
| Tool schemas | `packages/gate/tool_schemas.py` | ✅ Implemented |
| Auth models | `packages/auth/models.py` | ✅ Implemented |
| JWT verification | `packages/auth/jwt.py` | ✅ Implemented |
| RBAC helpers | `packages/auth/rbac.py` | ✅ Basic only |
| Contract schema | `packages/contracts/schema.py` | ✅ Implemented |
| Evidence retriever | `packages/evidence/retriever.py` | ✅ Implemented (Week 5) |
| NLI engine | `packages/evidence/nli.py` | ✅ Deterministic rule-based |
| Evidence ACL | `packages/evidence/acl.py` | ✅ Implemented |
| Policy loader | `packages/policy/loader.py` | ✅ Implemented |
| Policy compiler | `packages/policy/compiler.py` | ✅ Implemented |
| Policy models | `packages/policy/models.py` | ✅ Implemented |
| Tool registry | `packages/tools/registry.py` | ✅ Implemented |
| Archive invoices tool | `packages/tools/archive_invoices.py` | ✅ Implemented |
| Dummy tools | `packages/tools/dummy_tools.py` | ⚠️ Stubs for block/suspend/update |
| NLP intake | `packages/nlp/intake.py` | ✅ Implemented (Week 3) |
| NLP compiler | `packages/nlp/compiler.py` | ✅ Implemented (Week 4) |
| NLP normalizer | `packages/nlp/normalizer.py` | ✅ Implemented |
| NLP LLM client | `packages/nlp/llm_client.py` | ⚠️ Offline/mock only |
| Trace lake writer | `packages/lake/writer.py` | ✅ Implemented |
| Session manager | `packages/storage/session.py` | ✅ Implemented |
| Storage models | `packages/storage/models.py` | ✅ Implemented |
| Observability logger | `packages/observability/logger.py` | ✅ Implemented |

---

## 2. Canonical Policy File

**Path:** `policies/reference.yaml`  
**Version:** `1.0.0`  
**Tenant:** `acme`

Policy covers four tools:
- `archive_invoices` — roles: `procurement_manager`, `finance_admin`
- `update_credit_limit` — roles: `finance_admin`, `credit_officer`
- `suspend_vendor` — roles: `admin`, `security_officer`
- `block_user_access` — roles: `it_admin`, `security_officer`

**Policy is loaded deterministically.** Hash is derived from normalized JSON of the validated `PolicyBundle` model.

---

## 3. Canonical Benchmark / Result Sources

| Source | Path | Status |
|--------|------|--------|
| Internal 2000-case holdout | `data/benchmark/` | ✅ Frozen (do not modify) |
| Synthetic ERP seed | `data/synthetic/erp.py` | ✅ Deterministic seed |
| Tau-3 external results (partial) | `../tau3_recovered_quick_results.csv` | ⚠️ Partial/incomplete |
| Merged unified evidence | `../merged_unified_evidence.csv` | ⚠️ Derived artifact |
| Results JSON | `../results.json` | ✅ Retained |

---

## 4. Historical-Only Paths (Not Canonical Runtime)

The following paths exist in the repository for provenance/historical reference and are **not** part of the canonical execution path:

| Path | Reason |
|------|--------|
| `../codes and results/` | Historical experiment notebooks |
| `../experiments/` | Research notebooks (not production) |
| `../amd_session_*.txt` | AMD MI300X session logs |
| `../local_gpu_attempt_v*.zip` | Failed local GPU runs |
| `../NTX_RESULTS_MERGED_WITH_RECOVERY*.zip` | Merged historical results |
| `packages/gate/policy_compiler.py` | **Duplicate compiler** — see Known Limitations |
| `packages/nlp/llm_client.py` | Offline mock; no LLM in current runtime |

---

## 5. Current Known Limitations

1. **Duplicate policy compiler**: `packages/gate/policy_compiler.py` exists alongside the canonical `packages/policy/compiler.py`. The gate's `policy.py` imports from `packages.policy.compiler` (canonical). The gate-local `policy_compiler.py` is a legacy duplicate that should be deprecated (Prompt 12).

2. **Full principal not propagated**: `apps/gateway/main.py` reduces the principal's roles to a single arbitrary role (`next(iter(principal.roles))`) before passing to the pipeline. The gate checks currently use `actor_role` (single string) rather than the full `frozenset[str]` of roles. This means RBAC enforcement depends on arbitrary frozenset iteration order (Prompt 3).

3. **No RBAC gate check**: The gate has 5 checks but none explicitly verifies the authenticated role is allowed to call the tool per policy. R6 regression test expects this but it was not yet implemented at the gate level (Prompt 4).

4. **EffectCertificate placeholders**: The certificate emitted on ALLOW contains mocked values: `"DEFAULT-POLICY"`, `"evidence-1"`, and fake hash strings `"a1b2c3d4"` / `"e5f6g7h8"`. These are not real provenance (Prompt 9).

5. **Multi-tool simulation uses aggregated delta**: In pipeline.py, the combined delta from all tool calls is passed to each individual gate evaluation call — meaning tool_i is evaluated against the union of all tool deltas, not just its own delta (Prompt 6).

6. **Evidence described as stub in comments**: `policy.py` still has stub-labeled comments for Check 5 even though the real NLI is wired in Week 5. Comment cleanup needed (Prompt 10).

7. **Security tests not in CI**: `tests/security/` is not explicitly included in the CI workflow. The CI runs `pytest tests/` which would include it, but it is not separately staged or artifact-uploaded (Prompt 2).

8. **No scope or tenant checks**: There are no gate checks for `scope_authorization` or `tenant_isolation`. These are required for the paper's security claims (Prompt 4).

9. **`block_user_access` identity check uses VENDOR_ID fallback**: The target-identity check in `policy.py` has an intent-specific branch for `access.block` but falls through to the VENDOR_ID logic if the intent string doesn't exactly match (Prompt 5).

10. **No Verified Execution Broker**: The pipeline uses a direct `ERPExecutor` without the transaction-first broker described in Prompts 7–8. Individual tool implementations may commit directly (Prompt 7).

---

## 6. CI Status

**CI workflow file:** `.github/workflows/ci.yml`

Current stages:
1. `actions/checkout@v4`
2. Python 3.11 setup
3. `uv` install
4. `uv pip install --system -e .[dev]`
5. `black --check .` (format check)
6. `flake8 . --count --select=E9,F63,F7,F82` (narrow lint — only fatal errors)
7. `cp .env.example .env`
8. `pytest tests/ -v`

**Issues:**
- CI uses `flake8` not `ruff` — inconsistent with development tooling
- `black` is not in the main dev dependencies (uses `ruff format` instead)
- Security tests are not explicitly staged or artifact-uploaded
- No benchmark execution in CI
- No ruff lint step

---

## 7. Baseline Verdict

### What is actually implemented:

- **Semantic contract extraction**: Real multilingual NLP pipeline using `MultilingualIntake` + `NiyamCompiler` for English, Hindi Romanized, Telugu, Telugu Romanized. ✅
- **Evidence retrieval**: Real `EvidenceRetriever` with ACL-filtered retrieval from `policy_docs.json`. Deterministic rule-based NLI (not learned). ✅
- **Gate checks 1–4**: Target identity containment, temporal containment, attribute containment, cardinality/approval. ✅
- **Gate check 5**: Evidence sufficiency wired to real NLI verdict. ✅
- **Transactional execution boundary**: `SessionManager.transaction()` context manager wraps simulate + gate + execute. ✅
- **EffectCertificate with hash chain**: Certificate with `seal()`/`verify()` and `chain_from()`. ⚠️ Uses placeholder values in gate.py.
- **Trace lake**: JSONL trace events with all 9 event types. ✅
- **Internal 2000-case evaluation**: Frozen holdout exists. Not fully re-run on final runtime yet.

### What remains research-only:

- External benchmark evaluation (τ³, AgentDojo, BFCL): **Infrastructure-failure / incomplete**
- Full RBAC/scope/tenant gate checks: **Not yet implemented at gate level**
- Transaction-first Verified Execution Broker: **Not yet integrated**
- Production-quality EffectCertificate: **Placeholders remain**
- Human-written multilingual benchmark: **Not yet created**
- Statistical analysis pipeline: **Not yet created**
- Claim/evidence matrix: **Not yet created**
