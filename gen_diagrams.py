"""Generate updated architecture diagrams for PrepAI."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch

BG = "#0f172a"


def box(ax, x, y, w, h, color, label, sublabel=None, fontsize=9):
    rect = FancyBboxPatch(
        (x, y), w, h,
        boxstyle="round,pad=0.05,rounding_size=0.25",
        linewidth=1.5, edgecolor=color, facecolor=color + "28", zorder=3,
    )
    ax.add_patch(rect)
    cy = y + h / 2 + (0.15 if sublabel else 0)
    ax.text(x + w / 2, cy, label, ha="center", va="center",
            color="#f1f5f9", fontsize=fontsize, fontweight="bold", zorder=4)
    if sublabel:
        ax.text(x + w / 2, y + h / 2 - 0.22, sublabel, ha="center", va="center",
                color="#94a3b8", fontsize=7, zorder=4)


def grp(ax, x, y, w, h, color, title):
    rect = FancyBboxPatch(
        (x, y), w, h,
        boxstyle="round,pad=0.05,rounding_size=0.35",
        linewidth=1.2, edgecolor=color, facecolor=color + "0a",
        linestyle="--", zorder=1,
    )
    ax.add_patch(rect)
    ax.text(x + 0.18, y + h - 0.22, title, ha="left", va="top",
            color=color, fontsize=8.5, fontweight="bold", zorder=2)


def arr(ax, x1, y1, x2, y2, color="#475569", label=None):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="->", color=color, lw=1.5), zorder=2)
    if label:
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        ax.text(mx, my + 0.15, label, ha="center", va="bottom",
                color="#64748b", fontsize=7.5, zorder=5,
                bbox=dict(boxstyle="round,pad=0.1", facecolor=BG, edgecolor="none", alpha=0.8))


# ─────────────────────────────────────────────
# HLD
# ─────────────────────────────────────────────
fig, ax = plt.subplots(1, 1, figsize=(20, 13))
fig.patch.set_facecolor(BG)
ax.set_facecolor(BG)
ax.set_xlim(0, 20)
ax.set_ylim(0, 13)
ax.axis("off")

ax.text(10, 12.55, "PrepAI — High-Level Architecture", ha="center", va="center",
        color="#f8fafc", fontsize=17, fontweight="bold")
ax.text(10, 12.15, "AI-powered interview prep · ATS scoring · Gap analysis · Personalized email guides",
        ha="center", va="center", color="#64748b", fontsize=9.5)

# User
grp(ax, 0.2, 10.6, 2.6, 1.7, "#94a3b8", "User")
box(ax, 0.5, 10.9, 2.0, 1.1, "#94a3b8", "Browser", fontsize=10)

# Frontend
grp(ax, 3.2, 9.1, 6.5, 3.2, "#38bdf8", "Frontend  (React + Vite · Tailwind)")
box(ax, 3.45, 11.15, 1.35, 0.85, "#38bdf8", "Prep Guide", None, 8)
box(ax, 5.0, 11.15, 1.1, 0.85, "#38bdf8", "Ask", None, 8)
box(ax, 6.3, 11.15, 1.25, 0.85, "#f59e0b", "ATS Score", None, 8)
box(ax, 7.75, 11.15, 1.65, 0.85, "#a78bfa", "Gap Analysis", None, 8)
box(ax, 4.1, 9.4, 4.5, 0.85, "#60a5fa", "api.js", "fetch() REST client", 9)

# Backend
grp(ax, 10.0, 5.9, 9.6, 6.5, "#34d399", "Backend  (Flask · Gunicorn · Render)")
ax.text(14.8, 11.95, "API Blueprints", ha="center", color="#6ee7b7", fontsize=8, style="italic")
box(ax, 10.3, 11.1, 2.0, 0.85, "#34d399", "/api/profile", "prep-guide & init", 8)
box(ax, 12.5, 11.1, 1.6, 0.85, "#34d399", "/api/ask", None, 8)
box(ax, 14.3, 11.1, 2.1, 0.85, "#f59e0b", "/api/ats-score", "NEW", 8)
box(ax, 16.6, 11.1, 2.7, 0.85, "#a78bfa", "/api/profile/:id", "gap / summary data", 8)

ax.text(14.8, 10.65, "Services", ha="center", color="#6ee7b7", fontsize=8, style="italic")
box(ax, 10.3, 9.75, 1.8, 0.85, "#6ee7b7", "llm", "Groq / Gemini", 8)
box(ax, 12.3, 9.75, 1.8, 0.85, "#f59e0b", "ats_scorer", "LLM-based", 8)
box(ax, 14.3, 9.75, 1.8, 0.85, "#34d399", "guide_gen", "instant guide", 8)
box(ax, 16.3, 9.75, 1.5, 0.85, "#34d399", "n8n_client", None, 8)
box(ax, 18.0, 9.75, 1.3, 0.85, "#34d399", "pii_guard", None, 7.5)

box(ax, 10.3, 8.65, 1.8, 0.85, "#6ee7b7", "doc_parser", "PDF/DOCX/TXT", 8)
box(ax, 12.3, 8.65, 1.8, 0.85, "#6ee7b7", "jd_fetcher", "URL → text", 8)
box(ax, 14.3, 8.65, 1.8, 0.85, "#6ee7b7", "profile_sum", "async Gemini", 8)
box(ax, 16.3, 8.65, 1.8, 0.85, "#6ee7b7", "prompt_bld", "templates", 8)
box(ax, 18.3, 8.65, 1.0, 0.85, "#6ee7b7", "retriever", None, 7.5)

box(ax, 10.3, 7.55, 9.0, 0.85, "#34d399", "SQLAlchemy ORM  ·  Flask-Migrate",
    "SQLite (dev)  /  PostgreSQL (prod)", 9)

ax.text(14.8, 7.15, "Models", ha="center", color="#f472b6", fontsize=8, style="italic")
box(ax, 10.3, 6.2, 2.2, 0.75, "#f472b6", "Profile", "resume, JD, summary", 8)
box(ax, 12.7, 6.2, 2.2, 0.75, "#f472b6", "Conversation", "Q&A history", 8)
box(ax, 15.1, 6.2, 2.2, 0.75, "#f472b6", "Chunk", "RAG (TF-IDF)", 8)
box(ax, 17.5, 6.2, 1.8, 0.75, "#f472b6", "Feedback", None, 8)

# External
grp(ax, 0.2, 1.5, 8.8, 7.7, "#fb923c", "External Services")
box(ax, 0.5, 7.3, 2.5, 1.1, "#fb923c", "Groq API", "llama-3.3-70b", 9)
box(ax, 3.2, 7.3, 2.5, 1.1, "#fb923c", "Google Gemini", "async summary", 9)
box(ax, 6.0, 7.3, 2.7, 1.1, "#fb923c", "n8n Cloud", "prep guide email", 9)
box(ax, 0.5, 5.8, 2.5, 1.1, "#fb923c", "Gmail", "OAuth2 via n8n", 9)
box(ax, 3.2, 5.8, 2.5, 1.1, "#fb923c", "OpenAI", "n8n AI agent", 9)
box(ax, 6.0, 5.8, 2.7, 1.1, "#fb923c", "Render Cloud", "backend host", 9)
box(ax, 0.5, 3.1, 8.2, 2.2, "#e2e8f0",
    "n8n Workflows",
    "WF1: Qualify candidate → email prep guide  |  WF2: Classify seniority → personalized guide", 8.5)
box(ax, 0.5, 1.8, 8.2, 1.0, "#94a3b8",
    "prepai_dev.db  (SQLite)  ·  data/chunks.json  (RAG index)", None, 8.5)

# Arrows
arr(ax, 2.5, 11.1, 3.2, 11.3, "#94a3b8")
arr(ax, 8.6, 9.8, 10.0, 9.5, "#38bdf8", "HTTP REST")
arr(ax, 10.3, 8.15, 8.7, 7.85, "#34d399", "LLM / n8n calls")
arr(ax, 14.8, 7.55, 14.8, 6.97, "#f472b6", "ORM")

legend_items = [
    mpatches.Patch(color="#38bdf8", label="Frontend (React)"),
    mpatches.Patch(color="#34d399", label="Backend (Flask)"),
    mpatches.Patch(color="#fb923c", label="External Services"),
    mpatches.Patch(color="#f472b6", label="Data Models"),
    mpatches.Patch(color="#f59e0b", label="ATS Score (new)"),
    mpatches.Patch(color="#a78bfa", label="Gap Analysis (new)"),
]
leg = ax.legend(handles=legend_items, loc="lower right", framealpha=0.3,
                facecolor="#1e293b", edgecolor="#334155", labelcolor="#cbd5e1",
                fontsize=8.5, bbox_to_anchor=(0.99, 0.01),
                title="Components", title_fontsize=8.5)
leg.get_title().set_color("#94a3b8")

plt.tight_layout(pad=0.2)
plt.savefig("F:/IIIT Bhubaneswar/ML/PrepAI/HLD.png", dpi=150,
            bbox_inches="tight", facecolor=BG)
plt.close()
print("HLD.png done")


# ─────────────────────────────────────────────
# Sequence Diagram
# ─────────────────────────────────────────────
fig2, ax2 = plt.subplots(1, 1, figsize=(22, 16))
fig2.patch.set_facecolor(BG)
ax2.set_facecolor(BG)
ax2.set_xlim(0, 22)
ax2.set_ylim(0, 16)
ax2.axis("off")

ax2.text(11, 15.55, "PrepAI — Sequence Diagram", ha="center",
         color="#f8fafc", fontsize=17, fontweight="bold")
ax2.text(11, 15.15, "Four flows: Prep Guide · Ask · ATS Score · Gap Analysis",
         ha="center", color="#64748b", fontsize=9.5)

# Participants
parts = [
    ("User", 1.0, "#94a3b8"),
    ("Frontend", 3.5, "#38bdf8"),
    ("Flask API", 6.0, "#34d399"),
    ("LLM Service", 8.5, "#6ee7b7"),
    ("n8n / Email", 11.0, "#fb923c"),
    ("Gemini (async)", 13.5, "#e879f9"),
    ("ATS Scorer", 16.0, "#f59e0b"),
    ("Profile DB", 18.5, "#f472b6"),
    ("Gap Extractor", 21.0, "#a78bfa"),
]

LCOLOR = "#1e3a5f"

for name, x, color in parts:
    box(ax2, x - 0.85, 14.0, 1.7, 0.75, color, name, fontsize=8.5)
    ax2.plot([x, x], [0.3, 14.0], color=LCOLOR, lw=1.2, zorder=1, linestyle="--")


def seq_arr(x1, x2, y, label, color="#38bdf8", dashed=False):
    ls = "--" if dashed else "-"
    ax2.annotate("", xy=(x2, y), xytext=(x1, y),
                 arrowprops=dict(arrowstyle="->", color=color, lw=1.4,
                                 linestyle=ls), zorder=3)
    mx = (x1 + x2) / 2
    off = 0.12 if x2 > x1 else -0.12
    ax2.text(mx, y + 0.14, label, ha="center", va="bottom",
             color=color, fontsize=7.2, zorder=4,
             bbox=dict(boxstyle="round,pad=0.08", facecolor=BG, edgecolor="none", alpha=0.85))


def section(y, title, color):
    ax2.text(0.1, y + 0.05, title, ha="left", va="bottom",
             color=color, fontsize=8.5, fontweight="bold",
             bbox=dict(boxstyle="round,pad=0.2", facecolor=color + "22",
                       edgecolor=color + "55", alpha=0.9))
    ax2.plot([0.0, 22.0], [y, y], color=color + "44", lw=0.8, zorder=0)


# ── Flow 1: Prep Guide ──
section(13.55, "1  Prep Guide Flow", "#38bdf8")
seq_arr(1.0, 3.5, 13.2, "submit form (name, email, role, resume, JD)", "#94a3b8")
seq_arr(3.5, 6.0, 12.85, "POST /api/profile/init (FormData)", "#38bdf8")
seq_arr(6.0, 8.5, 12.5, "parse doc + fetch JD text", "#34d399")
seq_arr(6.0, 18.5, 12.15, "store_profile() → Profile DB", "#f472b6")
seq_arr(6.0, 13.5, 11.8, "summarize_profile_async() [background]", "#e879f9")
seq_arr(6.0, 11.0, 11.45, "POST webhook (flat JSON)", "#fb923c")
seq_arr(11.0, 6.0, 11.1, "200 OK (qualified/rejected email sent)", "#fb923c", dashed=True)
seq_arr(6.0, 3.5, 10.75, "{ profile_id, company_name, message }", "#34d399", dashed=True)
seq_arr(3.5, 1.0, 10.4, "show success + save to localStorage", "#38bdf8", dashed=True)
seq_arr(13.5, 18.5, 10.1, "update profile with summary/gaps [async]", "#e879f9", dashed=True)

# ── Flow 2: Ask ──
section(9.8, "2  Ask Flow", "#34d399")
seq_arr(1.0, 3.5, 9.5, "select profile + type question", "#94a3b8")
seq_arr(3.5, 6.0, 9.15, "POST /api/ask { question, user_id }", "#38bdf8")
seq_arr(6.0, 18.5, 8.8, "get_profile_context(user_id)", "#f472b6")
seq_arr(18.5, 6.0, 8.45, "profile (resume + JD + summary)", "#f472b6", dashed=True)
seq_arr(6.0, 8.5, 8.1, "build_ask_prompt() → Groq chat", "#34d399")
seq_arr(8.5, 6.0, 7.75, "{ answer, improvements, confidence }", "#6ee7b7", dashed=True)
seq_arr(6.0, 3.5, 7.4, "200 { answer, improvements, confidence, sources }", "#34d399", dashed=True)
seq_arr(3.5, 1.0, 7.05, "display answer panel", "#38bdf8", dashed=True)

# ── Flow 3: ATS Score ──
section(6.75, "3  ATS Score Flow  (new)", "#f59e0b")
seq_arr(1.0, 3.5, 6.45, "select profile + click Analyse", "#94a3b8")
seq_arr(3.5, 6.0, 6.1, "POST /api/ats-score { profile_id }", "#f59e0b")
seq_arr(6.0, 18.5, 5.75, "fetch resume_text + jd_text", "#f472b6")
seq_arr(6.0, 16.0, 5.4, "compute_ats_score(resume, jd)", "#f59e0b")
seq_arr(16.0, 8.5, 5.05, "LLM structured call (Groq)", "#f59e0b")
seq_arr(8.5, 16.0, 4.7, "{ score, keywords, categories, suggestions }", "#6ee7b7", dashed=True)
seq_arr(16.0, 6.0, 4.35, "parsed + validated ATS result", "#f59e0b", dashed=True)
seq_arr(6.0, 3.5, 4.0, "200 { score, matched_keywords, missing_keywords, ... }", "#f59e0b", dashed=True)
seq_arr(3.5, 1.0, 3.65, "render score ring + category bars + suggestions", "#38bdf8", dashed=True)

# ── Flow 4: Gap Analysis ──
section(3.35, "4  Gap Analysis Flow  (new)", "#a78bfa")
seq_arr(1.0, 3.5, 3.05, "select profile → view gaps", "#94a3b8")
seq_arr(3.5, 6.0, 2.7, "GET /api/profile/:id", "#a78bfa")
seq_arr(6.0, 18.5, 2.35, "get_profile(profile_id)", "#f472b6")
seq_arr(18.5, 21.0, 2.0, "fit_highlights, likely_gaps, focus_areas", "#a78bfa")
seq_arr(21.0, 6.0, 1.65, "gap fields (from Gemini summary)", "#a78bfa", dashed=True)
seq_arr(6.0, 3.5, 1.3, "200 profile with gap analysis data", "#34d399", dashed=True)
seq_arr(3.5, 1.0, 0.95, "render strengths + gaps + focus areas", "#38bdf8", dashed=True)

plt.tight_layout(pad=0.2)
plt.savefig("F:/IIIT Bhubaneswar/ML/PrepAI/Sequence Diagram.png", dpi=150,
            bbox_inches="tight", facecolor=BG)
plt.close()
print("Sequence Diagram.png done")
