# PrepAI

Interview preparation app: submit your profile to get a prep guide via email (n8n), then ask personalized interview questions (Groq) using your resume and JD context.

## Flows

1. **Prep Guide** — Submit name, email, role, resume (file or text), JD (URL or text). Backend stores profile, calls n8n webhook, and runs a background Gemini summary. You see a success message; qualified candidates receive a detailed prep guide by email.
2. **Ask** — Select a saved profile (e.g. "Internshala — SDE-1") and ask interview questions. Answers are personalized using full resume + JD context via Groq.

## Quick Start

**Backend**

```bash
cd backend
python -m venv venv
venv\Scripts\activate   # Windows; use source venv/bin/activate on Linux/Mac
pip install -r requirements.txt
cp .env.example .env
# Edit .env: GROQ_API_KEY, N8N_PREPAI_WEBHOOK_URL, optionally GOOGLE_API_KEY
python app.py
```

**Frontend**

```bash
cd frontend
npm install
echo "VITE_API_BASE_URL=http://localhost:5000" > .env
npm run dev
```

- Backend: http://localhost:5000  
- Frontend: http://localhost:5173  

## Docs

- **[ARCHITECTURE.md](./ARCHITECTURE.md)** — Full end-to-end architecture: backend API, frontend, n8n workflows, Render deployment, and system diagrams (Mermaid).

## Project Structure

```
PrepAI/
├── backend/     # Flask API (prep-guide, ask, profile)
├── frontend/    # React + Vite (Prep, Ask pages)
├── n8n/         # Workflow JSON exports
├── data/        # profile_context.json, chunks.json (runtime)
└── ARCHITECTURE.md
```

## License

MIT
