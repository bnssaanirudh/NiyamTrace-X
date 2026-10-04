"""
packages/evidence — NiyamEvidence: permission-filtered RAG + NLI grounding.

Status: IMPLEMENTED (Week 5)

Modules:
  acl.py          — document-level ACL filter (role × sensitivity)
  retriever.py    — local Jaccard + rapidfuzz TF-IDF retriever (ACL-gated)
  nli.py          — deterministic NLI verdict engine (SUPPORT|CONTRADICT|INSUFFICIENT)
"""

from packages.evidence.acl import ACLFilter
from packages.evidence.nli import EvidenceVerdict, NLIEngine
from packages.evidence.retriever import EvidenceRetriever, RetrievedChunk

__all__ = [
    "ACLFilter",
    "EvidenceRetriever",
    "EvidenceVerdict",
    "NLIEngine",
    "RetrievedChunk",
]
