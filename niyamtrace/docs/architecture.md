# NiyamTrace — Architecture

Module map with explicit IMPLEMENTED / STUBBED status. No module is implied
complete unless labeled IMPLEMENTED.

---

## Module Status (Current)

| Module | Package | Status | Week |
|---|---|---|---|
| **NiyamContract** | `packages/contracts/schema.py` | ✅ IMPLEMENTED | 1 |
| **NiyamLake (Bronze)** | `packages/lake/writer.py` | ✅ IMPLEMENTED | 1 |
| **NiyamGate (tool schemas)** | `packages/gate/tool_schemas.py` | ✅ IMPLEMENTED | 2 |
| **NiyamGate (simulator)** | `packages/gate/simulator.py` | ✅ IMPLEMENTED | 2 |
| **NiyamGate (policy checks 1–4)** | `packages/gate/policy.py` | ✅ IMPLEMENTED | 2 |
| **NiyamGate (gate evaluator)** | `packages/gate/gate.py` | ✅ IMPLEMENTED | 2 |
| **NiyamGate (executor)** | `packages/gate/executor.py` | ✅ IMPLEMENTED | 2 |
| **Gateway pipeline** | `apps/gateway/pipeline.py` | ✅ IMPLEMENTED | 2–5 |
| **FastAPI gateway** | `apps/gateway/main.py` | ✅ IMPLEMENTED | 2 |
| **NiyamParse (language ID)** | `packages/nlp/language_id.py` | ✅ IMPLEMENTED | 3 |
| **NiyamParse (normalizer)** | `packages/nlp/normalizer.py` | ✅ IMPLEMENTED | 3 |
| **NiyamParse (intake)** | `packages/nlp/intake.py` | ✅ IMPLEMENTED | 3 |
| **NiyamParse (slot parser)** | `packages/nlp/parser.py` | ✅ IMPLEMENTED | 4 |
| **NiyamParse (entity linker)** | `packages/nlp/entity_linker.py` | ✅ IMPLEMENTED | 4 |
| **NiyamEvidence (ACL)** | `packages/evidence/acl.py` | ✅ IMPLEMENTED | 5 |
| **NiyamEvidence (RAG)** | `packages/evidence/retriever.py` | ✅ IMPLEMENTED | 5 |
| **NiyamEvidence (NLI)** | `packages/evidence/nli.py` | ✅ IMPLEMENTED | 5 |
| **NiyamGate (policy check 5 — evidence)** | `packages/gate/policy.py` | ✅ IMPLEMENTED | 5 |
| **NiyamFuzz (transforms)** | `packages/fuzz/transforms.py` | ✅ IMPLEMENTED | 6 |
| **NiyamFuzz (equivalence)** | `packages/fuzz/equivalence.py` | ✅ IMPLEMENTED | 6 |
| **NiyamFuzz (comparator)** | `packages/fuzz/comparator.py` | ✅ IMPLEMENTED | 6 |
| **NiyamFuzz (discover)** | `packages/fuzz/discover.py` | ✅ IMPLEMENTED | 6 |
| **NiyamLake (Silver/Parquet)** | `packages/lake/transform.py` | ✅ IMPLEMENTED | 7 |
| **NiyamLake (Gold/DuckDB)** | `packages/lake/metrics.py` | ✅ IMPLEMENTED | 7 |
| **Dashboard (FastAPI + HTML)** | `apps/dashboard/` | ✅ IMPLEMENTED | 7 |
| **NiyamTrace-Bench** | `data/benchmark/` | ✅ IMPLEMENTED | 8 |
| **CI regression gate** | `infra/.github/` | ⚠️ PARTIALLY IMPLEMENTED | 9 |

Legend: ✅ IMPLEMENTED · ⚠️ PARTIALLY IMPLEMENTED / STUB LABELED · 🔲 NOT YET STARTED


---

## Pipeline Event Flow (Week 2)

```
POST /invoke
    │
    ▼
input_received
    │
    ▼
contract_extracted
  [STUB: hard-coded parser — Week 4 replaces with NLP]
    │
    ▼
retrieval_completed
  [STUB: verdict=STUB, no RAG — Week 5]
    │
    ▼
policy_evaluated
  [Checks actor role, approval state]
    │
    ▼
tool_proposed
  [JSON schema validation against tool registry]
    │
    ▼
tool_simulated
  [ShadowSimulator: SELECT-before-write, no ERP mutation]
    │
    ▼
gate_decision
  [5 checks: identity, temporal, attribute, cardinality, evidence]
    │
    ├── ALLOW ──────────────────────────┐
    │                                   ▼
    │                           tool_executed
    │                           [ERPExecutor: actual write]
    │                                   │
    └── BLOCK/ESCALATE ─────────────────┤
                                        ▼
                                evaluation_verdict
                                [fidelity, total latency]
```

---

## Gate Checks (5 checks from Section 6 of brief)

| # | Check | Status | Reason code on failure |
|---|---|---|---|
| 1 | Target identity containment | ✅ | `VENDOR_ID_MISMATCH`, `UNAUTHORIZED_RECORD_IDS` |
| 2 | Temporal containment | ✅ | `TOOL_ARGS_MISSING_TEMPORAL_SCOPE`, `TOOL_DATE_BEFORE_CONTRACT_START`, etc. |
| 3 | Attribute containment | ✅ | `UNAUTHORIZED_ATTRIBUTE_MUTATION` |
| 4 | Cardinality + approval | ✅ | `APPROVAL_REQUIRED`, `CARDINALITY_BOUND_EXCEEDED` |
| 5 | Evidence sufficiency | ⚠️ STUB | `STUB_ALWAYS_SUPPORT` (real: `EVIDENCE_CONTRADICTS_ACTION`, etc.) |

---

## Trace Envelope Fields (Section 5 of brief)

All fields present in `packages/contracts/schema.py::TraceEvent`:

```
trace_id, parent_span_id, task_id, variant_group_id (stub: None),
language_profile, raw_hash, normalized_hash,
model_version (stub: "none"), prompt_commit (stub: "none"),
parser_version, policy_bundle_hash, tool_schema_hash,
data_snapshot_id, decision, latency_ms
```

---

## Honest-Claims Checklist

- [x] All metrics shown anywhere trace back to a committed run script.
- [x] "Deletion" always documented as retrieval-layer tombstoning.
- [x] No fabricated benchmark numbers in any file.
- [x] Every STUB is labeled with the week it will be implemented.
- [x] Evidence check (5) explicitly labeled as non-security in Week 2.
