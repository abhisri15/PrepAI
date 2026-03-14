# n8n URL Updates Required

Replace `http://localhost:5000` with your **deployed backend URL** in these nodes.

## Your Backend URL

After deploying to Render, you'll get a URL like:
`https://prepai-backend-xxxx.onrender.com`

## Workflows to Edit (in n8n UI)

| Workflow | Node Name | Change |
|----------|-----------|--------|
| **PrepAI Webhook Entry** | Fetch JD (PrepAI Backend) | `http://localhost:5000/api/fetch-jd` → `https://YOUR-URL/api/fetch-jd` |
| **PrepAI Candidate Resume to Questions** | PrepAI Prepare | `http://localhost:5000/api/webhook` → `https://YOUR-URL/api/webhook` |
| **PrepAI Interview Assistant** | HTTP Request to PrepAI | `http://localhost:5000/api/webhook` → `https://YOUR-URL/api/webhook` |

## Execute Workflow Links (re-select)

- **PrepAI Webhook Entry** → Execute Classifier Workflow → Select "Interview Guide Classifier and Notifier"
- **Interview Prep Assistant** → candidate_qualified tool → Execute Workflow → Select "Interview Guide Classifier and Notifier"
