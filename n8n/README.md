# PrepAI n8n Workflows

## Overview

PrepAI uses n8n for the full interview prep flow: resume + JD → seniority classification → tailored guide → email delivery.

## Workflow Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  Entry Points                                                    │
│  • Form (Interview Prep Assistant)                               │
│  • Webhook (PrepAI Webhook Entry)                                │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  Interview Guide Classifier and Notifier                         │
│  • Classify: fresher | mid_level | senior                        │
│  • Generate guide (Fresher / Mid-Level / Senior prompts)         │
│  • Send email via Gmail                                          │
└─────────────────────────────────────────────────────────────────┘
```

## Import Order

1. **Interview Guide Classifier and Notifier** (child) – import first  
2. **Interview Prep Assistant (Form Submission)** – form + AI qualification  
3. **PrepAI Webhook Entry** – webhook + PrepAI backend integration  

After importing PrepAI Webhook Entry, open the **Execute Classifier Workflow** node and select the **Interview Guide Classifier and Notifier** workflow.

## PrepAI Webhook Entry

- **Path:** `/webhook/prepai-submit`
- **Method:** POST
- **Body:** `{ name, email, role, jd_url?, jd_text?, resume, additional_notes? }`

If `jd_url` is provided, the workflow calls PrepAI backend `/api/fetch-jd` to fetch JD text. Otherwise it uses `jd_text` directly.

### Backend Configuration

Add to `backend/.env`:

```
N8N_PREPAI_WEBHOOK_URL=http://localhost:5678/webhook/prepai-submit
```

Use your n8n base URL. For n8n cloud or remote: `https://your-n8n.example.com/webhook/prepai-submit`

### Fetch JD Backend URL

In PrepAI Webhook Entry, the **Fetch JD** node calls `http://localhost:5000/api/fetch-jd`. If your Flask backend runs elsewhere, edit that node’s URL (e.g. `http://host.docker.internal:5000` when n8n runs in Docker).

## Form Workflow (Interview Prep Assistant)

Uses **Relevance AI** to fetch job description from a URL. You must configure the Relevance AI API URL in the HTTP Request node.  
Alternatively, use **PrepAI Webhook Entry**, which uses the PrepAI backend for JD fetching.

## Credentials

On import, n8n will prompt for:

- **OpenAI API** – for classification and guide generation  
- **Gmail OAuth2** – for sending the prep guide  

Re-select your credentials in each node after import.
