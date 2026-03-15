# How to Run PrepAI

## 1. Backend (local)

```bash
cd backend
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/Mac:
# source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `backend/.env` and set:

- `GOOGLE_API_KEY` — your Gemini API key (for resume+JD summary and Ask answers)
- `N8N_PREPAI_WEBHOOK_URL=https://prepai.app.n8n.cloud/webhook/interview-prep`

Then:

```bash
python app.py
```

Backend: **http://localhost:5000**  
Check: `curl http://localhost:5000/health`

---

## 2. Frontend (local)

```bash
cd frontend
npm install
```

Create `frontend/.env` (or `.env.local`) with:

```
VITE_API_BASE_URL=http://localhost:5000
```

Then:

```bash
npm run dev
```

Frontend: **http://localhost:5173**

---

## 3. n8n (production)

1. In **n8n** (e.g. https://prepai.app.n8n.cloud), import the two workflows from the `n8n/` folder (Classifier first, then Form Submission).
2. Set the **Interview Prep Assistant** webhook path to **interview-prep** so the URL is `https://prepai.app.n8n.cloud/webhook/interview-prep`.
3. Configure **OpenAI** and **Gmail** credentials in the Classifier workflow.

---

## 4. Deploy on Render

1. Push code to GitHub.
2. In Render: connect repo, use existing `render.yaml` or create a Web Service with root directory `backend`, build `pip install -r requirements.txt`, start `gunicorn app:app --bind 0.0.0.0:$PORT`.
3. In Render **Environment**, set:
   - `GOOGLE_API_KEY`
   - `N8N_PREPAI_WEBHOOK_URL=https://prepai.app.n8n.cloud/webhook/interview-prep`
   - `LLM_PROVIDER=gemini`
4. Frontend: set `VITE_API_BASE_URL` to your Render backend URL (e.g. `https://prepai-backend-xxxx.onrender.com`), then build and deploy the frontend (e.g. static site or same Render service).

After deploy, new pushes to GitHub will auto-deploy on Render if auto-deploy is enabled.

---

## 5. Quick test

1. Open the app → **Prep Guide**.
2. Fill name, email, role. For **Resume**: either upload a file (txt/pdf/docx) or paste text. For **JD**: either paste a URL or paste JD text. Submit.
3. You should see: *Full prep guide will be sent via email…* and the profile is saved with a company name.
4. Go to **Ask** → select the profile (e.g. "Intuit — ML Engineer") → ask an interview question. The answer uses the stored Gemini summary for that profile.

---

## 6. End-to-end verification (after deploy on Render)

1. **Backend health**: `curl https://YOUR-RENDER-URL/health` → should return `{"status":"ok", ...}`.
2. **Prep Guide**: Open frontend → Prep Guide → submit with resume (file or text) and JD (URL or text). Expect success message; check email if n8n is configured.
3. **Ask**: Open Ask → select the saved profile from dropdown → ask a question → expect an answer using your resume/JD context.
4. **Gemini**: Ensure `GOOGLE_API_KEY` is set on Render so profile summary and Ask use Gemini.
