"""
/api/upload - Upload documents for vector retrieval.
"""
import os
import uuid
from flask import Blueprint, request, jsonify

from services.retriever import add_document

bp = Blueprint("upload", __name__)


@bp.route("/api/upload", methods=["POST"])
def upload():
    """Accept text or file upload, chunk and index for RAG."""
    data = request.get_json()
    text = None
    doc_id = str(uuid.uuid4())[:8]

    if data and data.get("text"):
        text = data.get("text", "").strip()
        doc_id = data.get("doc_id") or doc_id
    elif request.files:
        f = request.files.get("file")
        if f:
            try:
                text = f.read().decode("utf-8", errors="replace")
            except Exception:
                return jsonify({"error": "Could not read file as text"}), 400
            doc_id = data.get("doc_id", doc_id) if data else doc_id

    if not text:
        return jsonify({
            "error": "Provide 'text' in JSON body or upload a text file",
            "example": {"text": "Your document content...", "doc_id": "optional-id"}
        }), 400

    try:
        count = add_document(doc_id, text, metadata={"source": "upload"})
        return jsonify({
            "doc_id": doc_id,
            "chunks_indexed": count,
            "message": f"Document indexed with {count} chunks",
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
