# n8n URL Updates Required

Replace any old `http://localhost:5000` values with your **deployed backend URL** in these nodes.

## Your Backend URL

Current deployed backend:
`https://prepai-nytf.onrender.com`

## Workflows to Edit (in n8n UI)

| Workflow | Node Name | Change |
|----------|-----------|--------|
| **PrepAI Webhook Entry** | Fetch JD (PrepAI Backend) | `http://localhost:5000/api/fetch-jd` → `https://prepai-nytf.onrender.com/api/fetch-jd` |
| **PrepAI Candidate Resume to Questions** | PrepAI Prepare | `http://localhost:5000/api/webhook` → `https://prepai-nytf.onrender.com/api/webhook` |
| **PrepAI Interview Assistant** | HTTP Request to PrepAI | `http://localhost:5000/api/webhook` → `https://prepai-nytf.onrender.com/api/webhook` |

## Execute Workflow Links (re-select)

- **PrepAI Webhook Entry** → Execute Classifier Workflow → Select "Interview Guide Classifier and Notifier"
- **Interview Prep Assistant** → candidate_qualified tool → Execute Workflow → Select "Interview Guide Classifier and Notifier"
