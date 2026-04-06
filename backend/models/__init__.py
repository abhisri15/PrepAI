"""
ORM models sub-package.

Import order matters: db must be imported before the model modules so
the SQLAlchemy instance exists when Profile and Chunk reference it.
"""
from models.db import db
from models.chunk import Chunk
from models.conversation import Conversation
from models.profile import Profile

__all__ = ["db", "Profile", "Chunk", "Conversation"]
