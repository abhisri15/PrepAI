# InterviewPrepAssistant (PrepAI)

A production-quality, demo-ready AI-powered interview preparation assistant with clean architecture, full-stack development, and workflow orchestration.

## Architecture Overview

```
User
  |
React Frontend (Vite + TailwindCSS)
  |
Flask Backend
  |
+ AI Provider Layer (OpenAI | Anthropic | Gemini | Mock)
+ Vector Retriever (FAISS/TF-IDF)
+ n8n Webhook Integration
```

## Tech Stack

- **Frontend**: React + Vite, TailwindCSS
- **Backend**: Python Flask
- **AI**: OpenAI, Anthropic, Google Gemini, Mock (default, works offline)
- **Vector Retrieval**: FAISS or TF-IDF cosine fallback
- **Storage**: SQLite / JSON files
- **Workflow**: n8n
- **Testing**: pytest

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- (Optional) n8n for workflow automation

### Backend Setup

```bash
cd backend
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python app.py
```

Backend runs at `http://localhost:5000`

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at `http://localhost:5173`

### Default Configuration

- **LLM_PROVIDER=mock** — Works offline, deterministic responses
- Set `LLM_PROVIDER=openai` (or anthropic/gemini) and add API keys for real AI

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /health | Health check, model info |
| POST | /api/ask | AI interview Q&A |
| POST | /api/evaluate | Evaluate candidate answer |
| POST | /api/prepare | Resume + JD → Preparation roadmap |
| POST | /api/upload | Upload documents for RAG |
| POST | /api/feedback | Store feedback |
| POST | /api/webhook | n8n workflow webhook (unchanged) |

## n8n Workflow

Import `n8n/interview_assistant_workflow.json` into n8n. The webhook at `/api/webhook` accepts the existing payload format. Do not modify the workflow logic.

## Run Commands

```bash
# Terminal 1 - Backend
cd backend
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Linux/Mac
pip install -r requirements.txt
python app.py

# Terminal 2 - Frontend
cd frontend
npm install
npm run dev
```

Backend: http://localhost:5000 | Frontend: http://localhost:5173

## n8n Webhook curl Example

```bash
# Ask flow
curl -X POST http://localhost:5000/api/webhook \
  -H "Content-Type: application/json" \
  -d '{"action":"ask","question":"What is REST?"}'

# Evaluate flow
curl -X POST http://localhost:5000/api/webhook \
  -H "Content-Type: application/json" \
  -d '{"action":"evaluate","question":"What is REST?","candidate_answer":"REST is an API style."}'

# Prepare flow
curl -X POST http://localhost:5000/api/webhook \
  -H "Content-Type: application/json" \
  -d '{"action":"prepare","resume_text":"...","jd_text":"..."}'
```

## 3-Minute Demo Script

1. **Open UI** — Navigate to http://localhost:5173
2. **Ask tab** — Ask an interview question; show AI response
3. **Prompt Viewer** — Toggle "Show prompt" to reveal the exact prompt sent to the model
4. **Backend logs** — Show structured logging (requests, prompts, latency) in the backend terminal
5. **Provider abstraction** — Open `backend/services/llm_provider.py` and explain Mock/OpenAI/Anthropic/Gemini design
6. **Architecture** — Walk through: Frontend → Flask API → AI Provider Layer → n8n webhook

## Project Structure

```
PrepAI/
├── frontend/           # React + Vite
├── backend/            # Flask API
├── n8n/                # Workflow exports
├── data/               # Embeddings, storage
└── README.md
```

## License

MIT
