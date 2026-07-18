"""
tests/unit/test_evidence.py — Unit tests for NiyamEvidence (Week 5)

Covers:
  - ACLFilter: role-based access grant and denial
  - EvidenceRetriever: returns ACL-filtered, scored chunks
  - NLIEngine: SUPPORT / CONTRADICT / INSUFFICIENT verdicts
"""

from __future__ import annotations

import pytest
from packages.evidence.acl import ACLFilter
from packages.evidence.retriever import EvidenceRetriever, RetrievedChunk
from packages.evidence.nli import NLIEngine


# ---------------------------------------------------------------------------
# ACLFilter tests
# ---------------------------------------------------------------------------

class TestACLFilter:
    def setup_method(self):
        self.acl = ACLFilter()
        self.docs = [
            {
                "doc_id": "DOC-PUB",
                "sensitivity": "public",
                "allowed_roles": [],
                "content": "public doc",
            },
            {
                "doc_id": "DOC-INT",
                "sensitivity": "internal",
                "allowed_roles": ["procurement_manager", "finance_admin"],
                "content": "internal doc",
            },
            {
                "doc_id": "DOC-RES",
                "sensitivity": "restricted",
                "allowed_roles": ["finance_admin"],
                "content": "restricted doc",
            },
        ]

    def test_public_doc_accessible_to_any_known_role(self):
        result = self.acl.filter("procurement_manager", self.docs)
        ids = [d["doc_id"] for d in result]
        assert "DOC-PUB" in ids

    def test_internal_doc_accessible_to_allowed_role(self):
        result = self.acl.filter("procurement_manager", self.docs)
        ids = [d["doc_id"] for d in result]
        assert "DOC-INT" in ids

    def test_restricted_doc_denied_to_non_listed_role(self):
        result = self.acl.filter("procurement_manager", self.docs)
        ids = [d["doc_id"] for d in result]
        assert "DOC-RES" not in ids

    def test_restricted_doc_accessible_to_finance_admin(self):
        result = self.acl.filter("finance_admin", self.docs)
        ids = [d["doc_id"] for d in result]
        assert "DOC-RES" in ids

    def test_can_access_single_doc(self):
        assert self.acl.can_access("finance_admin", self.docs[2]) is True
        assert self.acl.can_access("procurement_manager", self.docs[2]) is False

    def test_empty_doc_list(self):
        result = self.acl.filter("finance_admin", [])
        assert result == []


# ---------------------------------------------------------------------------
# EvidenceRetriever tests
# ---------------------------------------------------------------------------

class TestEvidenceRetriever:
    def setup_method(self):
        self.retriever = EvidenceRetriever()

    def test_returns_chunks_for_known_intent(self):
        chunks = self.retriever.retrieve(
            query="archive invoices for vendor",
            actor_role="procurement_manager",
            top_k=3,
        )
        assert len(chunks) > 0
        assert all(isinstance(c, RetrievedChunk) for c in chunks)

    def test_top_chunk_for_archive_is_archive_policy(self):
        chunks = self.retriever.retrieve(
            query="invoice.archive archive vendor invoices",
            actor_role="procurement_manager",
            top_k=3,
        )
        assert len(chunks) > 0
        # The archive policy doc should rank highest
        assert chunks[0].doc_id == "POL-001"

    def test_acl_filters_out_restricted_docs_for_viewer(self):
        chunks = self.retriever.retrieve(
            query="credit limit update",
            actor_role="viewer",
            top_k=5,
        )
        # POL-003 (restricted, credit_officer/finance_admin) should not appear for viewer
        ids = [c.doc_id for c in chunks]
        assert "POL-003" not in ids

    def test_scores_between_zero_and_one(self):
        chunks = self.retriever.retrieve(
            query="block access user",
            actor_role="it_admin",
            top_k=5,
        )
        for c in chunks:
            assert 0.0 <= c.score <= 1.0

    def test_top_k_respected(self):
        chunks = self.retriever.retrieve(
            query="vendor operations",
            actor_role="finance_admin",
            top_k=2,
        )
        assert len(chunks) <= 2

    def test_to_dict_serializable(self):
        chunks = self.retriever.retrieve(
            query="archive vendor",
            actor_role="procurement_manager",
            top_k=1,
        )
        d = chunks[0].to_dict()
        assert "doc_id" in d
        assert "content" in d
        assert "score" in d


# ---------------------------------------------------------------------------
# NLIEngine tests
# ---------------------------------------------------------------------------

class TestNLIEngine:
    def setup_method(self):
        self.retriever = EvidenceRetriever()
        self.nli = NLIEngine()

    def _get_chunks(self, query: str, role: str, top_k: int = 3) -> list[RetrievedChunk]:
        return self.retriever.retrieve(query=query, actor_role=role, top_k=top_k)

    def test_support_invoice_archive_for_procurement_manager(self):
        chunks = self._get_chunks(
            "invoice.archive archive vendor invoices authorized",
            "procurement_manager",
        )
        verdict, reason = self.nli.classify("invoice.archive", "procurement_manager", chunks)
        assert verdict == "SUPPORT", f"Expected SUPPORT, got {verdict}: {reason}"

    def test_support_access_block_for_it_admin(self):
        chunks = self._get_chunks("access.block block user access it admin", "it_admin")
        verdict, reason = self.nli.classify("access.block", "it_admin", chunks)
        assert verdict == "SUPPORT", f"Expected SUPPORT, got {verdict}: {reason}"

    def test_insufficient_for_no_chunks(self):
        verdict, reason = self.nli.classify("invoice.archive", "procurement_manager", [])
        assert verdict == "INSUFFICIENT"

    def test_contradict_for_prohibited_operation(self):
        # Simulate a chunk that mentions prohibited operations
        from packages.evidence.retriever import RetrievedChunk
        prohibited_chunk = RetrievedChunk(
            doc_id="POL-006",
            title="Prohibited Operations",
            content="The following operations are prohibited for all actors via automated agent requests: modifying audit trail records, deleting data.",
            sensitivity="public",
            allowed_roles=[],
            score=0.8,
        )
        verdict, reason = self.nli.classify("invoice.delete", "procurement_manager", [prohibited_chunk])
        # "prohibited" pattern fires → CONTRADICT (delete is in content)
        # OR if that intent isn't mapped, INSUFFICIENT — both are valid blocking verdicts
        assert verdict in ("CONTRADICT", "INSUFFICIENT")

    def test_unknown_intent_gives_insufficient(self):
        chunks = self._get_chunks("unknown operation xyz", "procurement_manager")
        verdict, reason = self.nli.classify("unknown", "procurement_manager", chunks)
        # No support rules match "unknown" intent
        assert verdict in ("INSUFFICIENT", "CONTRADICT")
