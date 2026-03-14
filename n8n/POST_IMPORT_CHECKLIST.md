# n8n Post-Import Checklist

You have n8n at **https://prepai.app.n8n.cloud**. Your workflows call `localhost:5000` — n8n cloud **cannot** reach your local machine. Follow this checklist.

---

## ✅ What Works (after the steps below)

| Workflow | URL | Status |
|----------|-----|--------|
| Interview Guide Classifier and Notifier | (child) | ✅ Runs when called by Form or PrepAI Webhook |
| Interview Prep Assistant (Form) | https://prepai.app.n8n.cloud/form/b6603404-e2a5-4b50-b5e9-3c88eb753f2f | ✅ Needs step 1–3 |
| PrepAI Webhook Entry | https://prepai.app.n8n.cloud/webhook/prepai-submit | ✅ Needs step 1, 2, 4 |
| PrepAI Candidate Resume to Questions | https://prepai.app.n8n.cloud/webhook/resume-to-questions | ✅ Needs step 1 |
| PrepAI Interview Assistant | https://prepai.app.n8n.cloud/webhook/prepai-webhook | ✅ Needs step 1 |

---

## 🔧 Modifications Required

### 1. Link Execute Workflow nodes

After import, workflow IDs change. Re-link:

- **Interview Prep Assistant (Form Submission):**  
  Open the **candidate_qualified** tool node → **Execute Workflow** → choose **Interview Guide Classifier and Notifier**.

- **PrepAI Webhook Entry:**  
  Open **Execute Classifier Workflow** node → choose **Interview Guide Classifier and Notifier**.

### 2. Set credentials (Classifier + Form)

- **Interview Guide Classifier and Notifier:** OpenAI API, Gmail OAuth2
- **Interview Prep Assistant:** OpenAI API, Gmail OAuth2 (for rejection email)

### 3. Form workflow (Interview Prep Assistant)

- Uses **Relevance AI** for JD URL fetch.
- If the Relevance AI URL/API key is invalid or expired, the form will fail.
- Keep it as is if you use Relevance AI; otherwise use **PrepAI Webhook Entry** with a public PrepAI backend.

### 4. Replace `localhost:5000` with your public PrepAI backend

Deploy the PrepAI backend to a public URL (e.g. Render, Railway, Fly.io) and update these nodes:

| Workflow | Node | Change |
|----------|------|--------|
| PrepAI Webhook Entry | Fetch JD (PrepAI Backend) | `http://localhost:5000/api/fetch-jd` → `https://YOUR-BACKEND-URL/api/fetch-jd` |
| PrepAI Candidate Resume to Questions | PrepAI Prepare | `http://localhost:5000/api/webhook` → `https://YOUR-BACKEND-URL/api/webhook` |
| PrepAI Interview Assistant | HTTP Request to PrepAI | `http://localhost:5000/api/webhook` → `https://YOUR-BACKEND-URL/api/webhook` |

Example: `https://prepai-backend.onrender.com`

### 5. Backend `.env` (for Prep tab “Full guide via email”)

Add:

```
N8N_PREPAI_WEBHOOK_URL=https://prepai.app.n8n.cloud/webhook/prepai-submit
```

---

## Flow Summary

- **Form:** User submits form → Relevance AI fetches JD → AI qualifies → Classifier → email ✅ (no PrepAI backend)
- **PrepAI Webhook Entry:** User/UI POSTs → PrepAI backend fetches JD (needs public URL) → Classifier → email
- **PrepAI Candidate Resume to Questions / Interview Assistant:** Direct proxy to PrepAI backend (need public URL)
