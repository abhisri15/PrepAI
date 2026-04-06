"""
Document retrieval using TF-IDF cosine similarity (RAG layer).

Storage backend swapped from JSON file (Phase 1) to MySQL/SQLite via the
Chunk ORM model (Phase 3). The TF-IDF algorithm is unchanged — all chunks
are loaded from the DB at query time and the matrix is recomputed in-process.

Known limitation: the vectoriser is rebuilt on every retrieve() call, so
cost scales with total chunk count. Acceptable for < ~1 000 chunks; Phase 5
will replace this with ChromaDB persistent vector embeddings.
"""
import logging

from config import Config
from models.chunk import Chunk
from models.db import db

logger = logging.getLogger("prepai")


# ── Chunk I/O (DB-backed) ─────────────────────────────────────────────────────

def load_chunks() -> list[dict]:
    """Return all stored chunks as a list of plain dicts."""
    return [c.to_dict() for c in Chunk.query.order_by(Chunk.id).all()]


def save_chunks(chunks: list[dict]):
    """
    Replace *all* stored chunks with *chunks*.

    Primarily used in tests to reset retriever state to a known baseline.
    Prefer add_document() for normal writes.
    """
    Chunk.query.delete()
    for c in chunks:
        metadata = c.get("metadata") or {}
        db.session.add(Chunk(
            chunk_id=c["id"],
            doc_id=c["doc_id"],
            text=c["text"],
            profile_id=metadata.get("profile_id", ""),
            source=metadata.get("source", ""),
            metadata_json=metadata,
        ))
    db.session.commit()


# ── Chunking ──────────────────────────────────────────────────────────────────

def _chunk_text(text: str) -> list[str]:
    """
    Split *text* into overlapping word-windows.

    Window size and overlap are read from Config so they can be tuned
    without modifying this file.
    """
    words = text.split()
    size = Config.RAG_CHUNK_SIZE
    overlap = Config.RAG_CHUNK_OVERLAP
    chunks = []
    for i in range(0, len(words), size - overlap):
        chunk = " ".join(words[i: i + size])
        if chunk.strip():
            chunks.append(chunk)
    return chunks


# ── Indexing ──────────────────────────────────────────────────────────────────

def add_document(doc_id: str, text: str, metadata: dict = None) -> int:
    """
    Chunk *text* and persist to the profile_chunks table.

    Returns the number of new chunks added.
    """
    metadata = metadata or {}
    profile_id = metadata.get("profile_id", "")
    source = metadata.get("source", "")

    new_chunks = _chunk_text(text)
    for i, chunk_text in enumerate(new_chunks):
        db.session.add(Chunk(
            chunk_id=f"{doc_id}_{i}",
            doc_id=doc_id,
            text=chunk_text,
            profile_id=profile_id,
            source=source,
            metadata_json=metadata,
        ))
    db.session.commit()
    logger.info("Indexed document '%s': %d chunks", doc_id, len(new_chunks))
    return len(new_chunks)


# ── Retrieval ─────────────────────────────────────────────────────────────────

def retrieve(query: str, top_k: int = Config.RAG_TOP_K) -> list[dict]:
    """
    Return the *top_k* most relevant chunks for *query* using TF-IDF cosine similarity.

    Falls back to simple lexical overlap if sklearn is unavailable.
    Each result dict has keys: text, metadata, score.
    """
    chunks = load_chunks()
    if not chunks:
        return []

    try:
        import numpy as np
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity

        texts = [c["text"] for c in chunks]
        vectoriser = TfidfVectorizer(max_features=Config.RAG_MAX_FEATURES, stop_words="english")
        tfidf_matrix = vectoriser.fit_transform(texts)
        query_vec = vectoriser.transform([query])
        scores = cosine_similarity(query_vec, tfidf_matrix).flatten()
        top_indices = np.argsort(scores)[::-1][:top_k]

    except (ImportError, ValueError, TypeError) as exc:
        logger.warning("TF-IDF retrieval unavailable, falling back to lexical search: %s", exc)
        return _lexical_fallback(query, chunks, top_k)

    return [
        {"text": chunks[i]["text"], "metadata": chunks[i].get("metadata", {}), "score": float(scores[i])}
        for i in top_indices
        if scores[i] > Config.RAG_MIN_SIMILARITY
    ]


def _lexical_fallback(query: str, chunks: list[dict], top_k: int) -> list[dict]:
    """Simple term-frequency fallback when sklearn is unavailable."""
    terms = [t for t in query.lower().split() if t]
    if not terms:
        return []

    scored = []
    for chunk in chunks:
        text = (chunk.get("text") or "").lower()
        score = sum(text.count(term) for term in terms)
        if score > 0:
            scored.append({"text": chunk["text"], "metadata": chunk.get("metadata", {}), "score": float(score)})

    scored.sort(key=lambda x: x["score"], reverse=True)
    top = scored[:top_k]

    if top:
        max_score = max(r["score"] for r in top) or 1.0
        for r in top:
            r["score"] = r["score"] / max_score

    return top


def get_context_for_query(query: str, top_k: int = Config.RAG_TOP_K) -> str:
    """Return a concatenated context string suitable for injecting into a prompt."""
    results = retrieve(query, top_k=top_k)
    return "\n\n---\n\n".join(r["text"] for r in results)
