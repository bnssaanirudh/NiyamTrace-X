# NiyamTrace — Design Decisions

This file records every non-trivial default choice made during development.
Each entry: decision, rationale, alternatives considered, and the week in which
it can be revisited if needed.

Honest-claims rule: if a decision implies a limitation (e.g., no LLM in Week 2),
the limitation is stated explicitly alongside the decision.

---

## §1 — Data Ethics

**Decision**: Synthetic data only. No real PII, employee, medical, financial, or
customer data anywhere in the repo, including tests, demos, or notebooks.

**Rationale**: The NiyamTrace brief (Section 12) makes this a hard constraint.
Tracing and replay bundles must be safe to commit, share, and publish.

**Implementation**: All vendor names, amounts, IDs, and invoice data in
`data/synthetic/` are fabricated. Tests use in-memory SQLite seeded from the
same synthetic seed.

---

## §2 — SQLite: File-backed vs. In-Memory

**Decision**: The production ERP (`data/synthetic/erp.db`) is file-backed.
Tests use in-memory SQLite (`:memory:`) seeded via `reset_to_seed()`.

**Rationale**:
- File-backed: allows replay bundles to include a DB snapshot and allows the
  gateway to persist state across restarts during demos.
- In-memory for tests: guarantees isolation (no inter-test contamination),
  no disk I/O, fast.

**Implication**: Tests must always use the `fresh_erp` pytest fixture, never
the on-disk `erp.db` directly.

**Revisit**: Week 7 (NiyamLake) — add a `data_snapshot_id` backup/restore
mechanism so replay bundles can include the ERP state.

---

## §3 — "Deletion" = Retrieval-Layer Tombstoning

**Decision**: Deleting a record in NiyamTrace means setting `status='TOMBSTONED'`.
The record is never physically removed from `vendor_invoices`.

**Rationale**: Physical deletion breaks replay determinism, audit trails, and
NiyamTrace-Bench reproducibility. Retrieval-layer tombstoning means the record
is invisible to all normal queries (the simulator and executor filter it out)
while remaining auditable.

**Explicit label requirement**: Every place "deletion" is mentioned in docs,
UI copy, or README must state: *"Deletion = retrieval-layer tombstoning only."*

**Implication**: This is NOT the same as making data mathematically irretrievable
from LLM model weights. We do not claim unlearning.

---

## §4 — No LLM Calls in Weeks 0–2

**Decision**: The entire Week 0–2 pipeline is deterministic. No Ollama calls,
no network requests, no external model dependencies.

**Rationale**: The spine (contract → tool → delta → gate → trace) must be
fully testable offline and fast before any model is introduced. Adding an LLM
before the spine works would make failures ambiguous.

**Implementation**: The contract extractor in `apps/gateway/pipeline.py` is a
hard-coded rule-based function (`_extract_contract_hardcoded`) for the single
canonical scenario. Clearly labeled `STUB — Week 4 replaces with NLP slot-parser`.

**Revisit**: Week 4 — the NLP slot-parser (XLM-R or local LLM via Ollama)
replaces `_extract_contract_hardcoded`.

---

## §5 — Tool Vocabulary Is Deliberately Small and Explicit

**Decision**: The controlled action vocabulary for Week 2 is exactly:
`VIEW | ARCHIVE | DELETE | SHARE | REFUND | UPDATE`.
The tool registry contains only `archive_invoices`.

**Rationale**: Small, explicit vocabularies prevent scope creep via free-text
injection. New actions and tools are added intentionally, not inferred.

**Revisit**: Week 4–5 — extend vocabulary as new scenario categories are added
to NiyamTrace-Bench.

---

## §6 — Evidence Check (Gate Check 5) Is Stubbed in Week 2

**Decision**: Gate Check 5 (evidence sufficiency) always returns `SUPPORT` in
Week 2, labeled as `STUB_ALWAYS_SUPPORT` in the reason code.

**Rationale**: The NLI/RAG pipeline (NiyamEvidence) is a Week 5 deliverable.
The gate still enforces checks 1–4 in Week 2, which are sufficient to block
the most critical unauthorized-effect classes (wrong vendor, wrong time, wrong
attributes, excessive cardinality).

**Implication**: Do NOT make any security claim about evidence-based blocking
until Week 5 is implemented and tested. The stub is explicitly labeled in
`packages/gate/policy.py`.

**Revisit**: Week 5 — wire real NLI verdict from NiyamEvidence into gate.

---

## §7 — JSONL-First Tracing (Bronze Layer Only in Weeks 0–2)

**Decision**: Traces are written as JSONL files (Bronze layer only) in Weeks
0–2. Parquet (Silver) and DuckDB (Gold) transforms are Week 7 scope.

**Rationale**: JSONL is human-readable, appendable, and requires no schema
migration. It is the right format for the early spine where trace schema is
still evolving.

**Revisit**: Week 7 — add `packages/lake/transform.py` for JSONL → Parquet,
and `packages/lake/metrics.py` for DuckDB Gold-layer queries.

---

## §8 — Tool Schema Validation: Manual vs. `jsonschema` Library

**Decision**: Tool call validation in `packages/gate/tool_schemas.py` is
implemented manually (not using the `jsonschema` Python library).

**Rationale**: Keeps dependencies minimal for the MVP. The validation logic
for `archive_invoices` is simple enough (3 integer fields with range constraints)
that manual validation is readable and testable.

**Revisit**: Week 5 — when more tools are added, consider `jsonschema` or
`pydantic-based` schema validation.

---

## §9 — No Neo4j, Postgres, Kafka, Kubernetes

**Decision**: The MVP uses only SQLite (ERP + access graph), JSONL/Parquet
(trace lake), and DuckDB (Gold layer). Heavy infrastructure is explicitly
out of scope until after P0.

**Rationale**: Per Section 8 of the brief: "Do NOT introduce Kafka, Neo4j,
Postgres, Kubernetes, or any heavy infra until the P0 path above is fully
working."

**Revisit**: Post-Week 9 hardening only if scale-out is required.
