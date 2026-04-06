"""
SQLAlchemy ORM model for a TF-IDF retrieval chunk.

Maps to the `profile_chunks` table. Each row represents one word-window
chunk extracted from a source document (resume or job description).

The retriever service writes rows via add_document() and reads them all
at query time to rebuild the TF-IDF matrix. Phase 5 will replace this
table with ChromaDB persistent vector embeddings.
"""
from models.db import db


class Chunk(db.Model):
    __tablename__ = "profile_chunks"

    # Auto-increment integer PK — chunks have no natural stable key.
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # String identifier in the format "{doc_id}_{chunk_index}".
    chunk_id = db.Column(db.String(255), nullable=False, index=True)

    # The source document identifier (e.g. "profile-abc123_resume").
    doc_id = db.Column(db.String(255), nullable=False, index=True)

    # Denormalised profile_id extracted from metadata for easy filtering.
    profile_id = db.Column(
        db.String(64),
        db.ForeignKey("profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # "resume" | "jd" — identifies the source document type.
    source = db.Column(db.String(20), nullable=False, default="")

    # The actual text window sent to TF-IDF.
    text = db.Column(db.Text, nullable=False)

    # Full metadata dict stored as JSON for flexibility.
    metadata_json = db.Column(db.JSON, nullable=False, default=dict)

    def to_dict(self) -> dict:
        """Return the dict shape the retriever service expects."""
        return {
            "id": self.chunk_id,
            "doc_id": self.doc_id,
            "text": self.text,
            "metadata": self.metadata_json or {},
        }

    def __repr__(self) -> str:
        return f"<Chunk id={self.chunk_id!r} profile={self.profile_id!r}>"
