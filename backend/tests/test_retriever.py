"""Tests for the TF-IDF retriever service (DB-backed, Phase 3)."""
import services.retriever as ret


def test_add_and_retrieve(app_ctx):
    """Adding a document and retrieving against a matching query returns results."""
    ret.save_chunks([])  # clear state
    ret.add_document("doc1", "Python is a programming language. Machine learning uses Python.", {"source": "test", "profile_id": "test-profile"})
    results = ret.retrieve("Python programming", top_k=2)
    assert len(results) >= 1
    assert "Python" in results[0]["text"]
    assert results[0]["score"] > 0


def test_retrieve_empty_returns_empty(app_ctx):
    """Retrieving against an empty index returns an empty list."""
    ret.save_chunks([])
    results = ret.retrieve("xyz query", top_k=3)
    assert results == []
