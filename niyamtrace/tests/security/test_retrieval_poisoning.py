import pytest
from packages.evidence.retriever import EvidenceRetriever
import json
import datetime
from pathlib import Path

def test_missing_provenance_rejected(tmp_path):
    docs = [
        # Valid doc
        {
            "doc_id": "1", 
            "tenant": "acme", 
            "source": "hr_policy", 
            "version_hash": "abc", 
            "timestamp_indexed": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "title": "Doc 1",
            "content": "Valid"
        },
        # Missing tenant
        {
            "doc_id": "2", 
            "source": "hr_policy", 
            "version_hash": "abc", 
            "timestamp_indexed": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "title": "Doc 2",
            "content": "Missing tenant"
        }
    ]
    corpus = tmp_path / "corpus.json"
    corpus.write_text(json.dumps(docs))

    retriever = EvidenceRetriever(corpus_path=corpus)
    chunks = retriever.retrieve("Valid Missing", "viewer", tenant="acme")
    
    assert len(chunks) == 1
    assert chunks[0].doc_id == "1"

def test_stale_documents_rejected(tmp_path):
    now = datetime.datetime.now(datetime.timezone.utc)
    stale_date = now - datetime.timedelta(days=35)
    docs = [
        {
            "doc_id": "1", 
            "tenant": "acme", 
            "source": "hr_policy", 
            "version_hash": "abc", 
            "timestamp_indexed": stale_date.isoformat(),
            "title": "Doc 1",
            "content": "Stale"
        }
    ]
    corpus = tmp_path / "corpus.json"
    corpus.write_text(json.dumps(docs))

    retriever = EvidenceRetriever(corpus_path=corpus)
    chunks = retriever.retrieve("Stale", "viewer", tenant="acme")
    
    assert len(chunks) == 0

def test_revoked_documents_rejected(tmp_path):
    now = datetime.datetime.now(datetime.timezone.utc)
    docs = [
        {
            "doc_id": "1", 
            "tenant": "acme", 
            "source": "hr_policy", 
            "version_hash": "abc", 
            "timestamp_indexed": now.isoformat(),
            "revoked": True,
            "title": "Doc 1",
            "content": "Revoked"
        }
    ]
    corpus = tmp_path / "corpus.json"
    corpus.write_text(json.dumps(docs))

    retriever = EvidenceRetriever(corpus_path=corpus)
    chunks = retriever.retrieve("Revoked", "viewer", tenant="acme")
    
    assert len(chunks) == 0
