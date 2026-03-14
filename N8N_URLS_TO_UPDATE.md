# n8n URL Updates Required

Replace any old `http://localhost:5000` values with your **deployed backend URL** in these nodes.

## Your Backend URL

Current deployed backend:
`https://prepai-nytf.onrender.com`

## Workflows to Edit (in n8n UI)

| Workflow | Node Name | Change |
|----------|-----------|--------|
| **PrepAI Webhook Entry** | Fetch JD (PrepAI Backend) | `http://localhost:5000/api/fetch-jd` → `https://prepai-nytf.onrender.com/api/fetch-jd` |
| **PrepAI Candidate Resume to Questions** | Generate Prep Plan | Uses n8n OpenAI directly (no PrepAI backend URL needed) |
| **PrepAI Interview Assistant** | Generate Response | Uses n8n OpenAI directly (no PrepAI backend URL needed) |

## Execute Workflow Links (re-select)

- **PrepAI Webhook Entry** → Execute Classifier Workflow → Select "Interview Guide Classifier and Notifier"
- **Interview Prep Assistant** → candidate_qualified tool → Execute Workflow → Select "Interview Guide Classifier and Notifier"
