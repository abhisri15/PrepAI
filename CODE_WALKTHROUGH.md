# PrepAI — Line-by-Line Code Walkthrough (Local Code Only)

This document explains the entire PrepAI codebase in depth: every relevant file and what each section does. It covers backend, frontend, config, and data files (no n8n workflow internals).

---

## Table of Contents

1. [Project root & config](#1-project-root--config)
2. [Backend: app.py](#2-backend-apppy)
3. [Backend: models.py](#3-backend-modelspy)
4. [Backend: api/profile.py](#4-backend-apiprofilepy)
5. [Backend: api/ask.py](#5-backend-apiaskpy)
6. [Backend: services/llm_provider.py](#6-backend-servicesllm_providerpy)
7. [Backend: services/n8n_client.py](#7-backend-servicesn8n_clientpy)
8. [Backend: services/jd_fetcher.py](#8-backend-servicesjd_fetcherpy)
9. [Backend: services/document_parser.py](#9-backend-servicesdocument_parserpy)
10. [Backend: services/profile_summary.py](#10-backend-servicesprofile_summarypy)
11. [Backend: services/prompt_templates.py](#11-backend-servicesprompt_templatespy)
12. [Backend: services/security.py & utils/logging.py](#12-backend-servicessecuritypy--utilsloggingpy)
13. [Backend: services/retriever.py (summary)](#13-backend-servicesretrieverpy-summary)
14. [Backend: requirements.txt, Procfile, .env.example](#14-backend-requirementstxt-procfile-envexample)
15. [Frontend: App.jsx](#15-frontend-appjsx)
16. [Frontend: api.js](#16-frontend-apijs)
17. [Frontend: pages/Prep.jsx](#17-frontend-pagesprepjsx)
18. [Frontend: pages/Ask.jsx](#18-frontend-pagesaskjsx)
19. [Frontend: package.json](#19-frontend-packagejson)
20. [Data files: profile_context.json & chunks.json](#20-data-files-profile_contextjson--chunksjson)

---

## 1. Project root & config

### render.yaml

```yaml
# Render one-click deploy for PrepAI Backend
services:
  - type: web
    name: prepai-backend
    runtime: python
    rootDir: backend
    buildCommand: pip install -r requirements.txt
    startCommand: gunicorn app:app --bind 0.0.0.0:$PORT
    envVars:
      - key: LLM_PROVIDER
        value: auto
      - key: PYTHON_VERSION
        value: 3.11.0
```

- **type: web** — Render runs this as a web service (HTTP).
- **rootDir: backend** — All commands run from the `backend/` directory.
- **buildCommand** — Installs Python dependencies before deploy.
- **startCommand** — Runs the Flask app with Gunicorn; `$PORT` is set by Render.
- **envVars** — Default env: `LLM_PROVIDER=auto`, `PYTHON_VERSION=3.11.0`. You add `GROQ_API_KEY`, `N8N_PREPAI_WEBHOOK_URL`, etc. in the Render dashboard.

---

## 2. Backend: app.py

**Role:** Flask application entry point: load env, create app, register blueprints, expose root and health.

```python
# Lines 1–5: Docstring and imports
```
- Imports: `os`, `Path`, `load_dotenv`, `Flask`, `CORS`, the **ask** and **profile** blueprints only, and `get_provider` from the LLM service.

```python
# Lines 24–29: Load .env
root = Path(__file__).parent.parent   # Project root (parent of backend/)
for p in (root / ".env", Path(__file__).parent / ".env"):
    if p.exists():
        load_dotenv(p)
        break
```
- Loads the first existing `.env` (project root or `backend/`). Env vars (e.g. `GROQ_API_KEY`, `N8N_PREPAI_WEBHOOK_URL`) come from here.

```python
# Lines 31–32
app = Flask(__name__)
CORS(app, origins=["*"])
```
- Creates the Flask app and enables CORS for all origins so the frontend (different port or domain) can call the API.

```python
# Register blueprints
app.register_blueprint(ask_bp)
app.register_blueprint(profile_bp)
```
- Only two blueprints: **ask_bp** (`/api/ask`) and **profile_bp** (`/api/prep-guide`, `/api/profile/init`, `/api/profile/<id>`). Other APIs (evaluate, prepare, upload, feedback, webhook, fetch_jd, n8n_submit) were removed as unused.

```python
# Lines 44–47: GET /
def index():
    return {"service": "PrepAI", "status": "ok"}
```
- Root route for liveness/HTTP probes; returns a simple JSON payload.

```python
# Lines 50–59: GET /health
def health():
    provider = get_provider()
    return {"status": "ok", "model": ..., "provider": provider.name, "version": "1.0"}
```
- Health check: reports status, configured model name, and which LLM provider is active (mock, groq, gemini, etc.).

```python
# Lines 62–64: Run development server
if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=...)
```
- When you run `python app.py`, the app listens on `0.0.0.0:5000` (or `$PORT`). Production uses Gunicorn (Procfile/render.yaml).

---

## 3. Backend: models.py

**Role:** File-based persistence for **profile context** only. All paths are under project root `data/`.

```python
# Paths
DATA_DIR = Path(__file__).parent.parent / "data"
PROFILE_CONTEXT_FILE = DATA_DIR / "profile_context.json"
```
- `__file__` is `backend/models.py`, so `parent.parent` is the repo root. `DATA_DIR` = `PrepAI/data/`; profile data lives in `PrepAI/data/profile_context.json`.

```python
# ensure_data_dir()
```
- Creates `data/` if missing. Called before reading/writing profile context. (Feedback and uploads were removed; only profile storage remains.)

```python
# _load_profile_context_map()
```
- Reads `profile_context.json` and returns the whole dict (key = profile_id, value = profile object). Returns `{}` if the file is missing.

```python
# _save_profile_context_map(data)
```
- Writes the full profile map to `profile_context.json` (indented JSON).

```python
# store_profile_context(user_id, payload)
```
- Loads the map, gets the existing profile for `user_id`, merges `payload` and `updated_at` into it, writes back. Used by Prep Guide (initial save) and by profile_summary (Gemini summary merge).

```python
# get_profile_context(user_id)
```
- Loads the map and returns the profile for `user_id`, or `{}` if not found. Used by Ask and by GET `/api/profile/<id>`.

---

## 4. Backend: api/profile.py

**Role:** Prep Guide flow: parse input (form or JSON), validate, fetch JD if URL, derive company name, store profile, index for RAG, start async summary, call n8n webhook, return profile_id and company_name. Also GET profile by id.

```python
# Lines 1–18: Imports and blueprint
bp = Blueprint("profile", __name__)
```
- Imports: Flask (Blueprint, jsonify, request), models (get/store profile), document_parser (file → text), jd_fetcher (fetch JD, company name), n8n_client, profile_summary, retriever.

```python
# Lines 21–27: _pick_profile_id(payload)
```
- Returns `profile_id` from payload if provided, else `user_id`, else a new UUID string `profile-{12 hex chars}`. So each submission can get a unique id (no email fallback).

```python
# Lines 30–38: _parse_request_payload()
```
- If the request is `multipart/form-data`, builds a dict from the form; if a file is in `resume_file`, extracts text via `extract_text_from_upload()` and sets `resume_text` and `resume_filename`. Otherwise returns `request.get_json() or {}`.

```python
# Lines 41–54: _profile_context_text(profile)
```
- Used by GET profile: returns a string for “context”. Prefers `summary_context` or `summary`; if missing, concatenates truncated `resume_text` and `jd_text`.

```python
# Lines 57–66: Route and validation
@bp.route("/api/profile/init", methods=["POST"])
@bp.route("/api/prep-guide", methods=["POST"])
def init_profile_flow():
    payload = _parse_request_payload()
    resume_text = (payload.get("resume_text") or "").strip()
    jd_text = (payload.get("jd_text") or "").strip()
    jd_url = (payload.get("jd_url") or "").strip()
    # 400 if no resume or no JD (text or URL)
```
- Both routes use the same handler. After parsing, requires `resume_text` (from form or file) and either `jd_text` or `jd_url`.

```python
# Lines 68–72: Fetch JD from URL
if jd_url and not jd_text:
    jd_text = fetch_job_description(jd_url)
```
- If the user sent only a JD URL, fetches the page and extracts text (up to 15k chars). On failure returns 400.

```python
# Lines 74–78: Company name
company_name = "Company"
if jd_url:
    company_name = extract_company_name_from_url(jd_url)
if company_name == "Company" and jd_text:
    company_name = extract_company_name_from_jd_text(jd_text)
```
- Derives a display name from the JD URL (e.g. intuit.com → “Intuit”) or from JD text patterns (“At X we…”, “Company: X”).

```python
# Lines 80–92: Store profile
profile_id = _pick_profile_id(payload)
store_profile_context(profile_id, { ... })
```
- Builds the profile dict (profile_id, name, email, role, company_name, resume_text, jd_text, jd_url, additional_notes, summary_status="pending", resume_filename) and saves it to `profile_context.json`.

```python
# Lines 94–95: RAG index
add_document(f"{profile_id}_resume", resume_text, ...)
add_document(f"{profile_id}_jd", jd_text, ...)
```
- Appends chunked resume and JD to `chunks.json` with metadata (profile_id, source). Ask does not use RAG today; this keeps the index available for future use.

```python
# Lines 97–104: Async Gemini summary
summarize_profile_async(profile_id, name=..., role=..., resume_text=..., jd_text=..., additional_notes=...)
```
- Starts a background thread that calls the default LLM (e.g. Gemini) to produce a structured summary, then merges it into the same profile via `store_profile_context(profile_id, summary_data)`.

```python
# Lines 106–113: n8n webhook
webhook_url = os.getenv("N8N_PREPAI_WEBHOOK_URL") or os.getenv("N8N_FORM_WEBHOOK_URL")
# ...
n8n_payload = { "Your name": ..., "Email": ..., "Role you're applying for": ..., "Resume text": ..., "Job description URL": ..., "Or paste job description text": ..., "Additional notes": ... }
result = post_webhook(webhook_url, n8n_payload)  # or {} on exception
```
- Sends a flat JSON body to the n8n webhook. If the request fails, logs and continues; response still returns success so the user can use Ask.

```python
# Lines 129–134: Response
return jsonify({ "profile_id", "company_name", "summary_status": "pending", "message": ... })
```
- Frontend uses `profile_id` and `company_name` to append an entry to the Ask dropdown list in localStorage.

```python
# Lines 137–154: GET /api/profile/<profile_id>
def get_profile(profile_id):
    profile = get_profile_context(profile_id)
    # 404 if missing
    return jsonify({ profile_id, company_name, summary_status, summary, context, role, email })
```
- Returns the stored profile for the Ask page (summary status, summary text, and context string).

---

## 5. Backend: api/ask.py

**Role:** Interview Q&A: load profile by id, build full context (summary or resume+JD), call Groq (or default LLM), return answer + improvements + confidence.

```python
# Lines 1–12: Imports and blueprint
from services.llm_provider import get_ask_provider, generate_json
from services.prompt_templates import build_ask_prompt
from models import get_profile_context
# ...
bp = Blueprint("ask", __name__)
```

```python
# Lines 15–29: _full_profile_context(profile)
```
- If the profile has `summary_context` or `summary`, returns that as the context string. Otherwise concatenates resume (first 6000 chars) and JD (first 4000 chars). Used to send “full context” to the LLM on every request.

```python
# Lines 32–39: Parse request
data = request.get_json() or {}
question = (data.get("question") or "").strip()
context_override = (data.get("context") or "").strip()
user_id = data.get("user_id") or "anonymous"
# 400 if question empty
question = redact_pii(question)
provider = get_ask_provider()
```
- `user_id` is the selected profile id from the frontend. PII in the question is redacted before logging/sending to the LLM.

```python
# Lines 46–54: Build context
profile = get_profile_context(user_id)
full_context = context_override or _full_profile_context(profile)
if not full_context:
    full_context = "(No profile selected. Submit Prep Guide first and select a profile in Ask.)"
system, user_prompt = build_ask_prompt(question, full_context)
```
- Loads profile from `profile_context.json` and builds the prompt with the full context string.

```python
# Lines 59–78: Call LLM and return
result = generate_json(user_prompt, system=system, provider=provider, temperature=0.7, max_tokens=1024)
# Normalize answer, improvements (list), confidence (float), sources (list)
return jsonify({ "answer", "improvements", "confidence", "sources" })
```
- Uses the Ask provider (Groq if `GROQ_API_KEY` set). Parses JSON from the model output and returns a consistent shape. On exception returns 500 with a safe message.

---

## 6. Backend: services/llm_provider.py

**Role:** Single interface to multiple LLMs: mock, OpenAI, Anthropic, Gemini, Groq. Resolves provider from env; Ask can force Groq.

```python
# Lines 13–17: Lazy client singletons
_openai_client = None
_anthropic_client = None
_gemini_model = None
_groq_client = None
```
- Clients are created on first use to avoid loading heavy libs at import time.

```python
# Lines 19–25: _get_openai()
```
- Builds `OpenAI(api_key=OPENAI_API_KEY)` once and reuses it.

```python
# Lines 27–36: _get_groq()
```
- Builds `OpenAI(api_key=GROQ_API_KEY, base_url="https://api.groq.com/openai/v1")` so the same `chat.completions` API is used for Groq.

```python
# Lines 38–52: _get_anthropic(), _get_gemini()
```
- Lazy init for Anthropic and Google Gemini using their SDKs and env keys.

```python
# Lines 55–71: _parse_json_from_text(text)
```
- Tries to find JSON inside markdown code fences, then the first `{ ... }` in the string. Parses and returns a dict; on failure returns a default dict with `answer`, `improvements`, `confidence`, `sources` so the API always has a valid shape.

```python
# Lines 74–85: BaseLLMProvider (ABC)
```
- Abstract base: `generate(prompt, system, temperature, max_tokens)` returns a string; `name` property returns provider name.

```python
# Lines 88–130: MockProvider
```
- No network: returns fixed JSON so the UI always gets a valid shape (e.g. answer, improvements, confidence). Used when no API keys are set. (Evaluate/prep templates were removed.)

```python
# Lines 133–206: OpenAIProvider, AnthropicProvider, GeminiProvider, GroqProvider
```
- Each implements `generate()`: builds messages (system + user), calls the provider’s API, returns the content string. Groq uses `GROQ_MODEL` (default `llama-3.3-70b-versatile`).

```python
# Lines 209–231: _resolve_provider_name(), get_provider(), get_ask_provider()
```
- `_resolve_provider_name()`: if `LLM_PROVIDER` is `auto`, picks the first available key (OpenAI, Anthropic, Google, Groq); else uses the configured name.
- `get_provider()`: returns the default provider instance.
- `get_ask_provider()`: if `GROQ_API_KEY` is set, returns Groq; otherwise returns the default provider. Ask uses this so it can prefer Groq without changing the global default.

```python
# Lines 254–259: generate_json(prompt, system, provider=None, **kwargs)
```
- Calls `provider.generate(...)`, then `_parse_json_from_text(raw)` and returns the resulting dict. If `provider` is None, uses `get_provider()`.

---

## 7. Backend: services/n8n_client.py

**Role:** POST JSON to an n8n webhook and unwrap common response wrappers.

```python
# Lines 9–25: _extract_json_from_text(text)
```
- Looks for JSON in markdown fences or first `{ ... }`; returns parsed dict or None.

```python
# Lines 28–47: unwrap_n8n_response(data)
```
- Recursively unwraps n8n-style envelopes: list → first element; dict with `json`/`body`/`data` → recurse; `message.content` or `output` string → try parse as JSON. Returns the innermost useful object.

```python
# Lines 50–62: post_webhook(url, payload, timeout=45)
```
- `requests.post(url, json=payload)`. Raises on HTTP error or empty/invalid response. Parses response and passes it through `unwrap_n8n_response` so the caller gets a simple dict when possible.

```python
# Lines 65–73: trigger_webhook_async(url, payload, timeout=20)
```
- Starts a daemon thread that POSTs to the webhook; ignores errors. Used when the caller does not need to wait for the webhook response.

---

## 8. Backend: services/jd_fetcher.py

**Role:** Fetch JD HTML from a URL and extract text; derive company name from URL or JD text.

```python
# Lines 7–22: DOMAIN_TO_COMPANY
```
- Map of known hostnames to display names (e.g. intuit.com → "Intuit"). Used when the JD URL host matches.

```python
# Lines 25–55: extract_company_name_from_url(jd_url)
```
- Parses the URL, normalizes the host (strip www, strip jobs./careers./etc.). If the host (or parent domain) is in `DOMAIN_TO_COMPANY`, returns that name. For linkedin.com, tries `/company/(slug)` and title-cases it. Otherwise takes the first host label (e.g. “internshala” from internshala.com) and title-cases it. Returns "Company" on error or empty.

```python
# Lines 58–75: extract_company_name_from_jd_text(jd_text, max_chars=1500)
```
- Scans the first part of the JD for patterns like “At X we”, “Company: X”, “X is hiring” and returns the captured name, or "Company".

```python
# Lines 78–84: extract_text_from_html(html)
```
- Strips script/style tags, replaces tags with space, collapses whitespace. Simple HTML-to-text without BeautifulSoup.

```python
# Lines 87–98: validate_url(url), fetch_job_description(url, max_chars=15000)
```
- `validate_url`: checks scheme and netloc. `fetch_job_description`: GETs the URL, runs `extract_text_from_html`, returns the first `max_chars` characters. Raises on invalid URL or HTTP error.

---

## 9. Backend: services/document_parser.py

**Role:** Extract plain text from uploaded resume files (TXT, PDF, DOCX).

```python
# Lines 9–27: extract_text_from_upload(file_storage)
```
- `file_storage`: Flask `FileStorage` (e.g. `request.files["resume_file"]`). Reads the file once; uses the suffix to decide:
  - `.txt` / `.md` / `.rtf`: decode as UTF-8 and strip.
  - `.pdf`: `pypdf.PdfReader`, concatenate each page’s `extract_text()`.
  - `.docx`: `python-docx` Document, concatenate paragraph texts.
- Returns the extracted string; stream is reset so the file can be read again if needed.

---

## 10. Backend: services/profile_summary.py

**Role:** In a background thread, call the default LLM (e.g. Gemini) to summarize resume + JD, then merge the result into the profile in `profile_context.json`.

```python
# Lines 8–11: SUMMARY_SYSTEM
```
- System prompt: role is “interview preparation analyst”, output must be valid JSON.

```python
# Lines 14–34: _summary_prompt(...)
```
- Builds a user prompt with name, role, resume, JD, additional_notes and instructs the model to return JSON with keys: summary, resume_summary, jd_summary, fit_highlights, likely_gaps, focus_areas.

```python
# Lines 37–47: format_summary_context(summary_data)
```
- Turns the summary dict into a single string (summary + fit_highlights + likely_gaps + focus_areas) for storage and for use as “context” in Ask.

```python
# Lines 50–65: generate_profile_summary(...)
```
- Calls `generate_json(...)` with the summary prompt and system; normalizes the result into a dict with the expected keys and list types. Uses the default provider (typically Gemini when `GOOGLE_API_KEY` is set).

```python
# Lines 68–81: summarize_profile_async(profile_id, ...)
```
- Defines `_runner()`: calls `generate_profile_summary`, sets `summary_status="complete"` and `summary_context=format_summary_context(...)`, then `store_profile_context(profile_id, summary_data)`. On exception stores `summary_status="failed"` and `summary_error`. Starts `threading.Thread(target=_runner, daemon=True)` and returns. The profile in `profile_context.json` is updated when the thread finishes.

---

## 11. Backend: services/prompt_templates.py

**Role:** Prompt strings and builder for **Ask** only (interview Q&A with profile context). Evaluate and Prep templates were removed as unused.

```python
# ASK_SYSTEM, ASK_USER
```
- System = expert interview prep assistant; user template has `{retrieved_context}` and `{question}`, and asks for JSON with answer, improvements, confidence, sources.

```python
# build_ask_prompt(question, retrieved_context)
```
- Returns (system_string, user_string) with placeholders filled. Used by `/api/ask`.

---

## 12. Backend: services/security.py & utils/logging.py

### security.py

- **redact_pii(text):** Applies regex for email, phone, credit-card and replaces with `[EMAIL_REDACTED]` etc. Used in ask.py on the user’s question before sending to the LLM and logs.

### utils/logging.py

- Configures a logger named `"prepai"` to stdout with a simple format.
- **log_request(endpoint, model, latency_ms, **kwargs):** Logs one line per API request.
- **log_prompt(prompt_preview, max_len=200):** Logs a truncated prompt for debugging.
- **log_error(message, exc):** Logs errors with optional exception.
- **with_timing(f):** Decorator that logs execution time of a function.

---

## 13. Backend: services/retriever.py (summary)

- **DATA_DIR / CHUNKS_FILE:** Same idea as models: `Path(__file__).parent.parent.parent / "data"` → repo root `data/`; `chunks.json` lives there.
- **add_document(doc_id, text, metadata):** Chunks text (word-based, configurable size/overlap), appends each chunk to `chunks.json` with id, doc_id, text, metadata. Used by profile.py for resume and JD.
- **retrieve(query, top_k):** Loads chunks, uses TF-IDF (sklearn) to score chunks by similarity to the query, returns top_k. Ask does not use this; it uses full profile context from models instead.
- **get_context_for_query(query, top_k):** Wraps retrieve and formats the result as a string for prompts. Not used by the current Ask flow.

---

## 14. Backend: requirements.txt, Procfile, .env.example

### requirements.txt

- **flask, flask-cors:** Web app and CORS.
- **python-dotenv:** Load `.env`.
- **openai:** Used for OpenAI and for Groq (OpenAI-compatible client).
- **anthropic, google-generativeai:** Claude and Gemini.
- **numpy, scikit-learn:** Retriever TF-IDF.
- **requests:** n8n webhook and JD fetch.
- **pypdf, python-docx:** Resume file parsing.
- **gunicorn:** Production WSGI server.
- **pytest:** Tests.

### Procfile

```
web: gunicorn app:app --bind 0.0.0.0:$PORT
```

- Tells the platform (e.g. Render) to run the app with Gunicorn and bind to `$PORT`.

### .env.example

- Template for `.env`. Lists: `LLM_PROVIDER`, `LLM_MODEL`, `DEBUG`, `SECRET_KEY`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GOOGLE_API_KEY`, `GROQ_API_KEY` / `GROQ_MODEL`, `N8N_PREPAI_WEBHOOK_URL`, `N8N_FORM_WEBHOOK_URL`. Copy to `.env` and fill in real values (do not commit keys).

---

## 15. Frontend: App.jsx

**Role:** Root component: router, nav links, and the two main pages (Prep, Ask).

```javascript
// Lines 1–5: Imports
import { useState } from 'react'
import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom'
import Header from './components/Header'
import Ask from './pages/Ask'
import Prep from './pages/Prep'
```

```javascript
// Lines 7–8: App component state
const [health, setHealth] = useState({ status: 'unknown' })
```
- Header can show backend health; it receives `health` and `setHealth` so it can fetch `/health` and update this state.

```javascript
// Lines 10–13: navClass
const navClass = ({ isActive }) => `...`
```
- Function for `NavLink`: active link gets amber styling, inactive gets slate and hover.

```javascript
// Lines 15–30: JSX
<BrowserRouter>
  <Header health={health} setHealth={setHealth} />
  <nav>
    <NavLink to="/" className={navClass} end>Prep Guide</NavLink>
    <NavLink to="/ask" className={navClass}>Ask</NavLink>
  </nav>
  <main>
    <Routes>
      <Route path="/" element={<Prep />} />
      <Route path="/ask" element={<Ask />} />
    </Routes>
  </main>
</BrowserRouter>
```
- `/` renders Prep, `/ask` renders Ask. Nav and main content are in one column layout.

---

## 16. Frontend: api.js

**Role:** Base URL, fetch helpers, and exported functions for **health**, **ask**, **initProfileFlow**, **getProfile**. (Upload was removed as unused.)

```javascript
// Lines 1–6: API_BASE and apiUrl(path)
const API_BASE = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '')
function apiUrl(path) {
  if (!API_BASE) return path
  return `${API_BASE}${path}`
}
```
- `VITE_API_BASE_URL` is set at build time (e.g. `http://localhost:5000`). `apiUrl('/api/ask')` becomes `http://localhost:5000/api/ask`.

```javascript
// Lines 8–18: parseError(r)
```
- Reads response as text; if it’s JSON, returns `data.error` or `data.message`; otherwise returns status or raw text. Used to throw a single string for the UI.

```javascript
// Lines 21–36: extractJsonFromText(text)
```
- Tries to parse JSON from markdown fences or first `{ ... }`. Used when the backend might return wrapped or raw JSON.

```javascript
// Lines 39–55: unwrapN8nResponse(data)
```
- Recursively unwraps `json`/`body`/`data`/`message.content`/`output` so the caller gets the inner payload. Keeps compatibility with n8n-style responses.

```javascript
// Lines 57–75: postJson(url, body)
```
- `fetch` POST with `Content-Type: application/json`. On non-OK, throws with `parseError`. On OK, parses body and runs `unwrapN8nResponse` before returning.

```javascript
// Lines 78–95: postForm(url, formData)
```
- `fetch` POST with FormData (no Content-Type so browser sets multipart). Same error handling and unwrap as postJson.

```javascript
// health(), ask(...), initProfileFlow(payload), getProfile(profileId)
```
- **health():** GET `/health`, returns JSON.
- **ask({ question, context, user_id }):** POST `/api/ask` with JSON body.
- **initProfileFlow(payload):** If `payload` is FormData, POST to `/api/profile/init`; else POST JSON to `/api/prep-guide`. Prep page uses FormData.
- **getProfile(profileId):** GET `/api/profile/:id`, returns profile JSON.

---

## 17. Frontend: pages/Prep.jsx

**Role:** Prep Guide form: collect name, email, role, resume (file or text), JD (URL or text), notes; submit to backend; update localStorage for the Ask dropdown.

```javascript
// Lines 1–16: Imports and state
const [resumeFile, setResumeFile] = useState(null)
const [resume, setResume] = useState('')
const [jd, setJd] = useState('')
const [jdUrl, setJdUrl] = useState('')
const [name, setName] = useState('')
const [email, setEmail] = useState('')
const [role, setRole] = useState('')
const [notes, setNotes] = useState('')
const [statusMessage, setStatusMessage] = useState('')
const [profileId, setProfileId] = useState('')
const [loading, setLoading] = useState(false)
const [error, setError] = useState('')
```
- One state per form field plus status/loading/error.

```javascript
// Lines 18–56: handleSubmit
e.preventDefault()
// Clear error/status, set loading
// Validate: at least one of resume text or file; at least one of jd text or jdUrl
// Build FormData: name, email, role, additional_notes, jd_url if set, jd_text if set, resume_text if set, resume_file if set
const data = await initProfileFlow(formData)
setProfileId(data.profile_id)
if (data.profile_id) {
  localStorage.setItem('prepaiProfileId', data.profile_id)
  const companyName = data.company_name || 'Company'
  const roleLabel = data.role || role || 'Software Engineer'
  const list = JSON.parse(localStorage.getItem('prepaiProfiles') || '[]')
  list.push({ id: data.profile_id, companyName, role: roleLabel })
  localStorage.setItem('prepaiProfiles', JSON.stringify(list))
}
setStatusMessage(data.message)
// catch: setError(err.message)
// finally: setLoading(false)
```
- On success, saves the latest profile id to `prepaiProfileId` and appends `{ id, companyName, role }` to the `prepaiProfiles` array. The Ask page reads `prepaiProfiles` to build the dropdown.

```javascript
// Lines 59–151: JSX
```
- Form: inputs for name, email, role; file input + textarea for resume; URL input + textarea for JD; textarea for notes; submit button.
- Below: error div (red), success div with message and “Open Ask and select this role” when `profileId` is set.

---

## 18. Frontend: pages/Ask.jsx

**Role:** Load profile list from localStorage, show dropdown (newest first), on change load that profile from the API; submit question with selected profile id and show answer + improvements + confidence.

```javascript
// Lines 4–5: localStorage keys
const PREPAI_PROFILES_KEY = 'prepaiProfiles'
const PREPAI_PROFILE_ID_KEY = 'prepaiProfileId'
```

```javascript
// Lines 7–21: loadProfileList()
```
- Reads `prepaiProfiles` from localStorage; if non-empty array, normalizes each item to `{ id, companyName, role }` and returns the list **reversed** (newest first). If empty, tries `prepaiProfileId` and returns a single-item list so one “Saved profile” appears. This is the **only** source of the dropdown options (not profile_context.json or chunks.json).

```javascript
// Lines 23–32: State
const [profileList, setProfileList] = useState([])
const [selectedIndex, setSelectedIndex] = useState(0)
const [profile, setProfile] = useState(null)
const profileId = profileList[selectedIndex]?.id ?? ''
```
- Dropdown value is the **index** (0, 1, 2, …) so every option has a unique value and selection works even when multiple entries share the same backend profile id. The actual id sent to the API is `profileId`.

```javascript
// Lines 34–42: refreshProfile(id)
```
- Calls `getProfile(id)` and sets `profile` with the result (or null on error). Used when the list loads (first profile) and when the user changes the dropdown.

```javascript
// Lines 44–49: useEffect
const list = loadProfileList()
setProfileList(list)
setSelectedIndex(0)
if (list.length > 0) refreshProfile(list[0].id)
```
- On mount, loads the list, shows newest first, selects index 0, and fetches that profile’s details from the backend.

```javascript
// Lines 51–56: handleProfileChange(e)
const index = Number(e.target.value)
setSelectedIndex(index)
refreshProfile(profileList[index].id)
```
- When the user picks another option, updates selected index and fetches the corresponding profile.

```javascript
// Lines 58–70: handleSubmit
// POST /api/ask with { question, user_id: profileId }
// setResult(data) or setError(err.message)
```

```javascript
// Lines 72–155: JSX
```
- If `profileList.length > 0`: label, `<select value={selectedIndex} onChange={handleProfileChange}>` with `option value={index}` and label `companyName — role`; then a box showing summary status and summary text for the selected profile.
- If no profiles: message to submit Prep Guide first.
- Form: textarea for question, Ask button (disabled when no profile or no profileId).
- Error and result sections: answer, improvements list, confidence.

---

## 19. Frontend: package.json

- **name:** prepai-frontend.
- **scripts:** `dev` (Vite dev server), `build` (Vite build), `preview` (preview production build).
- **dependencies:** react, react-dom, react-router-dom.
- **devDependencies:** Vite, React plugin, Tailwind, PostCSS, Autoprefixer, type defs. Build and dev are done via these.

---

## 20. Data files: profile_context.json & chunks.json

### profile_context.json

- **Location:** `PrepAI/data/profile_context.json` (created by the backend when you run it from the repo).
- **Shape:** A single JSON object. Keys are **profile IDs** (e.g. `profile-abc123def456` or legacy email). Each value is a profile object with at least:
  - `profile_id`, `name`, `email`, `role`, `company_name`
  - `resume_text`, `jd_text`, `jd_url`, `additional_notes`
  - `summary_status` ("pending" | "complete" | "failed")
  - `summary`, `summary_context` (when Gemini summary has run)
  - `resume_filename`, `updated_at`
- **Written by:** `models.store_profile_context` (from profile.py on submit, and from profile_summary.py when the summary job finishes).
- **Read by:** GET `/api/profile/<id>` and by `/api/ask` (to load the selected profile and build full context). The **Ask dropdown does not read this file**; it reads only localStorage.

### chunks.json

- **Location:** `PrepAI/data/chunks.json`.
- **Shape:** A JSON array. Each element has `id`, `doc_id`, `text`, `metadata`. `doc_id` is like `{profile_id}_resume` or `{profile_id}_jd`.
- **Written by:** `retriever.add_document` from profile.py when a new profile is submitted (resume and JD are chunked and appended).
- **Read by:** Retriever (e.g. for `retrieve()` / `get_context_for_query()`). The current **Ask flow does not use chunks**; it uses full profile context from `profile_context.json` only.

---

## End-to-end flow summary

1. **Prep Guide (frontend → backend → data):**
   - User fills Prep form; Prep.jsx sends FormData to `POST /api/prep-guide` (or `/api/profile/init`).
   - profile.py parses form, extracts resume text (from file or field), fetches JD if URL, gets company name, picks a new profile_id, stores profile in `profile_context.json`, adds resume/JD to `chunks.json`, starts `summarize_profile_async`, POSTs to n8n, returns `profile_id` and `company_name`.
   - Prep.jsx appends `{ id: profile_id, companyName, role }` to `prepaiProfiles` in localStorage.

2. **Ask (frontend → backend → data):**
   - Ask.jsx loads the dropdown from `prepaiProfiles` (localStorage only). User selects an entry (by index); `profileId = profileList[selectedIndex].id`.
   - On “Ask”, frontend sends `POST /api/ask` with `question` and `user_id: profileId`.
   - ask.py loads the profile from `profile_context.json` via `get_profile_context(user_id)`, builds full context with `_full_profile_context(profile)`, gets the Ask provider (Groq if key set), calls `generate_json(...)`, returns answer, improvements, confidence, sources.

All of this uses only local code under `backend/`, `frontend/`, and the `data/` files produced at runtime; n8n is used only as an external webhook called by the backend.

