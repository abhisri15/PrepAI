# PrepAI End-to-End Verification

Backend: **https://prepai-nytf.onrender.com**  
n8n: **https://prepai.app.n8n.cloud**

---

## Before You Start

Render free tier may sleep after ~15 min idle. The **first request** can take 30–60 seconds. Wait and retry if you get a timeout.

---

## Step 1: Test Backend Directly

### 1a. Health check
```
GET https://prepai-nytf.onrender.com/health
```
Expected: `{"status":"ok","provider":"mock","version":"1.0"}`

**PowerShell:**
```powershell
Invoke-RestMethod -Uri "https://prepai-nytf.onrender.com/health" -Method Get
```

**Browser:** Open `https://prepai-nytf.onrender.com/health`

---

### 1b. /api/ask
```
POST https://prepai-nytf.onrender.com/api/ask
Content-Type: application/json
{"question": "What is REST?"}
```
Expected: `{"answer":"...","improvements":[...],"confidence":0.9,"sources":[]}`

**PowerShell:**
```powershell
$body = '{"question":"What is REST?"}'
Invoke-RestMethod -Uri "https://prepai-nytf.onrender.com/api/ask" -Method Post -Body $body -ContentType "application/json"
```

---

### 1c. /api/prepare
```
POST https://prepai-nytf.onrender.com/api/prepare
{"resume_text":"2 years Python","jd_text":"Backend engineer"}
```
Expected: strengths, weaknesses, key_topics, practice_questions, study_plan

---

## Step 2: Test n8n Workflows (Backend Proxy)

### 2a. PrepAI Interview Assistant (ask/evaluate/prepare)
```
POST https://prepai.app.n8n.cloud/webhook/prepai-webhook
Content-Type: application/json
{"action":"ask","question":"What is REST?"}
```
Expected: Same shape as /api/ask response.

**PowerShell:**
```powershell
$body = '{"action":"ask","question":"What is REST?"}'
Invoke-RestMethod -Uri "https://prepai.app.n8n.cloud/webhook/prepai-webhook" -Method Post -Body $body -ContentType "application/json"
```

---

### 2b. PrepAI Candidate Resume to Questions
```
POST https://prepai.app.n8n.cloud/webhook/resume-to-questions
Content-Type: application/json
{"resume":"My resume...","jd":"Job description..."}
```
Expected: PrepAI /api/prepare response (strengths, weaknesses, etc.)

---

## Step 3: Test PrepAI Webhook Entry (Full Guide via Email)

Requires: name, email, role, resume, jd_url OR jd_text

```
POST https://prepai.app.n8n.cloud/webhook/prepai-submit
Content-Type: application/json
{
  "name": "Your Name",
  "email": "your-real-email@gmail.com",
  "role": "Software Engineer",
  "resume": "2 years Python, Flask...",
  "jd_url": "https://example.com/job" 
  OR 
  "jd_text": "Paste JD here..."
}
```
Expected: `{"status":"accepted","message":"Guide will be sent to your email..."}`

**Note:** Check your email for the guide (ensure Gmail credentials are set in Interview Guide Classifier).

---

## Step 4: Test Form (Interview Prep Assistant)

1. Open: https://prepai.app.n8n.cloud/form/b6603404-e2a5-4b50-b5e9-3c88eb753f2f
2. Fill in: Name, Email, Role, Job Description URL, Resume, Additional Notes
3. Submit
4. If qualified: you receive the guide by email
5. If not qualified: rejection email

**Note:** Form uses Relevance AI for JD URL. If Relevance AI fails, use **jd_text** via PrepAI Webhook Entry instead.

---

## Step 5: Test Frontend (Local)

1. Run backend locally (or use deployed):
   ```powershell
   cd backend; .\venv\Scripts\activate; python app.py
   ```
2. Run frontend:
   ```powershell
   cd frontend; npm run dev
   ```
3. Open http://localhost:5173
4. **Prep tab** → Instant roadmap: paste resume + JD
5. **Prep tab** → Full guide via email: requires `N8N_PREPAI_WEBHOOK_URL` in backend `.env`

---

## Troubleshooting

| Symptom | Likely Cause |
|---------|--------------|
| Timeout on first request | Render cold start – wait 30–60 s |
| n8n returns 500 | Check n8n execution log; backend URL may be wrong |
| No email | Gmail credentials in Interview Guide Classifier |
| Form fails | Relevance AI URL or Execute Workflow not linked |
| PrepAI Webhook returns error | Execute Classifier node not linked to Interview Guide Classifier |
