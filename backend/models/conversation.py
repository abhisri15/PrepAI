"""
SQLAlchemy ORM model for conversation history.

Each row is one Q&A exchange tied to a profile.  The Ask endpoint writes
a row after every successful LLM call so users can review past practice.
"""
from datetime import datetime

from models.db import db


class Conversation(db.Model):
    __tablename__ = "conversations"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    profile_id = db.Column(
        db.String(64),
        db.ForeignKey("profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    question = db.Column(db.Text, nullable=False)
    answer = db.Column(db.Text, nullable=False, default="")
    confidence = db.Column(db.Float, nullable=False, default=0.0)
    improvements = db.Column(db.JSON, nullable=False, default=list)
    sources = db.Column(db.JSON, nullable=False, default=list)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    profile = db.relationship("Profile", backref=db.backref("conversations", lazy="dynamic"))

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "profile_id": self.profile_id,
            "question": self.question or "",
            "answer": self.answer or "",
            "confidence": self.confidence or 0.0,
            "improvements": self.improvements or [],
            "sources": self.sources or [],
            "created_at": self.created_at.isoformat() if self.created_at else "",
        }

    def __repr__(self) -> str:
        return f"<Conversation id={self.id} profile={self.profile_id!r}>"
