"""
packages/evidence/retriever.py — Local TF-IDF Retriever (Week 5)

Indexes the synthetic policy document corpus (data/gold/policy_docs.json)
at construction time. Given a query text, returns the top-K most relevant
document chunks after applying the ACL filter.

Design:
  - No heavy ML dependencies: uses token overlap (Jaccard) + rapidfuzz
    partial_ratio for lightweight similarity. Fast, deterministic, offline.
  - ACL filter is applied BEFORE ranking — never exposes forbidden docs.
  - Returns RetrievedChunk objects with doc metadata for NLI consumption.

Status: IMPLEMENTED (Week 5)
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from rapidfuzz import fuzz

from packages.evidence.acl import ACLFilter

# Default path to policy document corpus
_DEFAULT_CORPUS = (
    Path(__file__).parent.parent.parent / "data" / "gold" / "policy_docs.json"
)


@dataclass
class RetrievedChunk:
    """A policy document chunk returned by the retriever."""
    doc_id: str
    title: str
    content: str
    sensitivity: str
    allowed_roles: list[str]
    score: float  # similarity score [0, 1]
    tags: list[str] = field(default_factory=list)
    
    # Phase 8: Provenance and Segregation
    tenant: str = ""
    source: str = ""
    version_hash: str = ""
    timestamp_indexed: str = ""
    is_untrusted_user_content: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "doc_id": self.doc_id,
            "title": self.title,
            "content": self.content,
            "sensitivity": self.sensitivity,
            "allowed_roles": self.allowed_roles,
            "score": round(self.score, 4),
            "tags": self.tags,
            "tenant": self.tenant,
            "source": self.source,
            "version_hash": self.version_hash,
            "timestamp_indexed": self.timestamp_indexed,
            "is_untrusted_user_content": self.is_untrusted_user_content,
        }


def _tokenize(text: str) -> set[str]:
    """Lowercase word tokens, ignoring punctuation."""
    return set(re.findall(r"\b[a-z]{2,}\b", text.lower()))


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 1.0
    union = a | b
    if not union:
        return 0.0
    return len(a & b) / len(union)


def _similarity(query: str, doc_text: str) -> float:
    """
    Combined similarity score:
      0.5 × Jaccard token overlap  +  0.5 × rapidfuzz partial_ratio
    Returns [0, 1].
    """
    q_tokens = _tokenize(query)
    d_tokens = _tokenize(doc_text)
    jaccard = _jaccard(q_tokens, d_tokens)
    fuzzy = fuzz.partial_ratio(query.lower(), doc_text.lower()) / 100.0
    return 0.5 * jaccard + 0.5 * fuzzy


class EvidenceRetriever:
    """
    Permission-filtered local document retriever.

    Usage:
        retriever = EvidenceRetriever()
        chunks = retriever.retrieve(
            query="archive invoices for vendor",
            actor_role="procurement_manager",
            top_k=3,
        )
    """

    def __init__(self, corpus_path: Path | None = None) -> None:
        self._acl = ACLFilter()
        path = corpus_path or _DEFAULT_CORPUS
        with path.open("r", encoding="utf-8") as fh:
            self._documents: list[dict[str, Any]] = json.load(fh)

    def retrieve(
        self,
        query: str,
        actor_role: str,
        top_k: int = 3,
        tenant: str = "acme",
    ) -> list[RetrievedChunk]:
        """
        Return top-K document chunks relevant to query, filtered by actor_role.
        """

        # 1. Filter out documents missing provenance
        valid_docs = []
        import datetime
        now = datetime.datetime.now(datetime.timezone.utc)
        
        for doc in self._documents:
            # Must have provenance
            if not doc.get("tenant") or not doc.get("source") or not doc.get("version_hash") or not doc.get("timestamp_indexed"):
                continue
                
            # Freshness check: reject if > 30 days old or explicitly revoked
            try:
                indexed_dt = datetime.datetime.fromisoformat(doc["timestamp_indexed"].replace("Z", "+00:00"))
                if (now - indexed_dt).days > 30:
                    continue
            except Exception:
                continue
                
            if doc.get("revoked", False):
                continue
                
            valid_docs.append(doc)

        # 2. ACL filter — remove docs forbidden for actor_role.
        allowed_docs = self._acl.filter(actor_role, valid_docs, tenant=tenant)

        # Score each document
        scored: list[tuple[float, dict[str, Any]]] = []
        for doc in allowed_docs:
            # Build searchable text from title + content + tags
            searchable = f"{doc['title']} {doc['content']} {' '.join(doc.get('tags', []))}"
            score = _similarity(query, searchable)
            scored.append((score, doc))

        # Sort descending
        scored.sort(key=lambda x: x[0], reverse=True)

        chunks: list[RetrievedChunk] = []
        for score, doc in scored[:top_k]:
            chunks.append(
                RetrievedChunk(
                    doc_id=doc["doc_id"],
                    title=doc["title"],
                    content=doc["content"],
                    sensitivity=doc.get("sensitivity", "internal"),
                    allowed_roles=doc.get("allowed_roles", []),
                    score=score,
                    tags=doc.get("tags", []),
                    tenant=doc.get("tenant", ""),
                    source=doc.get("source", ""),
                    version_hash=doc.get("version_hash", ""),
                    timestamp_indexed=doc.get("timestamp_indexed", ""),
                    is_untrusted_user_content=doc.get("is_untrusted_user_content", False),
                )
            )
        return chunks
