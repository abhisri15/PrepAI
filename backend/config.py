"""
Central configuration for PrepAI.
All constants and environment variables live here — never scattered in service files.
"""
import os
from pathlib import Path


class Config:
    # ── LLM ──────────────────────────────────────────────────────────────────
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "auto")
    LLM_MODEL = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")
    LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.7"))
    LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "1024"))

    # Groq is the preferred provider for /api/ask (fast inference)
    GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

    # ── Context window limits (chars sent to LLM) ────────────────────────────
    RESUME_MAX_CHARS = 6000
    JD_MAX_CHARS = 4000
    SUMMARY_RESUME_MAX_CHARS = 3000
    SUMMARY_JD_MAX_CHARS = 3000

    # ── RAG / TF-IDF Retriever ───────────────────────────────────────────────
    RAG_CHUNK_SIZE = 500          # words per chunk
    RAG_CHUNK_OVERLAP = 50        # word overlap between consecutive chunks
    RAG_TOP_K = 3                 # number of chunks returned per query
    RAG_MIN_SIMILARITY = 0.01     # cosine similarity threshold; below this is noise
    RAG_MAX_FEATURES = 5000       # TF-IDF vocabulary size cap

    # ── File uploads ─────────────────────────────────────────────────────────
    MAX_UPLOAD_BYTES = 5 * 1024 * 1024   # 5 MB
    ALLOWED_EXTENSIONS = {"pdf", "docx", "txt"}

    # ── CORS ─────────────────────────────────────────────────────────────────
    # Comma-separated list in env: "http://localhost:5173,https://prepai.netlify.app"
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")

    # ── Database (Phase 3) ────────────────────────────────────────────────────
    # SQLite for local dev; set DATABASE_URL in production to MySQL:
    #   mysql+pymysql://user:pass@host:3306/prepai
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///prepai_dev.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ── n8n integration ───────────────────────────────────────────────────────
    N8N_WEBHOOK_URL = os.getenv("N8N_PREPAI_WEBHOOK_URL", "").strip()
    N8N_TIMEOUT_SECS = int(os.getenv("N8N_TIMEOUT_SECS", "10"))

    # ── App ───────────────────────────────────────────────────────────────────
    DEBUG = os.getenv("DEBUG", "false").lower() == "true"   # safe default: off
    SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-production")
    TESTING = False
