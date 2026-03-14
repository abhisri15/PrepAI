"""
Vector retrieval for RAG.
Uses TF-IDF cosine similarity fallback (no external deps).
FAISS optional if faiss-cpu installed.
"""
import json
from pathlib import Path

import logging
logger = logging.getLogger("prepai")

DATA_DIR = Path(__file__).parent.parent.parent / "data"
CHUNKS_FILE = DATA_DIR / "chunks.json"
EMBEDDINGS_DIR = DATA_DIR / "embeddings"


def _ensure_data_dir():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    EMBEDDINGS_DIR.mkdir(parents=True, exist_ok=True)


def _chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """Split text into overlapping chunks."""
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size - overlap):
        chunk = " ".join(words[i : i + chunk_size])
        if chunk.strip():
            chunks.append(chunk)
    return chunks


def load_chunks() -> list[dict]:
    """Load stored chunks from disk."""
    _ensure_data_dir()
    if not CHUNKS_FILE.exists():
        return []
    with open(CHUNKS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_chunks(chunks: list[dict]):
    """Persist chunks to disk."""
    _ensure_data_dir()
    with open(CHUNKS_FILE, "w", encoding="utf-8") as f:
        json.dump(chunks, f, indent=2)


def add_document(doc_id: str, text: str, metadata: dict = None):
    """
    Add document to retrieval index.
    Chunks text, stores with metadata.
    """
    chunks = load_chunks()
    new_chunks = _chunk_text(text)
    for i, c in enumerate(new_chunks):
        chunks.append({
            "id": f"{doc_id}_{i}",
            "doc_id": doc_id,
            "text": c,
            "metadata": metadata or {},
        })
    save_chunks(chunks)
    logger.info("Added document %s: %d chunks", doc_id, len(new_chunks))
    return len(new_chunks)


def retrieve(query: str, top_k: int = 3) -> list[dict]:
    """
    Retrieve top_k most relevant chunks using TF-IDF cosine similarity.
    Returns list of {text, metadata, score}.
    """
    chunks = load_chunks()
    if not chunks:
        return []

    # Import heavy ML deps lazily so app startup stays fast and robust in cloud runtimes.
    try:
        import numpy as np
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity

        texts = [c["text"] for c in chunks]
        vectorizer = TfidfVectorizer(max_features=5000, stop_words="english")
        tfidf = vectorizer.fit_transform(texts)
        q_vec = vectorizer.transform([query])
        sims = cosine_similarity(q_vec, tfidf).flatten()
        indices = np.argsort(sims)[::-1][:top_k]
    except (ImportError, ValueError, TypeError) as e:
        logger.warning("TF-IDF retrieval unavailable, using lexical fallback: %s", e)
        return _fallback_retrieve(query, chunks, top_k=top_k)

    results = []
    for i in indices:
        if sims[i] > 0.01:
            results.append({
                "text": chunks[i]["text"],
                "metadata": chunks[i].get("metadata", {}),
                "score": float(sims[i]),
            })
    return results


def _fallback_retrieve(query: str, chunks: list[dict], top_k: int = 3) -> list[dict]:
    """Simple lexical fallback when sklearn/scipy is unavailable."""
    terms = [t for t in query.lower().split() if t]
    if not terms:
        return []

    results = []
    for c in chunks:
        text = (c.get("text") or "").lower()
        score = sum(text.count(term) for term in terms)
        if score > 0:
            results.append({
                "text": c.get("text", ""),
                "metadata": c.get("metadata", {}),
                "score": float(score),
            })

    results.sort(key=lambda x: x["score"], reverse=True)
    results = results[:top_k]

    if not results:
        return []

    max_score = max(r["score"] for r in results) or 1.0
    for r in results:
        r["score"] = float(r["score"] / max_score)

    return results


def get_context_for_query(query: str, top_k: int = 3) -> str:
    """Return concatenated context string for RAG prompts."""
    results = retrieve(query, top_k=top_k)
    if not results:
        return ""
    return "\n\n---\n\n".join(r["text"] for r in results)
