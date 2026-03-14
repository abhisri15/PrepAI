# PrepAI n8n Workflows

PrepAI now uses a minimal n8n setup.

## Required Workflows

1. **Interview Guide Classifier and Notifier**
2. **Interview Prep Assistant (Form Submission)**

## Flow

```text
Frontend -> Flask /api/prep-guide -> n8n webhook /webhook/prepai-form-submit -> Execute Classifier Workflow -> email user
```

The backend already normalizes the input before calling n8n:

- resume is plain text
- JD URL is fetched and converted to JD text if necessary
- webhook payload is JSON

So the n8n workflow only needs to:

1. receive webhook JSON
2. map fields
3. execute `Interview Guide Classifier and Notifier`
4. return a JSON acknowledgement

## Import Order

1. Import **Interview Guide Classifier and Notifier** first.
2. Import **Interview Prep Assistant (Form Submission)** second.
3. Open `Execute Classifier Workflow` in the second workflow and re-link it to `Interview Guide Classifier and Notifier`.

## Webhook Endpoint

`Interview Prep Assistant (Form Submission)` now exposes:

`/webhook/prepai-form-submit`

Expected JSON body:

```json
{
    "name": "Jane Doe",
    "email": "jane@example.com",
    "role": "Software Engineer",
    "resume": "full resume text",
    "jd_text": "full job description text",
    "additional_notes": "optional"
}
```

## Credentials

Set these on n8n after import:

1. OpenAI API credential on the classifier workflow nodes
2. Gmail OAuth2 credential on the email nodes
