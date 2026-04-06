"""
Conversation repository — persists Q&A history per profile.
"""
from models.conversation import Conversation
from models.db import db


class ConversationRepository:

    def add(self, profile_id: str, question: str, answer: str,
            confidence: float = 0.0, improvements: list = None,
            sources: list = None) -> dict:
        """Save one Q&A exchange and return it as a dict."""
        conv = Conversation(
            profile_id=profile_id,
            question=question,
            answer=answer,
            confidence=confidence,
            improvements=improvements or [],
            sources=sources or [],
        )
        db.session.add(conv)
        db.session.commit()
        return conv.to_dict()

    def list_by_profile(self, profile_id: str, limit: int = 50) -> list[dict]:
        """Return recent conversations for a profile, newest first."""
        rows = (
            Conversation.query
            .filter_by(profile_id=profile_id)
            .order_by(Conversation.created_at.desc())
            .limit(limit)
            .all()
        )
        return [r.to_dict() for r in rows]

    def count_by_profile(self, profile_id: str) -> int:
        return Conversation.query.filter_by(profile_id=profile_id).count()


conversation_repo = ConversationRepository()
