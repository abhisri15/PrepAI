"""Tests for retriever service."""
import tempfile
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import services.retriever as ret
orig_data = ret.DATA_DIR
ret.DATA_DIR = Path(tempfile.mkdtemp())
ret.CHUNKS_FILE = ret.DATA_DIR / "chunks.json"


def test_add_and_retrieve():
    ret.save_chunks([])
    ret.add_document("doc1", "Python is a programming language. Machine learning uses Python.", {"source": "test"})
    results = ret.retrieve("Python programming", top_k=2)
    assert len(results) >= 1
    assert "Python" in results[0]["text"]
    assert results[0]["score"] > 0


def test_retrieve_empty_returns_empty():
    ret.save_chunks([])
    results = ret.retrieve("xyz query", top_k=3)
    assert results == []
