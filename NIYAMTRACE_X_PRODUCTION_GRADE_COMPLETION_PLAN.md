# NiyamTrace-X Production-Grade Completion Plan

> **For agentic workers:** Execute this plan task-by-task with test-first development, small commits, and independent review gates. Do not skip acceptance criteria because a feature "looks implemented."


## Recent Updates
- **2026-09-18**: Integrated T4 benchmark results, including AgentDojo, BFCL, and Tau3 benchmarks. Added manifests, SHAs, and model tracking.

**Goal:** Transform NiyamTrace-X from a strong research/demo assurance prototype into a production-grade, auditable, secure, multilingual execution-gating platform for tool-using AI agents.

**Architecture:** Preserve the central design principle: probabilistic NLP/LLM components may propose a typed intent contract, but deterministic policy, access, simulation, and effect checks decide whether a tool action may execute. Productionization must reduce trust in callers, models, prompts, UI state, and external services—not increase it.

**Tech Stack:** Python 3.11+, FastAPI, Pydantic v2, SQLite for local/dev, PostgreSQL for production state, DuckDB/Parquet for analytics, optional Gemini/Groq/Ollama-style LLM backends, Docker, GitHub Actions, OpenTelemetry, Prometheus-compatible metrics.

**Repository audited:** `bnssaanirudh/NiyamTrace-X`

**Audit baseline:** 2026-09-17, default branch `main`

---

# 0. Executive Audit Summary

## 0.1 What already exists

NiyamTrace-X already has meaningful implementation across:

- typed contracts;
- multilingual intake and normalization;
- language identification;
- LLM-backed contract compilation;
- entity linking;
- policy/evidence retrieval;
- NLI-style evidence classification;
- deterministic shadow simulation;
- five gate checks;
- execution logic;
- fuzz/metamorphic transforms;
- Bronze JSONL tracing;
- Silver Parquet transformation;
- Gold DuckDB analytics;
- a dashboard;
- benchmark runner and generated scenario sets;
- Dockerfiles and Docker Compose;
- a secrets-manager abstraction;
- unit, integration, regression, and replay test directories;
- one gate-regression test module;
- one Bronze replay test module;
- CI configuration inside the application directory.

This is **not a blank project**. The correct strategy is to harden and reconcile the current implementation, not rewrite everything.

## 0.2 Why it is not production-grade yet

Current repository evidence shows several release-blocking issues:

1. **Repository duplication**
   - The repo root contains a canonical `niyamtrace/` tree and a duplicated nested `NiyamTrace-X-main/.../niyamtrace/` tree.
   - Duplicate source creates ambiguity over what is authoritative.

2. **Contradictory status documentation**
   - `niyamtrace/README.md` still says Week 2.
   - architecture documents describe later modules.
   - the project report calls the codebase "production-ready."
   - production readiness must be derived from measured gates, not prose.

3. **Benchmark failure**
   - committed benchmark report: 20 samples, 35% accuracy;
   - 0/9 expected ALLOW cases were correct;
   - all 7 expected BLOCK cases were correct;
   - schema validity, contract field F1, clarification resolution and effect equivalence were reported as 0.
   - This means the system is currently safe largely by over-blocking, not by correctly understanding and safely executing authorized work.

4. **Caller identity is trusted**
   - `POST /invoke` accepts `actor_id` and `actor_role` from the request body.
   - Production must derive identity and roles from authenticated credentials.

5. **Admin reset endpoint is not protected**
   - `/admin/reset-erp` is a demo endpoint and cannot exist unguarded in production.

6. **CORS is open**
   - `allow_origins=["*"]`.
   - Production must allow only configured trusted origins.

7. **Shared SQLite connection**
   - a singleton ERP connection is created at application startup.
   - This is insufficient for safe concurrent production operation.

8. **Compiler contains demo assumptions**
   - a hard-coded default year of 2025;
   - mock entity resolution (`VENDOR_ID == 9999`);
   - model/backend behavior embedded directly in compiler code;
   - broad exception swallowing in repair handling.

9. **Policy still contains MVP hard-coding**
   - role lists, cardinality threshold and intent-to-attribute mapping live in Python code.
   - Production needs versioned, signed/hashed policy bundles with validation and rollout controls.

10. **Tool coverage and intent coverage are inconsistent**
    - compiler advertises multiple intents;
    - the core executable tool path is centered on `archive_invoices`.
    - Every advertised executable intent needs a real tool schema, simulator, policy, executor, tests and benchmark evidence.

11. **CI is in the wrong repository location**
    - `niyamtrace/.github/workflows/ci.yml` is not repository-root `.github/workflows/ci.yml`.
    - GitHub Actions workflows must live at repository root.

12. **Dependency management is not production-clean**
    - `pytest` and `httpx` are in base runtime dependencies;
    - optional LLM/secrets dependencies are not cleanly grouped;
    - no committed lock file is evident.

13. **Trace privacy is not production-safe**
    - trace payloads can include raw text, normalized text, actor identity and action details.
    - synthetic-only development assumptions cannot carry into real enterprise deployment.

14. **Dashboard analytics rebuild work synchronously**
    - the dashboard refreshes Silver data on request.
    - Production analytics should be incremental/background and must not block user requests.

15. **Safety claim language is stronger than evidence**
    - "guarantee" should only refer to deterministic properties actually proved/tested under explicit assumptions.
    - Never convert "blocked during our benchmark" into "cannot fail."

---

# 1. Production Definition of Done

NiyamTrace-X is **production-grade only when every P0/P1 item below is satisfied**.

## 1.1 P0 release gates — all mandatory

- [ ] Exactly one canonical source tree exists.
- [ ] Repository-root CI is active and required on `main`.
- [ ] All unit, integration, regression, replay, security and contract tests pass.
- [ ] Authentication is mandatory on all non-health endpoints.
- [ ] `actor_id` and `actor_role` are derived from authenticated identity, never trusted from request JSON.
- [ ] RBAC is enforced server-side.
- [ ] Demo/admin endpoints are disabled or strongly protected in production mode.
- [ ] CORS is explicit and environment-configured.
- [ ] Production database operations are transaction-safe under concurrency.
- [ ] Every supported write action has schema + simulator + gate policy + executor + rollback/idempotency behavior.
- [ ] Production policy is loaded from validated, versioned bundles.
- [ ] Prompt/model failures fail closed.
- [ ] LLM timeouts, malformed output, provider outage and rate limits have deterministic safe handling.
- [ ] No raw secret appears in source, logs, traces, dashboards or exception responses.
- [ ] Trace privacy/redaction policy is enforced.
- [ ] Trace retention/deletion policy is implemented.
- [ ] Replay bundles are deterministic for deterministic components.
- [ ] Simulator-to-executor fidelity is measured for every tool.
- [ ] Benchmark has a sealed held-out split.
- [ ] No benchmark evaluation path mutates gold labels or test scenarios.
- [ ] No observed unauthorized ALLOW on the safety-critical held-out suite.
- [ ] Cross-language semantic/effect equivalence meets the release threshold.
- [ ] Authorized ALLOW recall meets the release threshold.
- [ ] CLARIFY routing meets the ambiguity threshold.
- [ ] Rate limiting and request-size limits are active.
- [ ] Structured logs, metrics and traces are available.
- [ ] Readiness checks verify dependencies rather than merely returning process-alive.
- [ ] Docker image runs as a non-root user.
- [ ] Container filesystem is read-only where practical.
- [ ] SBOM and dependency-vulnerability scans run in CI.
- [ ] Backups and restore are tested.
- [ ] Incident response and rollback procedures exist.
- [ ] A tagged release reproduces the exact benchmark evidence quoted in README/paper.

## 1.2 Quantitative release targets

Use these as initial production gates. Change them only through a recorded ADR and benchmark re-freeze.

### Safety-critical held-out suite

Minimum size:

- 5,000 independently reviewed scenarios;
- at least 1,000 unauthorized-action scenarios;
- at least 1,000 ambiguous/clarification scenarios;
- at least 1,000 authorized-action scenarios;
- balanced multilingual/code-mixed variants;
- adversarial prompt-injection/evidence-poisoning subset.

Targets:

- **Unauthorized false-ALLOW:** 0 observed on the 5,000-case safety suite.
- Report one-sided 95% upper confidence bound; with zero failures in 5,000, the simple rule-of-three bound is ~0.06%.
- **Authorized action decision accuracy:** >= 95%.
- **Authorized ALLOW recall:** >= 95%.
- **BLOCK precision for genuinely unauthorized actions:** >= 99%.
- **CLARIFY recall on ambiguous/missing-critical-slot requests:** >= 95%.
- **Contract field micro-F1:** >= 98% for required execution fields.
- **Schema-valid compiler output:** >= 99.5% for production cloud structured-output path.
- **Effect-equivalence across reviewed language variants:** >= 98%.
- **Simulator/executor affected-record-set fidelity:** 100% on supported deterministic tools.
- **Simulator/executor field-delta fidelity:** 100% on supported deterministic tools.
- **Replay deterministic-event equality:** 100% for deterministic stages.
- **Evidence access-control leakage:** 0 observed across adversarial ACL tests.

### Reliability/performance

Initial SLO targets:

- Gateway availability: 99.9% monthly.
- `/health/live` p95: < 100 ms.
- `/health/ready` p95: < 300 ms under healthy dependencies.
- deterministic gate evaluation p95: < 50 ms.
- simulator p95 for supported bounded operations: < 250 ms.
- non-LLM request overhead p95: < 500 ms.
- cloud LLM compile stage p95: define per provider; initially < 4 s.
- timeout budget per external LLM call: <= 8 s unless a documented workload requires more.
- dashboard API p95: < 500 ms without synchronous full trace-lake rebuild.
- error budget alerts at 50%, 75%, 100% burn.

---

# 2. Target Production Architecture

```text
                ┌─────────────────────────────┐
                │ Enterprise Identity Provider│
                │ OIDC / JWT / service tokens│
                └──────────────┬──────────────┘
                               │ verified principal
                               ▼
┌──────────────────────────────────────────────────────────────┐
│                    NiyamTrace Gateway                         │
│ AuthN → RBAC → Rate Limit → Input Validation → Request ID    │
└──────────────────────────────┬───────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────┐
│                    Multilingual Intake                        │
│ Language ID → normalization → temporal/deictic resolution    │
└──────────────────────────────┬───────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────┐
│                     NiyamCompiler                             │
│ LLM proposal → typed schema → deterministic validation       │
│ → entity resolution → ambiguity check → optional bounded repair│
└──────────────────────────────┬───────────────────────────────┘
                               │ ActionContract
                               ▼
┌──────────────────────────────────────────────────────────────┐
│              Evidence + Access-Control Retrieval              │
│ ACL-filtered retrieval → evidence classification             │
└──────────────────────────────┬───────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────┐
│                    Tool Registry                              │
│ typed schema + capability metadata + risk classification     │
└──────────────────────────────┬───────────────────────────────┘
                               │ proposed ToolCall
                               ▼
┌──────────────────────────────────────────────────────────────┐
│                    Shadow Simulator                           │
│ snapshot/transaction → predicted affected records & fields   │
└──────────────────────────────┬───────────────────────────────┘
                               │ StateDelta
                               ▼
┌──────────────────────────────────────────────────────────────┐
│                      NiyamGate                                │
│ identity + temporal + attribute + cardinality + evidence     │
│ + role/policy + approval + risk class + invariant checks     │
└──────────────────────────────┬───────────────────────────────┘
               BLOCK/CLARIFY/ESCALATE │ ALLOW
                                      ▼
┌──────────────────────────────────────────────────────────────┐
│                  Transactional Executor                       │
│ idempotency → recheck → execute → compare actual/predicted   │
│ → commit only if invariants hold; otherwise rollback         │
└──────────────────────────────┬───────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────┐
│                 Audit / Observability Plane                   │
│ redacted traces + effect certificates + metrics + OTel       │
│ replay artifacts + signed policy/model/config provenance     │
└──────────────────────────────────────────────────────────────┘
```

Critical invariant:

> **No generative model directly authorizes or executes a side effect.**

---

# 3. Canonical Repository Structure

First remove duplicate source copies.

Target:

```text
NiyamTrace-X/
├── .github/
│   ├── workflows/
│   │   ├── ci.yml
│   │   ├── security.yml
│   │   ├── release.yml
│   │   └── nightly-benchmark.yml
│   ├── CODEOWNERS
│   └── dependabot.yml
├── .gitignore
├── .pre-commit-config.yaml
├── LICENSE
├── SECURITY.md
├── CONTRIBUTING.md
├── README.md
├── Makefile
├── docker-compose.yml
├── docs/
│   ├── ARCHITECTURE.md
│   ├── THREAT_MODEL.md
│   ├── SECURITY_MODEL.md
│   ├── DATA_GOVERNANCE.md
│   ├── BENCHMARK_PROTOCOL.md
│   ├── MODEL_POLICY.md
│   ├── OPERATIONS.md
│   ├── INCIDENT_RESPONSE.md
│   ├── RELEASE_PROCESS.md
│   └── adr/
├── niyamtrace/
│   ├── pyproject.toml
│   ├── uv.lock
│   ├── .env.example
│   ├── apps/
│   ├── packages/
│   ├── data/
│   ├── migrations/
│   └── tests/
└── artifacts/
    └── README.md
```

Do **not** keep:

```text
NiyamTrace-X-main/
NiyamTrace-X-main/NiyamTrace-X-main/
```

unless intentionally archived outside the active source branch.

---

# 4. Phase 0 — Repository Canonicalization

**Priority:** P0  
**Purpose:** eliminate ambiguity before changing code.

## Files

- Delete/archive: `NiyamTrace-X-main/`
- Keep canonical: `niyamtrace/`
- Move/create: `.github/workflows/*`
- Update: root `README.md`
- Update: `TEAM_TASKS.md`
- Create: `docs/REPOSITORY_STATE.md`

## Tasks

- [ ] Generate recursive file hashes for canonical `niyamtrace/` and duplicated nested trees.
- [ ] Compare duplicates and identify files that exist only in the nested copy.
- [ ] Preserve unique evidence/artifacts before deletion.
- [ ] Declare `niyamtrace/` the only active implementation tree.
- [ ] Remove duplicate code directories from active `main`.
- [ ] Add `docs/REPOSITORY_STATE.md` explaining the cleanup and canonical path.
- [ ] Move CI workflows to repository-root `.github/workflows/`.
- [ ] Move/merge Docker Compose to the repository root or clearly document `docker compose -f niyamtrace/docker-compose.yml`.
- [ ] Remove editor workspace files from test directories.
- [ ] Add generated artifact policy.
- [ ] Remove stale committed HTML benchmark reports if they are intended to be regenerated; otherwise move them under versioned evidence snapshots.
- [ ] Tag the pre-cleanup state, e.g. `v0.1-pre-prod-hardening`.
- [ ] Create a branch `prod-hardening`.
- [ ] Require PR review for `main`.

## Acceptance gate

```bash
git ls-files | grep -E 'NiyamTrace-X-main/NiyamTrace-X-main'
```

Expected:

```text
(no output)
```

and:

```bash
test -f .github/workflows/ci.yml
```

must succeed.

---

# 5. Phase 1 — Truthful Status and Claim Reconciliation

**Priority:** P0

Current docs conflict. Fix them before publication or deployment.

## Files

Modify:

- `README.md`
- `niyamtrace/README.md`
- `niyamtrace/docs/architecture.md`
- `niyamtrace/docs/PROJECT_REPORT.md`
- `niyamtrace/NiyamTrace_Comprehensive_Report.md`
- `TEAM_TASKS.md`

Create:

- `docs/CLAIMS_EVIDENCE.md`
- `docs/IMPLEMENTATION_STATUS.md`

## Required status vocabulary

Use only:

- `IMPLEMENTED`
- `IMPLEMENTED_BUT_UNVALIDATED`
- `VALIDATED_SYNTHETIC`
- `VALIDATED_EXTERNAL`
- `PRODUCTION_HARDENED`
- `EXPERIMENTAL`
- `STUB`
- `DEPRECATED`

## Tasks

- [ ] Remove "Week 2 current status" from canonical README.
- [ ] Replace week-based status with module/evidence status.
- [ ] Remove "production-ready" unless every production gate in this plan passes.
- [ ] Replace absolute words like "guarantees" with scoped deterministic claims.
- [ ] Explain that fail-closed behavior applies only to code paths actually guarded by the gate.
- [ ] Explain which tool actions are truly executable.
- [ ] Explain which languages are heuristic-only vs model-backed.
- [x] List benchmark dataset versions and hashes.
- [x] Link every metric to a command and artifact.
- [ ] State benchmark failures prominently, including over-blocking.
- [ ] Document that current 35% benchmark cannot justify production deployment.
- [ ] Record every supported LLM provider/model as configuration, not marketing copy.
- [ ] Add limitations for provider drift.
- [ ] Add a clear "Supported Production Surface" section.
- [ ] Add a "Not Supported" section.

## Acceptance gate

Every numerical claim in README/paper must map to:

```text
claim → script → config → data hash → result artifact → commit SHA
```

---

# 6. Phase 2 — Configuration and Dependency Hardening

**Priority:** P0

## Problems to fix

- dev/test dependencies in base dependencies;
- no frozen environment;
- provider-specific packages not cleanly separated;
- configuration read directly with `os.environ` across modules;
- provider/model defaults embedded in code.

## Files

Create:

- `niyamtrace/packages/config/settings.py`
- `niyamtrace/packages/config/__init__.py`
- `niyamtrace/uv.lock`
- `niyamtrace/constraints.txt` if required for reproducibility

Modify:

- `niyamtrace/pyproject.toml`
- `.env.example`
- Dockerfiles

## Dependency groups

Suggested:

```toml
[project]
dependencies = [
  "fastapi",
  "uvicorn[standard]",
  "pydantic",
  "pydantic-settings",
  "duckdb",
  "pyarrow",
  "python-dateutil",
  "structlog",
  "prometheus-client",
  "opentelemetry-api",
]

[project.optional-dependencies]
dev = [
  "pytest",
  "pytest-cov",
  "pytest-asyncio",
  "hypothesis",
  "ruff",
  "mypy",
  "bandit",
]
cloud-llm = [
  "google-genai",
  "groq",
  "instructor",
]
local-llm = [
  "openai",
]
aws-secrets = ["boto3"]
vault-secrets = ["hvac"]
postgres = [
  "sqlalchemy",
  "asyncpg",
  "alembic",
]
```

## Tasks

- [ ] Remove `pytest` from runtime dependencies.
- [ ] Remove `httpx` from runtime dependencies unless production code truly uses it.
- [ ] Add `pydantic-settings`.
- [ ] Add explicit provider extras.
- [ ] Add secrets-backend extras.
- [ ] Add PostgreSQL extra.
- [ ] Create one typed `Settings` object.
- [ ] Validate environment at startup.
- [ ] Reject unsupported LLM backend values.
- [ ] Reject production mode with missing auth configuration.
- [ ] Reject production mode with SQLite unless explicitly permitted.
- [ ] Reject wildcard CORS in production.
- [ ] Reject debug mode in production.
- [ ] Pin Python minor compatibility in CI.
- [ ] Generate `uv.lock`.
- [ ] Add reproducible install command:

```bash
uv sync --frozen --all-extras
```

- [ ] Add `make verify-lock`.
- [ ] Add dependency license audit.

---

# 7. Phase 3 — Authentication and Principal Integrity

**Priority:** P0, security-critical

Current request model accepts identity and role from the caller. That is unacceptable for production authorization.

## Target rule

```text
Request body contains intent text.
Verified token contains identity/roles.
Server constructs actor context.
User cannot self-assert role.
```

## Files

Create:

- `niyamtrace/packages/auth/models.py`
- `niyamtrace/packages/auth/jwt.py`
- `niyamtrace/packages/auth/dependencies.py`
- `niyamtrace/packages/auth/rbac.py`
- `niyamtrace/tests/security/test_authn.py`
- `niyamtrace/tests/security/test_rbac.py`

Modify:

- `niyamtrace/apps/gateway/main.py`
- `niyamtrace/apps/dashboard/main.py`

## Request model target

Replace:

```python
class InvokeRequest(BaseModel):
    raw_text: str
    actor_id: str
    actor_role: str
```

with:

```python
class InvokeRequest(BaseModel):
    raw_text: str
    task_id: str | None = None
```

Principal:

```python
class Principal(BaseModel):
    subject: str
    tenant_id: str
    roles: frozenset[str]
    scopes: frozenset[str]
```

## Tasks

- [ ] Implement OIDC/JWT verification.
- [ ] Validate issuer.
- [ ] Validate audience.
- [ ] Validate expiry.
- [ ] Validate not-before.
- [ ] Validate signature algorithm allow-list.
- [ ] Reject `alg=none`.
- [ ] Support key rotation through JWKS.
- [ ] Cache JWKS with bounded TTL.
- [ ] Add service-account authentication.
- [ ] Add tenant ID.
- [ ] Add scopes.
- [ ] Create RBAC mapping.
- [ ] Derive actor from token.
- [ ] Delete actor-role trust from JSON.
- [ ] Bind trace identity to verified principal.
- [ ] Prevent tenant switching through parameters.
- [ ] Require admin scope for admin APIs.
- [ ] Require auditor scope for full-trace APIs.
- [ ] Redact auth errors.
- [ ] Add tests for expired token.
- [ ] Add tests for wrong audience.
- [ ] Add tests for wrong issuer.
- [ ] Add tests for forged signature.
- [ ] Add tests for role escalation.
- [ ] Add tests for cross-tenant trace read.
- [ ] Add tests for cross-tenant action execution.

## Acceptance

No code path may use:

```python
req.actor_role
```

or:

```python
req.actor_id
```

from user JSON.

---

## Phase 4: API Surface Hardening
**Status: COMPLETED**

* [x] Split `/health` into `/health/live` and `/health/ready`
* [x] Add global overload protection (token bucket or simple concurrency limit)
* [x] Inject Request IDs and Trace IDs into response headers
* [x] Return structured, machine-readable `error_code` responses
* [x] Do not leak stack traces or internal component errors (e.g. 500 mapping)
* [x] Add max-length guard (5000 chars) before NLP processing

## Phase 5: Compiler Productionization
**Status: COMPLETED**

* [x] Remove all hard-coded 2025 defaults
* [x] Inject UTC reference time explicitly
* [x] Record reference time in trace
* [x] Move API clients to provider adapters
* [x] Add provider timeout
* [x] Add bounded retries only for retryable errors (429, 503)
* [x] Replace mock vendor existence check with repository lookup
* [x] Resolve entities within authenticated tenant
* [x] Calibrate confidence thresholds using validation data
* [x] Do not use raw LLM self-confidence as a security guarantee
* [x] Add deterministic slot validation and schemas
* [x] Version and hash prompts
* [x] Record provider/model/version/prompt_hash in trace
* [x] Make local offline mode explicit

- [ ] Restrict OpenAPI docs in production if required.
- [ ] Disable `/admin/reset-erp` in production.
- [ ] Rename demo reset to a dev-only router.
- [ ] Add idempotency key header for write-capable requests.
- [ ] Enforce timeout budget.
- [ ] Return `429` on rate-limit rejection.
- [ ] Return `503` when dependencies are not ready.
- [ ] Return `422` for invalid contract input.
- [ ] Return consistent BLOCK/CLARIFY semantics without transport-level crashes.

## Important bug test

Create a test where compilation returns `contract=None`.

The API must not dereference:

```python
result.predicted_delta.estimated_row_count
```

when `predicted_delta` is `None`.

Expected response:

```json
{
  "verdict": "CLARIFY",
  "predicted_record_count": 0,
  "actual_record_count": null
}
```

---

# 9. Phase 5 — Compiler Productionization

**Priority:** P0

## Current issues

- year `2025` is hard-coded;
- entity-link stage still has mock logic;
- exception swallowing hides provider/repair failures;
- provider client construction lives inside compiler;
- prompt text and model config are embedded;
- one confidence number is treated as trustworthy despite no calibration evidence.

## Files

Refactor:

- `packages/nlp/compiler.py`

Create:

- `packages/nlp/provider.py`
- `packages/nlp/prompts.py`
- `packages/nlp/entity_repository.py`
- `packages/nlp/confidence.py`
- `packages/nlp/errors.py`

Modify:

- `packages/nlp/temporal.py`

## Tasks

- [x] Remove all hard-coded 2025 defaults.
- [x] Inject reference time explicitly.
- [x] Use UTC-aware clock abstraction.
- [x] Record reference time in trace.
- [x] Make model name configuration-only.
- [x] Make provider endpoint configuration-only.
- [x] Move API clients to provider adapters.
- [x] Add provider timeout.
- [x] Add bounded retries only for retryable errors.
- [x] Do not retry policy rejection.
- [x] Do not silently swallow repair exceptions.
- [x] Emit structured repair failure reason.
- [x] Replace mock vendor existence check with repository lookup.
- [x] Resolve entities within authenticated tenant.
- [x] Support ambiguous entity matches.
- [x] Route ambiguity to CLARIFY.
- [x] Record candidate alternatives without leaking unrelated tenant entities.
- [x] Calibrate confidence thresholds using validation data.
- [x] Do not use raw LLM self-confidence as a security guarantee.
- [x] Add deterministic slot validation.
- [x] Enforce slot schemas per intent.
- [x] Reject unknown slots for security-sensitive intents.
- [x] Version prompts.
- [x] Hash prompt template and include hash in trace.
- [x] Record provider/model/version in trace.
- [x] Add provider fallback only if policy explicitly allows it.
- [x] Never silently switch a production request to a different model family.
- [x] Label fallback outputs.
- [x] Make local offline mode explicit.

## Provider interface

```python
class StructuredExtractor(Protocol):
    async def extract(
        self,
        *,
        text: str,
        schema: type[BaseModel],
        request_id: str,
        timeout_s: float,
    ) -> BaseModel:
        ...
```

## Required compiler outcomes

Exactly:

```text
SUCCESS
CLARIFY
FAIL_CLOSED
PROVIDER_UNAVAILABLE
```

Map all internal exceptions into one of these categories.

---

# 10. Phase 6 — Intent and Tool Capability Model

**Priority:** P0

Do not advertise executable intents without complete capability implementation.

## Production capability tuple

Every executable action must have:

```text
Intent schema
→ tool schema
→ authorization policy
→ simulator
→ gate rules
→ executor
→ idempotency behavior
→ rollback/transaction semantics
→ regression tests
→ benchmark cases
→ effect certificate
```

## Initial production scope

Start with **one** write capability:

```text
invoice.archive
```

Stabilize it completely before enabling:

- access.grant
- access.block
- limit.update
- vendor.suspend
- refund
- share
- delete/tombstone

## Files

Create:

- `packages/tools/base.py`
- `packages/tools/registry.py`
- `packages/tools/archive_invoices.py`

Refactor:

- `packages/gate/tool_schemas.py`
- `packages/gate/simulator.py`
- `packages/gate/executor.py`

## Registry model

```python
class ToolCapability(BaseModel):
    name: str
    schema_version: str
    risk_class: Literal["READ", "LOW_WRITE", "HIGH_WRITE"]
    required_scopes: frozenset[str]
    supports_simulation: bool
    supports_idempotency: bool
```

## Tasks

- [x] Create central capability registry.
- [x] Reject tools absent from registry.
- [x] Reject schema-version mismatch.
- [x] Bind intent to exactly allowed tools.
- [x] Bind principal scopes to tool capability.
- [x] Add risk class.
- [x] Require approval for high-risk classes.
- [x] Define idempotency semantics.
- [x] Define max affected rows per tool.
- [x] Define allowed fields per tool.
- [x] Define allowed tables per tool.
- [x] Define transactional boundary.
- [x] Add simulator and executor interface parity tests.
- [x] Add capability-version hash.
- [x] Include tool registry hash in traces.

---

# 11. Phase 7 — Policy Engine Productionization

**Priority:** P0

## Current issue

Policy roles and cardinality thresholds are hard-coded Python defaults.

## Target

Versioned policy bundle:

```yaml
version: 1.0.0
tenant: acme
rules:
  invoice.archive:
    allowed_roles:
      - procurement_manager
      - finance_admin
    allowed_attributes:
      - status
    max_rows_without_approval: 10
    evidence_required: true
    approval:
      required_above_rows: 10
```

## Files

Create:

- `packages/policy/models.py`
- `packages/policy/loader.py`
- `packages/policy/compiler.py`
- `packages/policy/signature.py`
- `policies/reference.yaml`
- `tests/unit/test_policy_loader.py`
- `tests/security/test_policy_tamper.py`

Refactor:

- `packages/gate/policy.py`

## Tasks

- [ ] Move policy data out of Python constants.
- [ ] Validate YAML/JSON against typed schema.
- [ ] Compute full SHA-256 bundle hash.
- [ ] Record bundle version and hash in every decision.
- [ ] Reject invalid bundle at startup.
- [ ] Reject unsigned/unapproved bundle in production if signing is enabled.
- [ ] Support tenant-specific bundle.
- [ ] Support staged rollout.
- [ ] Support rollback.
- [ ] Make policy change auditable.
- [ ] Prevent hot reload from partially applying invalid policy.
- [ ] Add policy-diff command.
- [ ] Add policy regression suite.
- [ ] Add policy conflict detection.
- [ ] Define deny-overrides semantics.
- [ ] Explicitly define default-deny behavior.

---

# 12. Phase 8 — Evidence/RAG Security

**Priority:** P0

NiyamEvidence is part of authorization context; therefore retrieval security matters.

## Files

Review/refactor:

- `packages/evidence/acl.py`
- `packages/evidence/retriever.py`
- `packages/evidence/nli.py`

Create:

- `tests/security/test_evidence_acl.py`
- `tests/security/test_retrieval_poisoning.py`
- `tests/security/test_prompt_injection_evidence.py`

## Tasks

- [ ] Apply ACL filter before ranking whenever possible.
- [ ] Never retrieve unauthorized chunks and then "hide" them after generation.
- [ ] Tag every chunk with tenant, source, version and ACL.
- [ ] Reject evidence without provenance.
- [ ] Separate policy documents from untrusted user content.
- [ ] Mark untrusted content as inert data.
- [ ] Add prompt-injection markers to benchmark.
- [ ] Ensure retrieved text cannot define executable instructions.
- [ ] Treat evidence NLI output as advisory unless deterministic policy says otherwise.
- [ ] Define evidence freshness rules.
- [ ] Define evidence revocation.
- [ ] Add source version hash.
- [ ] Add evidence trace references.
- [ ] Add contradiction tests.
- [ ] Add insufficient-evidence tests.
- [ ] Add stale-policy tests.
- [ ] Add poisoned-document tests.
- [ ] Add cross-tenant leakage tests.
- [ ] Add top-k manipulation tests.
- [ ] Add duplicate evidence tests.

## Required metric

```text
Unauthorized evidence leakage rate = 0 observed
```

on the adversarial test corpus.

---

# 13. Phase 9 — Shadow Simulator and Executor Atomicity

**Priority:** P0

The simulator/executor relationship is the core differentiator of NiyamTrace.

## Required invariant

For every allowed deterministic tool:

```text
predicted affected record IDs == actual affected record IDs
predicted fields == actual changed fields
```

If execution-time state changes invalidate the simulation:

```text
ROLLBACK
```

not "continue anyway."

## Files

Refactor:

- `packages/gate/simulator.py`
- `packages/gate/executor.py`
- `apps/gateway/pipeline.py`

Create:

- `packages/storage/session.py`
- `tests/integration/test_simulate_execute_atomicity.py`
- `tests/integration/test_concurrent_state_change.py`

## Production sequence

```text
BEGIN TRANSACTION
→ obtain snapshot/version
→ simulate
→ gate
→ revalidate state version
→ execute
→ compare actual vs predicted
→ if mismatch: ROLLBACK
→ else COMMIT
```

## Tasks

- [ ] Add state/snapshot version.
- [ ] Add optimistic concurrency token or transaction isolation.
- [ ] Simulate and execute against consistent state.
- [ ] Recheck policy immediately before write.
- [ ] Recheck authorization immediately before write.
- [ ] Compare actual delta to predicted delta before commit.
- [ ] Roll back on mismatch.
- [ ] Log mismatch as high-severity incident.
- [ ] Add idempotency key.
- [ ] Persist idempotency record transactionally.
- [ ] Return previous result on duplicate idempotency key.
- [ ] Prevent double execution under retries.
- [ ] Add concurrent request tests.
- [ ] Add race-condition tests.
- [ ] Add partial failure tests.
- [ ] Add DB disconnect tests.
- [ ] Add deadlock/retry policy.
- [ ] Bound transaction time.
- [ ] Add row-count ceiling before materializing huge diffs.
- [ ] Make simulator read-only at DB permission level in production.

---

# 14. Phase 10 — Database Productionization

**Priority:** P0 for multi-user production

SQLite is acceptable for local demos, replay and tests. Use PostgreSQL for production concurrency.

## Files

Create:

- `packages/storage/db.py`
- `packages/storage/models.py`
- `migrations/`
- `alembic.ini`

## Tasks

- [ ] Introduce storage interface.
- [ ] Keep SQLite adapter for local/demo.
- [ ] Add PostgreSQL adapter.
- [ ] Use connection pool.
- [ ] Set transaction isolation explicitly.
- [ ] Add migrations.
- [ ] Add migration test from clean DB.
- [ ] Add upgrade/downgrade smoke test.
- [ ] Add tenant column to all tenant-owned tables.
- [ ] Add foreign keys.
- [ ] Add unique idempotency keys.
- [ ] Add audit/event constraints.
- [ ] Add indexes for selectors used by simulator.
- [ ] Add backup job.
- [ ] Add restore rehearsal.
- [ ] Add point-in-time recovery if managed Postgres supports it.
- [ ] Verify least-privilege DB roles.
- [ ] Separate read-only simulator DB role if architecture permits.
- [ ] Encrypt storage at provider level.
- [ ] Document data residency assumptions.

---

# 15. Phase 11 — Approval and Human Escalation Workflow

**Priority:** P1, but P0 for high-risk actions

`ESCALATE` must be an actual workflow, not a label.

## Files

Create:

- `packages/approval/models.py`
- `packages/approval/service.py`
- `apps/gateway/approval_routes.py`
- `tests/integration/test_approval_flow.py`

## State machine

```text
PENDING_APPROVAL
→ APPROVED
→ EXECUTED

PENDING_APPROVAL
→ REJECTED

PENDING_APPROVAL
→ EXPIRED
```

## Tasks

- [ ] Persist approval request.
- [ ] Include exact contract hash.
- [ ] Include exact predicted delta hash.
- [ ] Include policy bundle hash.
- [ ] Include requester principal.
- [ ] Include required approver role.
- [ ] Expire approvals.
- [ ] Prevent approval replay after contract changes.
- [ ] Prevent self-approval when segregation-of-duties policy requires it.
- [ ] Re-simulate after approval if state changed.
- [ ] Re-run gate before execution.
- [ ] Audit approver identity.
- [ ] Add approve/reject APIs.
- [ ] Add dashboard approval view.
- [ ] Add concurrency tests.
- [ ] Add expired approval tests.
- [ ] Add tampered approval token tests.

---

# 16. Phase 12 — Trace Privacy, Provenance and Effect Certificates

**Priority:** P0

Current trace architecture is useful for research but needs enterprise privacy controls.

## Principles

- default to hashes/IDs rather than raw sensitive text;
- raw prompt retention is opt-in by tenant policy;
- protect traces as sensitive security data;
- distinguish audit provenance from user-visible diagnostics.

## Files

Create:

- `packages/privacy/redaction.py`
- `packages/privacy/policy.py`
- `packages/audit/certificates.py`
- `packages/audit/chain_store.py`
- `tests/security/test_trace_redaction.py`
- `tests/security/test_certificate_chain.py`

Refactor:

- `packages/lake/writer.py`
- `packages/contracts/schema.py`

## Tasks

- [ ] Define data classification.
- [ ] Define trace fields that may contain PII.
- [ ] Redact secrets.
- [ ] Redact access tokens.
- [ ] Redact API keys.
- [ ] Redact passwords.
- [ ] Redact likely financial/account identifiers where configured.
- [ ] Replace raw text with hash by default in production audit log.
- [ ] Store encrypted raw text only when required.
- [ ] Add tenant retention setting.
- [ ] Add trace deletion workflow.
- [ ] Preserve non-sensitive integrity metadata after permitted deletion.
- [ ] Add access-control around trace reading.
- [ ] Add tamper-detection verification CLI.
- [ ] Verify certificate chain continuity.
- [ ] Fix actor field to immutable principal ID, not merely role.
- [ ] Include policy hash.
- [ ] Include tool schema hash.
- [ ] Include model/prompt version.
- [ ] Include database snapshot/version.
- [ ] Include predicted-delta hash.
- [ ] Include actual-delta hash.
- [ ] Do not claim a hash chain makes source facts truthful.
- [ ] Consider digital signatures for release/audit bundles.
- [ ] Add key rotation procedure if signing is used.

---

# 17. Phase 13 — Replay System

**Priority:** P0

Replay is central to assurance.

## Existing starting point

There is a Bronze replay test, but production replay needs a formal bundle format.

## Bundle contents

```text
replay/
  manifest.json
  request.json
  principal.json
  normalized_input.json
  contract.json
  policy_bundle.json
  evidence_refs.json
  tool_schema.json
  state_snapshot_ref.json
  events.jsonl
  expected_decision.json
  hashes.json
```

## Files

Create:

- `packages/replay/bundle.py`
- `packages/replay/runner.py`
- `packages/replay/diff.py`
- `apps/replay/main.py`

## Tasks

- [ ] Version replay bundle schema.
- [ ] Validate checksums before replay.
- [ ] Require exact policy bundle.
- [ ] Require exact tool schema.
- [ ] Require exact deterministic configuration.
- [ ] Separate deterministic replay from LLM re-inference.
- [ ] For LLM stages, support:
  - recorded-output replay;
  - live re-inference comparison.
- [ ] Do not require live provider for deterministic replay.
- [ ] Diff decisions.
- [ ] Diff contracts.
- [ ] Diff affected record IDs.
- [ ] Diff field deltas.
- [ ] Diff evidence refs.
- [ ] Diff latency separately; latency equality is not required.
- [ ] Add replay CLI.
- [ ] Add CI replay corpus.
- [ ] Add version migration for replay bundles.
- [ ] Add corrupted-bundle tests.
- [ ] Add missing-snapshot tests.
- [ ] Add wrong-policy tests.
- [ ] Add wrong-model-version warnings.
- [ ] Add deterministic hash output.

---

# 18. Phase 14 — Multilingual Production Evaluation

**Priority:** P0 for core product claim

Do not use machine translation alone as gold data.

## Required language groups

At minimum for current product claim:

- English
- Hinglish / romanized Hindi
- Telugu script
- Romanized Telugu

Only add Hindi, Tamil or Kannada to the production claim after equivalent evidence exists.

## Data design

For each canonical scenario create semantically matched variants:

```text
canonical_id: invoice.archive.0042
variants:
  en
  hi_rom
  te
  te_rom
```

Each reviewed variant must preserve:

- actor intent;
- target entity;
- temporal bounds;
- quantity/cardinality;
- action;
- approval semantics;
- negation;
- ambiguity level.

## Annotation protocol

Require:

- annotator A;
- annotator B;
- adjudicator for disagreement;
- language proficiency field;
- machine-translation flag;
- confidence;
- rationale;
- immutable split assignment.

## Metrics

Measure:

- language-ID accuracy;
- normalization preservation rate;
- intent accuracy;
- slot F1;
- entity-link accuracy;
- clarification recall;
- gate verdict accuracy;
- false-ALLOW;
- effect-equivalence;
- latency;
- provider failure rate.

## Tasks

- [ ] Write annotation guidelines.
- [ ] Create canonical scenario ontology.
- [ ] Freeze train/dev/test IDs.
- [ ] Hash dataset files.
- [ ] Measure inter-annotator agreement.
- [ ] Report adjudication rate.
- [ ] Keep machine-generated variants separate.
- [ ] Create spelling-noise subset.
- [ ] Create script-mixing subset.
- [ ] Create transliteration subset.
- [ ] Create negation subset.
- [ ] Create code-switch boundary subset.
- [ ] Create temporal-deixis subset.
- [ ] Create ambiguous-entity subset.
- [ ] Create prompt-injection subset.
- [ ] Create overbroad-scope subset.
- [ ] Create conversational carryover subset only after session semantics are implemented.
- [ ] Run per-language confidence intervals.
- [ ] Report worst-language metric, not only pooled average.
- [ ] Do not ship a language with unacceptable false-ALLOW even if global average passes.

---

# 19. Phase 15 — Benchmark Redesign

**Priority:** P0

Current committed 20-case report is not a production qualification benchmark.

## Split structure

```text
data/benchmark/
  protocol.md
  schema/
  train/
  dev/
  test_sealed/
  adversarial/
  manifests/
```

## No test contamination

- test labels are not imported into runtime code;
- no prompt contains gold answer;
- no threshold tuning on sealed test;
- test run writes to a new immutable directory.

## Primary metrics

```text
Safety:
  false_allow_rate
  unauthorized_block_recall
  evidence_acl_leak_rate

Utility:
  authorized_allow_recall
  clarify_recall
  contract_field_f1

Consistency:
  effect_equivalence_rate
  cross_language_verdict_consistency

Engineering:
  schema_validity_rate
  simulator_fidelity
  replay_match_rate
  provider_error_rate
  p50/p95/p99 latency
```

## Baselines

Compare:

1. raw LLM tool caller without NiyamGate;
2. LLM + schema validation only;
3. LLM + schema + RBAC;
4. LLM + schema + RBAC + simulator;
5. full NiyamTrace;
6. deterministic parser where applicable;
7. constrained-output LLM baseline;
8. local model baseline.

## Ablations

Remove one component at a time:

- language normalization;
- entity linker;
- evidence;
- simulator;
- identity containment;
- temporal containment;
- attribute containment;
- cardinality;
- repair pass;
- confidence/clarification gate.

## Statistical reporting

- bootstrap CIs for accuracy/F1/equivalence;
- Wilson/Clopper-Pearson for rare safety failure rates;
- paired tests on matched scenarios;
- per-language paired comparison;
- report absolute counts with rates.

## Tasks

- [ ] Replace 80% single accuracy threshold with multi-metric release gate.
- [ ] Add false-ALLOW hard gate.
- [ ] Add ALLOW recall hard gate.
- [ ] Add CLARIFY hard gate.
- [ ] Add equivalence hard gate.
- [ ] Add schema-validity hard gate.
- [ ] Add simulator-fidelity hard gate.
- [x] Store per-scenario outputs.
- [x] Store config manifest.
- [x] Store environment manifest.
- [x] Store git SHA.
- [x] Store dataset SHA.
- [x] Store prompt hash.
- [x] Store model ID.
- [ ] Store policy hash.
- [ ] Fail if output directory already exists.
- [ ] Add deterministic seed where applicable.
- [x] Add offline fixture mode for PRs.
- [ ] Run expensive live-provider benchmark nightly or manually.
- [ ] Never place paid provider benchmark in mandatory PR gate.
- [ ] Require manual promotion of a benchmark artifact to "release evidence."

---

# 20. Phase 16 — Testing Pyramid

**Priority:** P0

## Required suites

```text
tests/
  unit/
  integration/
  regression/
  replay/
  contract/
  security/
  adversarial/
  property/
  load/
  migration/
  e2e/
```

## Unit tests

Add tests for:

- typed config;
- auth parser;
- role resolution;
- policy loader;
- policy conflicts;
- provider adapters;
- temporal resolver;
- entity repository;
- slot schema;
- tool registry;
- evidence ACL;
- redaction;
- idempotency;
- certificate hashes.

## Property-based tests

Use Hypothesis for:

- temporal boundaries;
- arbitrary Unicode;
- malformed structured outputs;
- tool arguments;
- selector cardinality;
- record delta sets;
- policy bundle parse/round-trip;
- trace serialization;
- hash-chain tampering.

## Security tests

Must include:

- forged JWT;
- role escalation;
- tenant escape;
- prompt injection;
- evidence poisoning;
- malformed Unicode;
- SQL injection attempts;
- path traversal;
- oversized body;
- rate-limit bypass;
- replay tampering;
- admin endpoint access;
- trace enumeration.

## Regression corpus

Every discovered failure receives:

```text
bug ID
minimal reproducer
expected safe behavior
test
commit fixing it
```

Examples:

- local LLM string in integer MONTH;
- missing temporal scope;
- 2025-default bug;
- CLARIFY path response crash;
- overbroad tool date;
- cross-language variant mismatch;
- evidence contradiction;
- simulator/executor mismatch.

## E2E tests

Minimum:

1. authorized archive → ALLOW → exact expected rows tombstoned;
2. unauthorized role → BLOCK;
3. missing month → CLARIFY;
4. cardinality over threshold → ESCALATE;
5. approved escalation → ALLOW after re-simulation;
6. prompt injection → BLOCK;
7. provider failure → fail closed;
8. concurrent state change → rollback;
9. duplicate idempotency key → no duplicate effect;
10. cross-tenant request → BLOCK.

## Coverage goals

- safety-critical deterministic packages: >= 95% branch coverage;
- total Python project: >= 90% line coverage;
- 100% coverage alone is not sufficient.

Add mutation testing for:

- gate rules;
- RBAC;
- policy evaluation;
- simulator/executor comparison.

---

# 21. Phase 17 — CI/CD

**Priority:** P0

## Root workflow

Create:

```text
.github/workflows/ci.yml
```

PR jobs:

```text
format/lint
typecheck
unit
integration
regression
replay
security
property
coverage
package-build
docker-build
SBOM
dependency-scan
```

Main-branch jobs:

```text
all PR jobs
offline benchmark
artifact upload
image signing
```

Nightly/manual:

```text
live-provider benchmark
adversarial benchmark
load test
long replay corpus
dependency freshness
```

## Required checks

- [ ] `ruff check`
- [ ] `ruff format --check`
- [ ] `mypy`
- [ ] `pytest`
- [ ] branch coverage
- [ ] Bandit/Semgrep
- [ ] dependency audit
- [ ] secret scan
- [ ] Dockerfile scan
- [ ] SBOM generation
- [ ] package build
- [ ] install built wheel in clean environment
- [ ] Docker smoke test
- [ ] OpenAPI schema export diff
- [ ] benchmark smoke test
- [ ] replay smoke test

## Branch protection

Require:

- PR;
- all required checks;
- no force push;
- signed commits/tags where feasible;
- CODEOWNERS review for:
  - auth;
  - gate;
  - policy;
  - executor;
  - production config.

---

# 22. Phase 18 — Container and Deployment Hardening

**Priority:** P0

## Docker requirements

- [ ] pin base image digest;
- [ ] multi-stage build;
- [ ] non-root UID;
- [ ] no package manager cache;
- [ ] minimal runtime deps;
- [ ] healthcheck;
- [ ] read-only root filesystem where practical;
- [ ] writable mounted volume only for explicit data;
- [ ] no secret in image layer;
- [ ] no `.env` copied into image;
- [ ] no benchmark corpus containing restricted data copied unless required;
- [ ] drop Linux capabilities;
- [ ] resource limits documented.

## Deployment recommendation

Do **not** jump straight to Kubernetes.

Start:

```text
Managed container service
+ managed PostgreSQL
+ managed secret store
+ object storage for immutable replay/evidence artifacts
+ OTel collector
```

Use Kubernetes only after load/tenant requirements justify operational complexity.

## Environments

```text
dev
test
staging
production
```

Production must refuse:

- wildcard CORS;
- demo reset route;
- default secret backend with plaintext `.env` if organizational policy forbids it;
- missing auth;
- missing policy bundle;
- unknown tool schema;
- debug reload;
- unversioned model configuration.

---

# 23. Phase 19 — Observability

**Priority:** P0

## Create

- `packages/observability/logging.py`
- `packages/observability/metrics.py`
- `packages/observability/tracing.py`

## Structured log fields

```text
timestamp
level
service
request_id
trace_id
tenant_id_hash
principal_id_hash
intent
verdict
reason_code
policy_version
tool_name
model_provider
model_id
latency_ms
error_class
```

Do not log:

- access token;
- API key;
- raw password;
- secrets;
- full raw prompt by default;
- private model reasoning.

## Metrics

Counters:

- requests_total;
- allow_total;
- block_total;
- clarify_total;
- escalate_total;
- provider_errors_total;
- tool_execution_total;
- simulator_mismatch_total;
- replay_mismatch_total;
- auth_failures_total;
- rate_limit_total.

Histograms:

- total latency;
- intake latency;
- compiler latency;
- retrieval latency;
- simulation latency;
- gate latency;
- execution latency.

Gauges:

- DB pool utilization;
- queue depth;
- policy bundle age;
- provider circuit state.

## Alerts

Page on:

- any simulator/executor mismatch in production;
- any unauthorized-effect post-execution invariant violation;
- sustained auth failure spike;
- provider failure rate > threshold;
- database unavailable;
- replay integrity failure;
- policy load failure.

---

# 24. Phase 20 — Dashboard Productionization

**Priority:** P1

Dashboard is an observability/audit surface, not part of authorization truth.

## Tasks

- [ ] Add authentication.
- [ ] Add auditor/admin roles.
- [ ] Enforce tenant filtering.
- [ ] Remove filesystem paths.
- [ ] Paginate traces.
- [ ] Bound `n`.
- [ ] Add query timeouts.
- [ ] Do not rebuild entire Silver layer per request.
- [ ] Move Bronze→Silver transform to background/streaming job.
- [ ] Cache aggregate metrics.
- [ ] Add trace search.
- [ ] Add reason-code filter.
- [ ] Add policy-version filter.
- [ ] Add language filter.
- [ ] Add provider/model filter.
- [ ] Add approval queue.
- [ ] Add simulator-vs-executor fidelity view.
- [ ] Add redaction indicators.
- [ ] Add replay button only for authorized auditors.
- [ ] Add accessible keyboard navigation.
- [ ] Add CSP.
- [ ] Avoid remote third-party fonts/assets in restricted deployments.
- [ ] Add empty/error/loading states.
- [ ] Add export with authorization and audit logging.

---

# 25. Phase 21 — Threat Model

**Priority:** P0

Create `docs/THREAT_MODEL.md`.

## Assets

Protect:

- production state;
- policy bundles;
- identity/role claims;
- evidence documents;
- tool schemas;
- traces;
- secrets;
- effect certificates;
- approval records.

## Threat actors

- malicious ordinary user;
- compromised tenant account;
- compromised admin;
- malicious document/evidence author;
- compromised LLM/provider;
- prompt-injection content;
- insider with DB access;
- attacker with trace-store access;
- supply-chain attacker.

## Mandatory threat scenarios

### Identity

- user claims `finance_admin`;
- forged JWT;
- token replay;
- expired token;
- cross-tenant token.

### NLP/LLM

- prompt requests ignoring policy;
- malicious multilingual code switching;
- Unicode confusables;
- model hallucinates broader date;
- model emits extra fields;
- model provider returns malformed JSON;
- provider outage.

### Evidence

- policy document contains prompt injection;
- tenant A document retrieved for tenant B;
- stale policy;
- manipulated metadata;
- duplicated evidence boosting rank.

### Tool execution

- tool schema drift;
- TOCTOU between simulation and execution;
- retry causes duplicate write;
- execution changes more rows than simulation;
- DB state changes after approval;
- unknown tool.

### Audit

- trace deletion;
- hash-chain tamper;
- log injection;
- secret leakage;
- raw prompt over-retention.

For each threat record:

```text
asset
entry point
precondition
attack
existing control
missing control
test
residual risk
owner
```

---

# 26. Phase 22 — Secrets Management

**Priority:** P0

A secrets abstraction already exists; harden it.

## Tasks

- [ ] Do not silently fall back from AWS/Vault to environment if the configured backend dependency is absent in production.
- [ ] Fail startup instead.
- [ ] Never accept Vault token in application logs.
- [ ] Prefer workload identity/IAM role over static AWS access keys.
- [ ] Add secret version awareness.
- [ ] Add rotation test.
- [ ] Clear/refresh in-process cache on rotation signal if required.
- [ ] Add startup validation for required keys.
- [ ] Add secret backend health metric.
- [ ] Add tests for missing backend library.
- [ ] Add tests for missing secret.
- [ ] Add tests for inaccessible secret store.
- [ ] Add tests ensuring values are not included in exceptions.
- [ ] Run secret scanner over full Git history.

---

# 27. Phase 23 — Production Data Governance

**Priority:** P0

The current "synthetic only" development policy is good, but real deployments need explicit governance.

Create:

- `docs/DATA_GOVERNANCE.md`

Define:

- data controller/processor responsibility;
- input data classes;
- trace data classes;
- tenant isolation;
- retention;
- deletion;
- export;
- encryption;
- backup;
- legal hold if relevant;
- model-provider data transmission.

## Tasks

- [ ] Add configuration controlling whether raw text may leave local environment.
- [ ] For local-only tenants, reject cloud providers.
- [ ] Record provider destination region if available.
- [ ] Add data-processing disclosure.
- [ ] Add tenant-level retention days.
- [ ] Add "do not store raw text" mode.
- [ ] Add "hash-only audit" mode.
- [ ] Add deletion verification.
- [ ] Add backup retention.
- [ ] Add dataset licensing manifest.

---

# 28. Phase 24 — LLM Provider Governance

**Priority:** P1

Create `docs/MODEL_POLICY.md`.

For each production model record:

```text
provider
model ID
structured output capability
region
data retention policy
timeout
retry count
max tokens
temperature
fallback allowed?
validation benchmark artifact
approval date
```

## Rules

- no implicit model upgrade;
- no `latest` aliases for release evidence;
- model/provider change requires benchmark;
- prompt change requires benchmark;
- fallback model requires independent qualification;
- local model failure must remain fail-closed.

---

# 29. Phase 25 — Temporal Semantics

**Priority:** P0 because time scope controls side effects

## Problems

Temporal words are security-sensitive:

- "last month"
- "March"
- "previous quarter"
- "before yesterday"
- "older than 30 days"

## Tasks

- [ ] Inject reference clock.
- [ ] Inject tenant timezone.
- [ ] Store resolved timezone.
- [ ] Test DST boundaries.
- [ ] Test month/year rollover.
- [ ] Test leap year.
- [ ] Test current month ambiguity.
- [ ] Never assume a year silently when doing a destructive action unless policy explicitly allows it.
- [ ] Prefer CLARIFY for unresolved year.
- [ ] Add exact source span for temporal expression.
- [ ] Add temporal-resolution confidence.
- [ ] Include resolved bounds in contract.
- [ ] Compare tool bounds against contract bounds structurally.

---

# 30. Phase 26 — Entity Linking

**Priority:** P0

Replace mock entity logic with real tenant-scoped entity resolution.

## API

```python
class EntityRepository(Protocol):
    async def resolve_vendor(
        self,
        *,
        tenant_id: str,
        vendor_id: int | None,
        vendor_name: str | None,
    ) -> EntityResolution:
        ...
```

## Resolution outcomes

```text
EXACT
AMBIGUOUS
NOT_FOUND
UNAUTHORIZED
```

## Tasks

- [ ] Resolve by stable ID when present.
- [ ] Resolve name only within authorized tenant.
- [ ] Do not reveal unauthorized entity existence.
- [ ] Add fuzzy-match threshold.
- [ ] Calibrate threshold.
- [ ] Return CLARIFY on multiple plausible entities.
- [ ] Add alias support.
- [ ] Add Unicode normalization.
- [ ] Add transliterated-name support separately from action-language support.
- [ ] Add entity-link benchmark.
- [ ] Add adversarial near-name tests.

---

# 31. Phase 27 — Fail-Closed Semantics

**Priority:** P0

Create one explicit decision table.

| Failure | Production behavior |
|---|---|
| auth invalid | reject request |
| auth service unavailable | reject protected request |
| policy unavailable | BLOCK / service unavailable |
| tool schema unknown | BLOCK |
| LLM malformed output | CLARIFY or BLOCK; never execute |
| LLM timeout | BLOCK/CLARIFY according to endpoint policy |
| entity ambiguous | CLARIFY |
| evidence inaccessible | BLOCK or ESCALATE |
| simulator error | BLOCK |
| simulator too many rows | BLOCK/ESCALATE |
| gate internal error | BLOCK |
| DB state changed before execute | re-simulate or rollback |
| actual delta differs from predicted | rollback + incident |
| audit write failure | fail closed for high-risk action |
| approval invalid/expired | BLOCK |

Add tests for every row.

---

# 32. Phase 28 — Concurrency and Load Testing

**Priority:** P0 before multi-user deployment

Use Locust/k6 or a Python load harness.

Scenarios:

- read-only health;
- concurrent authorized archives on different vendors;
- same vendor/date conflict;
- duplicate idempotency key;
- simultaneous approval and state mutation;
- provider slowdown;
- DB connection saturation;
- dashboard trace browsing during writes.

Targets:

- no double execution;
- no cross-request trace corruption;
- no SQLite threading errors in dev;
- no DB pool exhaustion under target load;
- p95 within SLO;
- controlled 429/503 under overload.

---

# 33. Phase 29 — Fault Injection and Chaos Tests

**Priority:** P1

Inject:

- LLM 429;
- LLM 500;
- malformed JSON;
- 10-second LLM delay;
- evidence store unavailable;
- DB timeout;
- disk full for trace writer;
- corrupted replay artifact;
- policy bundle unavailable;
- secret-store unavailable;
- dashboard analytics failure.

Expected:

```text
safe failure
clear reason code
no unintended write
observable alert
```

---

# 34. Phase 30 — Supply Chain Security

**Priority:** P0

## Tasks

- [ ] Dependabot or Renovate.
- [ ] pip dependency audit.
- [ ] SBOM CycloneDX/SPDX.
- [ ] Docker image scan.
- [ ] pin GitHub Actions by major or commit according to org policy.
- [ ] signed release tags.
- [ ] provenance attestation where available.
- [ ] license scan.
- [ ] secret scan.
- [ ] verify downloaded model hashes.
- [ ] document model/data origin.
- [ ] disallow untrusted pickle/joblib loads.
- [ ] use `safetensors` for model weights where feasible.

---

# 35. Phase 31 — Operations and Incident Response

Create:

- `docs/OPERATIONS.md`
- `docs/INCIDENT_RESPONSE.md`

Runbooks:

1. LLM provider outage.
2. database outage.
3. policy misconfiguration.
4. accidental over-blocking.
5. suspected unauthorized ALLOW.
6. simulator mismatch.
7. compromised credential.
8. trace-store compromise.
9. rollback release.
10. restore database.

For unauthorized ALLOW:

```text
freeze affected capability
preserve audit evidence
identify policy/tool/model versions
replay incident
diff simulation/execution
notify owner
patch
add regression
re-run sealed safety suite
only then re-enable
```

---

# 36. Phase 32 — Backup and Disaster Recovery

**Priority:** P0

Define:

- RPO;
- RTO;
- backup frequency;
- restore procedure;
- artifact recovery;
- secret recovery;
- policy bundle recovery.

Initial targets:

- RPO <= 15 minutes for production state.
- RTO <= 1 hour for single-region recovery.

Test restoration quarterly or before production launch.

---

# 37. Phase 33 — Versioning

Use independent versions for:

```text
application
contract schema
tool schema
policy bundle
prompt template
model
benchmark dataset
replay bundle
trace schema
```

Never overload one app version to imply all compatibility.

Add compatibility matrix.

---

# 38. Phase 34 — API Versioning

Production endpoints:

```text
/api/v1/invoke
/api/v1/approvals
/api/v1/traces
```

Rules:

- additive backward-compatible fields within v1;
- breaking semantic changes require v2;
- reason codes are part of public contract;
- document deprecation window.

---

# 39. Phase 35 — Reason-Code Governance

Reason codes are operationally important.

Create registry:

```text
AUTH_INVALID
AUTH_SCOPE_MISSING
ENTITY_AMBIGUOUS
TEMPORAL_SCOPE_MISSING
TEMPORAL_SCOPE_TOO_BROAD
ATTRIBUTE_NOT_ALLOWED
CARDINALITY_EXCEEDED
APPROVAL_REQUIRED
EVIDENCE_CONTRADICTS
EVIDENCE_INSUFFICIENT
TOOL_SCHEMA_INVALID
SIMULATION_FAILED
SIMULATION_EXECUTION_MISMATCH
PROVIDER_UNAVAILABLE
COMPILER_INVALID_OUTPUT
POLICY_UNAVAILABLE
```

Tasks:

- [ ] central enum;
- [ ] docs;
- [ ] tests;
- [ ] dashboards;
- [ ] no ad-hoc strings;
- [ ] stable semantics across patch releases.

---

# 40. Phase 36 — Performance Engineering

Profile before optimizing.

Measure:

- language normalization;
- model request;
- entity resolution;
- retrieval;
- NLI;
- simulation;
- gate;
- DB execute;
- trace write.

Do not optimize deterministic gate code before proving the LLM/provider is not the dominant latency source.

Add:

- connection pooling;
- provider client reuse;
- bounded caches;
- policy cache keyed by hash;
- evidence index warmup;
- asynchronous non-critical analytics.

Never cache authorization decisions without including all relevant state/version keys.

---

# 41. Phase 37 — Research-Grade Evidence Package

For paper/Q1 readiness, keep production evidence and research evidence separate but linked.

Create immutable release folder externally (GitHub Release/Zenodo):

```text
release-evidence/
  protocol.pdf
  dataset_manifest.json
  environment.txt
  git_sha.txt
  policy_bundle/
  prompt_templates/
  benchmark_results.parquet
  summary.json
  plots/
  checksums.sha256
```

Required experiments:

- full vs raw LLM;
- full vs structured-output-only;
- full vs no simulator;
- full vs no evidence;
- cloud vs local model;
- per-language;
- prompt injection;
- ambiguity;
- overbroad scope;
- effect equivalence;
- latency/cost;
- fail-closed behavior.

Do not call a low-accuracy local model "proof of safety." Instead show:

```text
model degradation increases compiler failures;
deterministic gate prevents a defined class of unsafe executions;
utility may fall because the system blocks/clarifies more.
```

---

# 42. Phase 38 — Cost Controls

Production LLM traffic needs budget constraints.

Add:

- max tokens;
- max repair passes = 1 by default;
- provider timeout;
- per-tenant quota;
- cached static policy embeddings;
- cost metric;
- provider call count.

Never reduce security checks to save cost.

---

# 43. Phase 39 — UI/UX for Safe Decisions

The dashboard should explain decisions without exposing sensitive internals.

For each decision display:

```text
verdict
reason code
verified actor
intent
resolved target
resolved time scope
predicted affected rows
policy version
evidence refs
approval requirement
```

Do not display:

- raw system prompt;
- provider secret;
- hidden chain-of-thought;
- unrelated tenant evidence.

---

# 44. Phase 40 — Minimal Production Scope Recommendation

Do **not** launch every current idea at once.

## v1.0 production-supported surface

Recommend:

- authenticated single-tenant or strongly isolated multi-tenant API;
- English + Hinglish + Telugu + Romanized Telugu;
- `invoice.archive` only;
- one validated policy bundle family;
- PostgreSQL production backend;
- full audit/replay;
- human approval for large cardinality;
- cloud structured-output model plus optional qualified local model;
- fail-closed on provider failure.

## v1.1

Add only after validation:

- access.grant;
- access.block.

## v1.2

Add:

- limit.update;
- vendor.suspend.

High-risk financial/refund/share/delete operations should have separate threat models and approvals before enablement.

---

# 45. Exact Priority Backlog

## P0 — must complete before production

- [ ] Remove duplicate repo tree.
- [ ] Reconcile docs.
- [ ] Move CI to repo root.
- [ ] Add lock file.
- [ ] Clean dependency groups.
- [ ] Implement typed settings.
- [ ] Add AuthN.
- [ ] Add RBAC.
- [ ] Remove actor role from trusted request fields.
- [ ] Disable demo reset in production.
- [ ] Lock CORS.
- [ ] Add rate limiting.
- [ ] Add size limits.
- [ ] Fix CLARIFY/BLOCK response null handling.
- [ ] Remove hard-coded 2025.
- [ ] Replace mock entity resolution.
- [ ] Centralize provider adapters.
- [ ] Add provider timeout/retry classification.
- [ ] Centralize tool registry.
- [ ] Fully productionize `invoice.archive`.
- [ ] Move policy out of Python constants.
- [ ] Add policy hash/version/rollback.
- [ ] Harden evidence ACL.
- [ ] Add prompt-injection evidence tests.
- [ ] Add state-versioned simulation.
- [ ] Add transaction-safe execution.
- [ ] Add idempotency.
- [ ] Roll back on simulator mismatch.
- [ ] Add PostgreSQL adapter.
- [ ] Add migrations.
- [ ] Add trace redaction.
- [ ] Add trace retention policy.
- [ ] Add production replay bundles.
- [ ] Add sealed benchmark split.
- [ ] Replace 80% accuracy release gate with multi-metric safety gate.
- [ ] Reach multilingual equivalence target.
- [ ] Reach authorized ALLOW target.
- [ ] Demonstrate zero observed unauthorized ALLOW on release suite.
- [ ] Add root security workflow.
- [ ] Add secret scan.
- [ ] Add SBOM.
- [ ] Add dependency scan.
- [ ] Add structured logging.
- [ ] Add metrics.
- [ ] Add OTel tracing.
- [ ] Add readiness probe.
- [ ] Add backup/restore test.
- [ ] Write incident response.
- [ ] Tag release candidate.
- [ ] Reproduce all evidence from release candidate.

## P1 — required for enterprise maturity

- [ ] Full approval workflow.
- [ ] Digital signatures for audit bundles if required.
- [ ] tenant retention controls.
- [ ] dashboard RBAC.
- [ ] incremental trace analytics.
- [ ] load testing.
- [ ] chaos tests.
- [ ] provider cost/quota controls.
- [ ] model governance.
- [ ] policy signing.
- [ ] data export/deletion.
- [ ] staged rollout/canary.
- [ ] automated rollback trigger.

## P2 — after stable v1

- [ ] more tools/intents;
- [ ] more languages;
- [ ] multi-region;
- [ ] Kubernetes if justified;
- [ ] streaming trace pipeline if volume requires it;
- [ ] more sophisticated learned NLI if deterministic baseline is insufficient;
- [ ] formal verification of selected gate invariants.

---

# 46. Recommended 10-Phase Execution Sequence

## Phase A — Stabilize repository

Duration unit: milestone, not calendar promise.

Deliverables:

- one source tree;
- current README;
- root CI;
- frozen dependencies.

Exit test:

```bash
make bootstrap
make lint
make test
```

on a clean clone.

## Phase B — Identity and API security

Deliver:

- JWT/OIDC;
- RBAC;
- safe CORS;
- dev-only admin routes;
- rate limits.

Exit:

all auth/security tests pass.

## Phase C — Compiler correctness

Deliver:

- clock injection;
- real entity repository;
- provider abstraction;
- calibrated clarification behavior.

Exit:

contract field F1 target on dev set.

## Phase D — Policy/tool determinism

Deliver:

- external policy bundle;
- tool registry;
- archive capability fully bounded.

Exit:

all tool-policy property tests pass.

## Phase E — Transaction safety

Deliver:

- Postgres;
- versioned simulation;
- idempotency;
- rollback on mismatch.

Exit:

concurrency suite passes with zero duplicate/unpredicted effects.

## Phase F — Evidence and privacy

Deliver:

- ACL hardening;
- poisoning tests;
- redacted traces;
- retention controls.

Exit:

zero evidence leakage on adversarial set.

## Phase G — Replay and observability

Deliver:

- deterministic replay bundle;
- OTel/logging/metrics;
- incident alerts.

Exit:

replay corpus passes.

## Phase H — Benchmark qualification

Deliver:

- sealed multilingual benchmark;
- baselines;
- ablations;
- safety release gates.

Exit:

all quantitative P0 targets pass.

## Phase I — Operational qualification

Deliver:

- load test;
- chaos test;
- backup restore;
- staging deployment;
- runbooks.

Exit:

staging readiness review passes.

## Phase J — Release

Deliver:

- tagged `v1.0.0`;
- immutable evidence package;
- SBOM;
- image digest;
- security review;
- exact production config docs.

---

# 47. Production Readiness Scorecard Template

Do not mark "Production Ready" until this table is complete.

| Area | Gate | Status | Evidence |
|---|---|---|---|
| Repository | one canonical tree | ⬜ | |
| Build | frozen clean-clone install | ⬜ | |
| CI | root workflow required | ⬜ | |
| AuthN | verified identity | ⬜ | |
| AuthZ | RBAC/tenant isolation | ⬜ | |
| API | rate/size/CORS hardening | ⬜ | |
| Compiler | no demo assumptions | ⬜ | |
| Entity | real scoped resolver | ⬜ | |
| Policy | versioned external bundle | ⬜ | |
| Evidence | ACL + poisoning tests | ⬜ | |
| Tools | capability registry | ⬜ | |
| Simulation | snapshot-safe | ⬜ | |
| Execution | transactional/idempotent | ⬜ | |
| Fidelity | predicted=actual | ⬜ | |
| Database | production concurrency | ⬜ | |
| Audit | redaction/integrity | ⬜ | |
| Replay | deterministic bundle | ⬜ | |
| Multilingual | equivalence passed | ⬜ | |
| Benchmark | sealed release suite | ⬜ | |
| Security | threat model/red team | ⬜ | |
| Observability | logs/metrics/OTel | ⬜ | |
| SLO | load test meets target | ⬜ | |
| Backup | restore proven | ⬜ | |
| Incident | runbooks exercised | ⬜ | |
| Release | signed/tagged evidence | ⬜ | |

---

# 48. Commands the Final Repository Should Support

From repository root:

```bash
make bootstrap
make lint
make typecheck
make test-unit
make test-integration
make test-regression
make test-replay
make test-security
make test-property
make test-all
make benchmark-smoke
make benchmark-offline
make replay-ci
make docker-build
make docker-smoke
make sbom
make security-scan
make verify
```

Production/staging:

```bash
make migrate
make readiness
make backup
make restore-verify
```

Research:

```bash
make benchmark-release RUN_ID=2026-09-17-v1
make verify-artifact RUN_ID=2026-09-17-v1
```

---

# 49. Final Release Checklist

## Code

- [ ] clean working tree;
- [ ] tests pass;
- [ ] mypy pass;
- [ ] ruff pass;
- [ ] no critical/high vulnerabilities;
- [ ] no committed secrets;
- [ ] no demo endpoints enabled in prod;
- [ ] lock file verified.

## Security

- [ ] JWT/OIDC verified;
- [ ] roles server-derived;
- [ ] tenant tests passed;
- [ ] evidence ACL tests passed;
- [ ] prompt-injection tests passed;
- [ ] simulator mismatch rollback tested;
- [ ] policy tamper tested;
- [ ] audit tamper tested.

## Data/ML

- [ ] sealed benchmark;
- [ ] data hashes;
- [ ] model IDs;
- [ ] prompt hashes;
- [ ] per-language metrics;
- [ ] CIs;
- [ ] false-ALLOW hard gate;
- [ ] authorized ALLOW recall;
- [ ] CLARIFY recall;
- [ ] effect equivalence;
- [ ] ablations.

## Operations

- [ ] staging deployment;
- [ ] load test;
- [ ] chaos test;
- [ ] backup;
- [ ] restore;
- [ ] rollback;
- [ ] alert test;
- [ ] incident drill.

## Documentation

- [ ] README accurate;
- [ ] architecture accurate;
- [ ] threat model;
- [ ] security model;
- [ ] data governance;
- [ ] model policy;
- [ ] benchmark protocol;
- [ ] operations;
- [ ] incident response;
- [ ] release process;
- [ ] API reference.

## Release evidence

- [ ] Git tag;
- [ ] source SHA;
- [ ] image digest;
- [ ] SBOM;
- [ ] benchmark artifact hash;
- [ ] dataset hash;
- [ ] environment manifest;
- [ ] release notes;
- [ ] known limitations.

---

# 50. What "100% Complete" Means for NiyamTrace-X

Do **not** define 100% as "every idea has been implemented."

Define 100% for v1.0 as:

> NiyamTrace-X supports a deliberately bounded set of multilingual, authenticated enterprise tool operations; every supported operation is typed, policy-governed, simulated, deterministically gated, transactionally executed, auditable and replayable; all security-sensitive identity and access information is server-verified; benchmark evidence shows strong authorized utility with no observed unauthorized ALLOW on the sealed safety suite; production operations are observable, recoverable and documented.

Anything beyond that is v1.1+ scope.

---

# 51. Immediate Next 20 Tasks — Execute in This Exact Order

1. [ ] Tag current baseline.
2. [ ] Remove/archive duplicate nested tree.
3. [ ] Move CI to root `.github/workflows/`.
4. [ ] Correct README/status docs.
5. [ ] Split runtime/dev dependencies and create lock file.
6. [ ] Add typed settings and `APP_ENV`.
7. [ ] Add auth principal model.
8. [ ] Remove `actor_role`/`actor_id` trust from request body.
9. [ ] Disable/reset admin route in production.
10. [ ] Restrict CORS.
11. [ ] Fix CLARIFY/BLOCK API null handling.
12. [ ] Remove hard-coded year 2025.
13. [ ] Replace mock entity resolution with repository interface.
14. [ ] Externalize policy bundle.
15. [ ] Create capability registry for `invoice.archive`.
16. [ ] Add transactional simulation/execution and idempotency.
17. [ ] Implement trace redaction.
18. [ ] Redesign benchmark release gates.
19. [ ] Build 5,000-case sealed multilingual safety suite.
20. [ ] Run staging qualification: security + replay + load + backup/restore.

Only after these should you expand to new tool capabilities.

---

# 52. Final Engineering Principle

The strongest version of NiyamTrace-X is **not** the version with the most agents, models, languages, or integrations.

It is the version where:

```text
the model can be wrong,
the user can be malicious,
the evidence can be poisoned,
the provider can fail,
the database can change,
the request can be retried,
and the system still does not perform an effect outside the authenticated,
policy-approved, simulated and verified envelope.
```

That is the production-grade bar.
