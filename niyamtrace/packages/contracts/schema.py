"""
NiyamContract — Typed Intent-to-Effect Schema (packages/contracts/schema.py)

Implements the IntentContract Pydantic model exactly as specified in the
NiyamTrace brief (Section 4) plus supporting types for trace events,
gate decisions, and state-delta representations.

Status: IMPLEMENTED (Weeks 0–2)
"""

from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timezone as _tz
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator


# ---------------------------------------------------------------------------
# Supporting sub-models
# ---------------------------------------------------------------------------


class TemporalRange(BaseModel):
    """Closed temporal interval.  At least one of start/end must be present."""

    start: datetime | None = None
    end: datetime | None = None
    # If True the range was inferred (e.g. "March" → Jan of which year?)
    inferred: bool = False

    @model_validator(mode="after")
    def at_least_one_bound(self) -> "TemporalRange":
        if self.start is None and self.end is None:
            raise ValueError("TemporalRange must have at least one of start or end.")
        return self


class ContractAction(str):
    """Controlled vocabulary for allowed actions.
    Extend deliberately — not via free text injection.
    Current vocabulary: VIEW | ARCHIVE | DELETE | SHARE | REFUND | UPDATE
    """


# ---------------------------------------------------------------------------
# Core contract model (Section 4 of brief — reproduced exactly)
# ---------------------------------------------------------------------------


class SourceSpan(BaseModel):
    """Traces a parsed slot back to its source text."""
    slot: str
    raw_text: str
    normalized_text: str
    confidence: float = Field(ge=0.0, le=1.0)


class ActionContract(BaseModel):
    """
    Typed intent-to-effect contract produced by NiyamParse (Week 4 Slot Parser).
    Replaces IntentContract by using discrete intent strings and a dynamic slots dictionary.
    """
    contract_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    actor_id: str
    actor_role: str
    
    intent: str
    intent_confidence: float = Field(ge=0.0, le=1.0)
    
    slots: dict[str, Any] = Field(default_factory=dict)
    source_spans: list[SourceSpan] = Field(default_factory=list)
    
    requires_review: bool = False
    
    raw_text: str
    normalized_text: str
    language_profile: dict[str, Any] = Field(default_factory=dict)
    
    parser_version: str = "0.4.0"

    @model_validator(mode="after")
    def validate_unknown_intent(self) -> "ActionContract":
        """If intent is unknown, it should require review."""
        if self.intent.lower() == "unknown":
            self.requires_review = True
        return self


class IntentContract(BaseModel):
    """
    Typed intent-to-effect contract produced by NiyamParse for every request.

    Rule: if a required field (e.g. date) cannot be confidently resolved,
    set ambiguity=True and route to clarification — never silently widen scope.
    """

    contract_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    actor_id: str
    actor_role: str

    action: Literal["VIEW", "ARCHIVE", "DELETE", "SHARE", "REFUND", "UPDATE"]

    object_type: str  # e.g. "vendor_invoice"
    entity_ids: list[str]  # empty → selector_predicate used instead
    allowed_attributes: list[str]  # explicit field-level permission list

    # Normalized AST/expression string — NOT free text.
    # Example: "vendor_id = 4421 AND month = 3 AND year = 2025"
    selector_predicate: str

    temporal_scope: TemporalRange | None = None
    cardinality_bound: int | None = None  # max records this action may touch

    purpose: str
    approval_state: Literal["NONE", "REQUIRED", "GRANTED"] = "NONE"

    ambiguity: bool = False
    confidence: float = Field(ge=0.0, le=1.0)

    raw_text: str
    normalized_text: str
    language_profile: dict[str, Any] = Field(default_factory=dict)

    # Provenance / versioning
    parser_version: str = "0.1.0-hardcoded"  # updated when NLP parser lands (Week 4)

    @field_validator("confidence")
    @classmethod
    def confidence_range(cls, v: float) -> float:
        if not 0.0 <= v <= 1.0:
            raise ValueError("confidence must be in [0, 1]")
        return v

    @model_validator(mode="after")
    def ambiguity_requires_no_scope_widening(self) -> "IntentContract":
        """If ambiguity=True, the contract must NOT have a wildcard selector."""
        if self.ambiguity and self.selector_predicate in ("*", "TRUE", "1=1"):
            raise ValueError(
                "Ambiguous contract must not use a wildcard selector predicate. "
                "Route to clarification instead of widening scope."
            )
        return self

    def normalized_hash(self) -> str:
        return hashlib.sha256(self.normalized_text.encode()).hexdigest()[:16]

    def raw_hash(self) -> str:
        return hashlib.sha256(self.raw_text.encode()).hexdigest()[:16]


# ---------------------------------------------------------------------------
# Tool call representation
# ---------------------------------------------------------------------------


class ToolCall(BaseModel):
    """A proposed tool invocation, produced after contract parsing."""

    tool_name: str
    arguments: dict[str, Any]
    schema_version: str = "1.0"
    tool_schema_hash: str = ""


class MultiToolContract(BaseModel):
    """
    A composite contract containing multiple independent tool calls 
    parsed from a single user intent (e.g. archive AND suspend).
    """
    contracts: list[ActionContract]
    tool_calls: list[ToolCall]


# ---------------------------------------------------------------------------
# State-delta representations (simulator output vs. actual execution output)
# ---------------------------------------------------------------------------


class RecordDelta(BaseModel):
    """Represents the change to a single ERP record."""

    record_id: str
    table: str
    field: str
    old_value: Any
    new_value: Any


class StateDelta(BaseModel):
    """
    Set of record-level changes produced by the simulator (predicted) or
    the executor (actual). The gate compares predicted ⊆ allowed_effects.
    """

    affected_record_ids: list[str]
    record_deltas: list[RecordDelta]
    table: str | list[str]  # string for single table, list for composite delta
    estimated_row_count: int

    def record_id_set(self) -> set[str]:
        return set(self.affected_record_ids)

    def __add__(self, other: "StateDelta") -> "StateDelta":
        """Aggregate two state deltas (e.g. for MultiToolContract)."""
        tables = set()
        if isinstance(self.table, list): tables.update(self.table)
        elif self.table: tables.add(self.table)
        
        if isinstance(other.table, list): tables.update(other.table)
        elif other.table: tables.add(other.table)

        return StateDelta(
            affected_record_ids=list(set(self.affected_record_ids + other.affected_record_ids)),
            record_deltas=self.record_deltas + other.record_deltas,
            table=sorted(tables) if len(tables) > 1 else (list(tables)[0] if tables else ""),
            estimated_row_count=self.estimated_row_count + other.estimated_row_count
        )


# ---------------------------------------------------------------------------
# Gate decision
# ---------------------------------------------------------------------------


class GateCheckResult(BaseModel):
    """Result of a single gate check (one of the 5 from Section 6)."""

    check_name: str
    passed: bool
    reason_code: str  # machine-readable — never a generic string
    detail: str


class GateDecision(BaseModel):
    """
    Final gate verdict. On BLOCK the reason_code is machine-readable so
    callers can programmatically route (not just log) the failure.
    """

    verdict: Literal["ALLOW", "BLOCK", "ESCALATE", "CLARIFY"]
    reason_code: str  # e.g. "TEMPORAL_SCOPE_TOO_BROAD", "APPROVAL_REQUIRED"
    detail: str
    check_results: list[GateCheckResult]
    latency_ms: float = 0.0

    # Structured correction payload (populated on BLOCK/ESCALATE)
    correction: dict[str, Any] | None = None
    clarification_prompt: str | None = None
    effect_certificate: Any | None = None
    policy_hash: str = ""


# ---------------------------------------------------------------------------
# Trace event envelope (Section 5 of brief)
# ---------------------------------------------------------------------------

EVENT_TYPES = Literal[
    "input_received",
    "contract_extracted",
    "retrieval_completed",
    "policy_evaluated",
    "tool_proposed",
    "tool_simulated",
    "gate_decision",
    "tool_executed",
    "evaluation_verdict",
]


class TraceEvent(BaseModel):
    """
    Unified trace envelope.  Every pipeline event produces one of these.
    All fields from Section 5 of the NiyamTrace brief are present.
    """

    # Identity
    trace_id: str
    parent_span_id: str | None = None
    task_id: str
    variant_group_id: str | None = None  # set by NiyamFuzz (Week 6)

    # Event metadata
    event_type: EVENT_TYPES
    timestamp: datetime = Field(default_factory=lambda: datetime.now(_tz.utc))
    latency_ms: float = 0.0

    # Language / provenance
    language_profile: dict[str, Any] = Field(default_factory=dict)
    raw_hash: str = ""
    normalized_hash: str = ""

    # Version hashes — all must be populated before gate decision
    model_version: str = "none"  # no LLM in Weeks 0–2
    prompt_commit: str = "none"
    parser_version: str = "0.1.0-hardcoded"
    policy_bundle_hash: str = ""
    tool_schema_hash: str = ""
    data_snapshot_id: str = ""  # hash of ERP seed state

    # Schema Versioning (#2.4)
    schema_version: str = "1.0"

    # Decision (populated from gate_decision event onward)
    decision: str = ""

    # Arbitrary payload (contract, delta, etc.) — stored as dict for JSONL
    payload: dict[str, Any] = Field(default_factory=dict)


class EffectCertificate(BaseModel):
    """
    Auditable proof object generated when an action is ALLOWed.

    Upgrade #21: Cryptographic Hash-Chaining (Merkle-style)
    --------------------------------------------------------
    Each certificate contains:
      - cert_hash: SHA-256 of the certificate's own canonical content.
      - prev_cert_hash: SHA-256 hash of the PREVIOUS certificate in the chain
        for this actor (or 'GENESIS' for the first).

    This makes the trace lake independently tamper-evident: if any historical
    certificate is altered, all downstream cert_hashes become invalid.
    """
    trace_id: str
    actor: str
    action: str
    target_type: str
    selector: dict[str, Any]
    policy_rules_used: list[str]
    evidence_refs: list[str]
    predicted_delta: dict[str, Any]  # rows_changed, fields_changed, before_hash, after_hash
    gate_decision: str = "ALLOW"
    timestamp: datetime = Field(default_factory=lambda: datetime.now(_tz.utc))

    # #21: Hash-chain fields
    prev_cert_hash: str = "GENESIS"   # SHA-256 of previous cert, or sentinel
    cert_hash: str = ""               # SHA-256 of THIS cert (computed on creation)

    # #22: Extraction confidence propagated into the certificate for auditors
    extraction_confidence: float | None = None
    repair_attempted: bool = False

    def compute_hash(self) -> str:
        """Compute the canonical SHA-256 hash of this certificate's core fields."""
        import json
        core = {
            "trace_id": self.trace_id,
            "actor": self.actor,
            "action": self.action,
            "target_type": self.target_type,
            "selector": self.selector,
            "policy_rules_used": sorted(self.policy_rules_used),
            "predicted_delta": self.predicted_delta,
            "gate_decision": self.gate_decision,
            "timestamp": self.timestamp.isoformat(),
            "prev_cert_hash": self.prev_cert_hash,
        }
        canonical = json.dumps(core, sort_keys=True, default=str)
        return hashlib.sha256(canonical.encode()).hexdigest()

    def seal(self) -> "EffectCertificate":
        """Compute and store the cert_hash. Call after construction."""
        self.cert_hash = self.compute_hash()
        return self

    def verify(self) -> bool:
        """Verify the cert_hash matches the current content (tamper detection)."""
        return self.cert_hash == self.compute_hash()

    @classmethod
    def chain_from(
        cls,
        prev: "EffectCertificate | None",
        **kwargs: Any,
    ) -> "EffectCertificate":
        """
        Factory: create a new certificate chained to the previous one.
        If prev is None this is the GENESIS certificate for this actor.
        """
        prev_hash = prev.cert_hash if prev else "GENESIS"
        cert = cls(prev_cert_hash=prev_hash, **kwargs)
        return cert.seal()
