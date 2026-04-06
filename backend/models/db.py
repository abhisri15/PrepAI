"""
SQLAlchemy instance shared across all ORM models.

Import `db` from here (not from models/__init__.py) to avoid circular
imports between models and the package __init__.
"""
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
