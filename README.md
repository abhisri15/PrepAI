# PrepAI

PrepAI is now intentionally simplified to two product flows:

1. Submit resume + JD + email to get a detailed prep guide by email via n8n.
2. Ask follow-up interview questions using a stored Gemini-generated summary of that resume and JD.

## Architecture

```
User
  |
React Frontend
  |
Flask Backend
  |-- /api/prep-guide -> stores profile context -> forwards normalized payload to n8n webhook
  |-- /api/ask -> uses stored Gemini summary + optional retrieval context
  |
Local Storage (JSON files)
  |
n8n Workflow -> Interview Guide Classifier and Notifier -> Email
```

## Core Behavior

- Prep Guide form accepts name, email, role, resume text or file, JD URL or JD text.
- Backend fetches JD text from the URL if needed.
- Backend generates and stores a Gemini summary in the background.
- Backend forwards the normalized payload to the webhook version of `Interview Prep Assistant (Form Submission)`.
- Ask uses the stored summary to answer questions specifically for that user profile.

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

Recommended `backend/.env` for local use:

```bash
LLM_PROVIDER=gemini
LLM_MODEL=gemini-1.5-flash
GOOGLE_API_KEY=your_gemini_api_key
N8N_PREPAI_WEBHOOK_URL=https://prepai.app.n8n.cloud/webhook/interview-prep
```

Backend runs at `http://localhost:5000`

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at `http://localhost:5173`

Frontend `.env`:

```bash
VITE_API_BASE_URL=http://localhost:5000
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /health | Health check, model info |
| POST | /api/prep-guide | Submit profile, store summary context, trigger email guide workflow |
| POST | /api/ask | Ask profile-aware interview questions |
| GET | /api/profile/:id | Get stored summary state |

## n8n Workflows

Required workflows:

1. `Interview Guide Classifier and Notifier`
2. `Interview Prep Assistant (Form Submission)` — webhook at `/webhook/interview-prep` (production: `https://prepai.app.n8n.cloud/webhook/interview-prep`)

The frontend never posts directly to n8n. The backend handles webhook forwarding after normalizing JD text.

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

## Example Flow

1. **Prep Guide (home):** Enter name, email, role, resume (paste or upload file), JD link (or paste), and optional notes. Submit.
2. Backend sends data to the n8n webhook; n8n processes and emails you a full prep guide if qualified.
3. UI shows: *Full prep guide will be sent via email. You can use Ask to get personalized answers for this role in the meantime.*
4. Backend stores the profile with **company name** (from JD URL/text) and runs a **Gemini summary** of resume + JD in the background (saved locally).
5. **Ask:** Open Ask, select the profile (e.g. "Intuit — ML Engineer") from the dropdown, then ask interview questions. Answers use the stored Gemini summary for that profile.

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
