# PrepAI n8n Workflows

Workflows used by PrepAI for qualification and email prep guides.

## Workflows

1. **Interview Prep Assistant (Form Submission)** — Webhook at `/webhook/interview-prep`. Receives flat JSON from the backend, runs HTTP request (optional), prepares agent input, and an AI agent qualifies the candidate and either triggers the classifier workflow or sends a rejection email.
2. **Interview Guide Classifier and Notifier** — Invoked by the first workflow when qualified. Classifies seniority and sends a personalized prep guide email via Gmail.

## Webhook Payload (from Backend)

Backend sends **flat JSON** (no `body` wrapper) with these exact keys:

```json
{
  "Your name": "Jane Doe",
  "Email": "jane@example.com",
  "Role you're applying for": "ML Engineer",
  "Resume text": "...",
  "Job description URL": "https://...",
  "Or paste job description text": "",
  "Additional notes": "..."
}
```

## Full Architecture

See **[../ARCHITECTURE.md](../ARCHITECTURE.md)** for complete n8n flow, node roles, and integration with backend and Render.

## Import

1. Import **Interview Guide Classifier and Notifier** first.
2. Import **Interview Prep Assistant (Form Submission)** second.
3. In n8n, set webhook path to `interview-prep` and configure OpenAI + Gmail credentials.
