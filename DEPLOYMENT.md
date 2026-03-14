# PrepAI End-to-End Setup

## Step 1: Run Backend Locally (verify)

```bash
cd backend
python -m venv venv
venv\Scripts\activate   # Windows
pip install -r requirements.txt
python app.py
```

Backend: http://localhost:5000 — test: `curl http://localhost:5000/health`

---

## Step 2: Run Frontend Locally

```bash
cd frontend
npm install
npm run dev
```

Frontend: http://localhost:5173

---

## Step 3: Deploy Backend (required for n8n cloud)

n8n at prepai.app.n8n.cloud cannot reach localhost. Deploy backend to **Render** (free):

**Option A – Blueprint (if render.yaml is in repo):**  
1. Push latest code to GitHub  
2. Go to https://dashboard.render.com/select-repo  
3. Select your PrepAI repo → Render will detect `render.yaml`  
4. Create services → Copy your backend URL

**Option B – Manual:**  
1. Push latest code to GitHub  
2. Go to https://render.com → **New** → **Web Service**  
3. Connect your GitHub repo  
4. Settings:
   - **Root Directory:** `backend`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app --bind 0.0.0.0:$PORT`
5. Add environment variable:
   - **PYTHON_VERSION=3.11.0**
   - **LLM_PROVIDER=auto**
   - **OPENAI_API_KEY=<your key>** or **GOOGLE_API_KEY=<your key>** or **ANTHROPIC_API_KEY=<your key>**
   - **N8N_PREPAI_WEBHOOK_URL=<your real n8n webhook URL for prepai-submit>**
6. **Create Web Service**  
7. Copy your service URL (e.g. `https://prepai-backend-xxxx.onrender.com`)

With `LLM_PROVIDER=auto`, the backend will automatically use OpenAI, Anthropic, or Gemini when the corresponding API key is present. If no provider key is set, it falls back to `mock`.

---

## Step 4: Update n8n Workflows

In n8n (https://prepai.app.n8n.cloud), edit these 3 workflows and replace `http://localhost:5000` with your backend URL (e.g. `https://prepai-backend-xxxx.onrender.com`):

| Workflow | Node | Field |
|----------|------|-------|
| PrepAI Webhook Entry | Fetch JD (PrepAI Backend) | URL |
| PrepAI Candidate Resume to Questions | PrepAI Prepare | URL |
| PrepAI Interview Assistant | HTTP Request to PrepAI | URL |

Also re-link **Execute Workflow** in PrepAI Webhook Entry and Interview Prep Assistant → **Interview Guide Classifier and Notifier**.

---

## Step 5: Backend .env (optional)

For Prep tab "Full guide via email":

```
N8N_PREPAI_WEBHOOK_URL=https://prepai.app.n8n.cloud/webhook/prepai-submit
```

---

## Step 6: Test

- **Form:** https://prepai.app.n8n.cloud/form/b6603404-e2a5-4b50-b5e9-3c88eb753f2f
- **PrepAI Webhook Entry:** `POST https://prepai.app.n8n.cloud/webhook/prepai-submit` with JSON body (name, email, role, jd_url, resume)
