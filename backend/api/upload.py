"""
/api/upload - Upload documents for vector retrieval.
"""
import uuid
from flask import Blueprint, request, jsonify

from models import store_profile_context
from services.document_parser import extract_text_from_upload
from services.retriever import add_document

bp = Blueprint("upload", __name__)


@bp.route("/api/upload", methods=["POST"])
def upload():
    """Accept text or file upload, chunk and index for RAG."""
    data = request.get_json()
    text = None
    doc_id = str(uuid.uuid4())[:8]
    profile_id = None
    source = "upload"

    if data and data.get("text"):
        text = data.get("text", "").strip()
        doc_id = data.get("doc_id") or doc_id
        profile_id = data.get("profile_id")
        source = data.get("source") or source
    elif request.files:
        f = request.files.get("file")
        profile_id = request.form.get("profile_id")
        source = request.form.get("source") or source
        if f:
            try:
                text = extract_text_from_upload(f)
            except Exception:
                return jsonify({"error": "Could not read file as text"}), 400
            doc_id = request.form.get("doc_id", doc_id)

    if not text:
        return jsonify({
            "error": "Provide 'text' in JSON body or upload a text file",
            "example": {"text": "Your document content...", "doc_id": "optional-id"}
        }), 400

    try:
        count = add_document(doc_id, text, metadata={"source": source, "profile_id": profile_id or ""})
        if profile_id and source == "resume":
            store_profile_context(profile_id, {"resume_text": text})
        return jsonify({
            "doc_id": doc_id,
            "chunks_indexed": count,
            "message": f"Document indexed with {count} chunks",
            "text_preview": text[:300],
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
