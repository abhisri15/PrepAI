# PrepAI — End-to-End Flow (Which File Gets Triggered When)

This document traces **which file runs at each step** when a user uses the app. Two main flows: **Prep Guide** (submit profile) and **Ask** (Q&A with a selected profile).

---

## 1. App load (first thing that runs)

| Step | What runs | File |
|------|------------|------|
| 1 | User opens the app in the browser | `frontend/index.html` → Vite loads `frontend/src/main.jsx` |
| 2 | React mounts, router and routes are set up | `frontend/src/main.jsx` → renders `App` from `frontend/src/App.jsx` |
| 3 | App renders Header, nav, and routes | `frontend/src/App.jsx` |
| 4 | Header mounts and calls health API | `frontend/src/components/Header.jsx` → `useEffect` calls `health()` from `frontend/src/api.js` |
| 5 | Health request hits backend | **Backend:** `backend/app.py` → route `GET /health` → returns JSON (status, model, provider) |
| 6 | User sees either **Prep Guide** (`/`) or **Ask** (`/ask`) | `App.jsx` `<Routes>` → `<Prep />` or `<Ask />` |

---

## 2. Prep Guide flow (user submits profile)

User is on **Prep Guide** (`/`), fills the form (name, email, role, resume file/text, JD URL/text, notes), and clicks Submit.

| Step | What runs | File |
|------|------------|------|
| 1 | User submits the form | `frontend/src/pages/Prep.jsx` → `handleSubmit()` |
| 2 | Prep builds `FormData` and calls API | `Prep.jsx` → `initProfileFlow(formData)` from `frontend/src/api.js` |
| 3 | Frontend sends POST (FormData) | `frontend/src/api.js` → `postForm(apiUrl('/api/profile/init'), formData)` → `fetch()` to backend |
| 4 | Request hits Flask | **Backend:** `backend/app.py` receives request → **profile_bp** handles it |
| 5 | Profile route handler runs | `backend/api/profile.py` → `init_profile_flow()` (registered on both `/api/profile/init` and `/api/prep-guide`) |
| 6 | Parse body (form → dict, file → text) | `backend/api/profile.py` → `_parse_request_payload()` → if file present, `services/document_parser.py` → `extract_text_from_upload()` |
| 7 | Validate: resume and JD required | `backend/api/profile.py` → returns 400 if missing |
| 8 | If JD URL given, fetch JD text | `backend/api/profile.py` → `services/jd_fetcher.py` → `fetch_job_description(jd_url)` |
| 9 | Get company name | `backend/api/profile.py` → `extract_company_name_from_url(jd_url)` or `extract_company_name_from_jd_text(jd_text)` from `services/jd_fetcher.py` |
| 10 | Generate profile ID | `backend/api/profile.py` → `_pick_profile_id(payload)` → new UUID (e.g. `profile-abc123def456`) |
| 11 | Save profile to disk | `backend/api/profile.py` → `models.store_profile_context(profile_id, {...})` → **backend/models.py** → reads/writes `data/profile_context.json` |
| 12 | Index resume and JD for retrieval | `backend/api/profile.py` → `services/retriever.py` → `add_document(profile_id_resume, ...)` and `add_document(profile_id_jd, ...)` → writes to `data/chunks.json` |
| 13 | Start background summary (Gemini) | `backend/api/profile.py` → `services/profile_summary.py` → `summarize_profile_async(...)` (runs in thread, updates `profile_context.json` when done) |
| 14 | Call n8n webhook | `backend/api/profile.py` → `services/n8n_client.py` → `post_webhook(webhook_url, n8n_payload)` → POST to e.g. `https://prepai.app.n8n.cloud/webhook/interview-prep` |
| 15 | Return success to frontend | `backend/api/profile.py` → `jsonify({ profile_id, company_name, message })` |
| 16 | Frontend receives response | `frontend/src/api.js` → `postForm` resolves → `unwrapN8nResponse` → returns data to Prep.jsx |
| 17 | Prep saves to localStorage and shows message | `frontend/src/pages/Prep.jsx` → `localStorage.setItem('prepaiProfileId', ...)`, append to `prepaiProfiles` array, `setStatusMessage(data.message)` |

**Prep Guide flow summary:**  
`Prep.jsx` → `api.js` (initProfileFlow → postForm) → **app.py** → **profile.py** → document_parser (if file) / jd_fetcher (if URL) / **models.py** (store) / retriever (chunks) / profile_summary (async) / n8n_client (webhook) → response back to **api.js** → **Prep.jsx** (localStorage + UI).

---

## 3. Ask flow (user selects profile and asks a question)

User goes to **Ask** (`/ask`), picks a profile from the dropdown, types a question, and clicks Ask.

| Step | What runs | File |
|------|------------|------|
| 1 | Ask page mounts | `frontend/src/pages/Ask.jsx` |
| 2 | Load profile list from localStorage | `frontend/src/pages/Ask.jsx` → `loadProfileList()` → `localStorage.getItem('prepaiProfiles')` → newest first |
| 3 | Fetch first profile details from backend | `frontend/src/pages/Ask.jsx` → `refreshProfile(list[0].id)` → `getProfile(id)` from `frontend/src/api.js` |
| 4 | GET profile request | `frontend/src/api.js` → `fetch(apiUrl('/api/profile/' + profileId))` |
| 5 | Backend returns profile | **Backend:** `backend/app.py` → **profile_bp** → `backend/api/profile.py` → `get_profile(profile_id)` → **models.py** `get_profile_context(profile_id)` → read `data/profile_context.json` → jsonify profile |
| 6 | User selects another profile (optional) | `Ask.jsx` → `handleProfileChange` → `setSelectedIndex` → `refreshProfile(profileList[index].id)` → same GET `/api/profile/<id>` as above |
| 7 | User types question and clicks Ask | `frontend/src/pages/Ask.jsx` → `handleSubmit()` |
| 8 | Ask calls API with question and profile id | `frontend/src/pages/Ask.jsx` → `ask({ question, user_id: profileId })` from `frontend/src/api.js` |
| 9 | Frontend sends POST | `frontend/src/api.js` → `postJson(apiUrl('/api/ask'), { question, context, user_id })` → `fetch()` to backend |
| 10 | Request hits Flask | **Backend:** `backend/app.py` → **ask_bp** handles `/api/ask` |
| 11 | Ask route handler runs | `backend/api/ask.py` → `ask()` |
| 12 | Load profile from disk | `backend/api/ask.py` → `models.get_profile_context(user_id)` → **backend/models.py** → read `data/profile_context.json` |
| 13 | Build full context (summary or resume+JD) | `backend/api/ask.py` → `_full_profile_context(profile)` |
| 14 | Redact PII from question | `backend/api/ask.py` → `services/security.py` → `redact_pii(question)` |
| 15 | Choose LLM (Groq if key set) | `backend/api/ask.py` → `services/llm_provider.py` → `get_ask_provider()` |
| 16 | Build prompt | `backend/api/ask.py` → `services/prompt_templates.py` → `build_ask_prompt(question, full_context)` |
| 17 | Call LLM and parse JSON | `backend/api/ask.py` → `services/llm_provider.py` → `generate_json(user_prompt, system=..., provider=...)` → Groq/OpenAI/etc. API call |
| 18 | Return answer to frontend | `backend/api/ask.py` → `jsonify({ answer, improvements, confidence, sources })` |
| 19 | Frontend receives and displays | `frontend/src/api.js` → `postJson` resolves → `Ask.jsx` → `setResult(data)` → UI shows answer, improvements, confidence, sources |

**Ask flow summary:**  
`Ask.jsx` → (dropdown) `api.js` getProfile → **app.py** → **profile.py** get_profile → **models.py**.  
(On Ask click) `Ask.jsx` → `api.js` ask → postJson → **app.py** → **ask.py** → **models.py** (get profile) → **prompt_templates** (build prompt) → **llm_provider** (Groq/other) → **ask.py** returns JSON → **api.js** → **Ask.jsx** (setResult).

---

## 4. Quick reference: file roles

| File | Role |
|------|------|
| **frontend/src/App.jsx** | Router, nav, routes; mounts Header, Prep, Ask. |
| **frontend/src/components/Header.jsx** | On mount: calls `health()`; displays status and provider. |
| **frontend/src/api.js** | `health()`, `ask()`, `initProfileFlow()`, `getProfile()`; `postJson` / `postForm`; talks to backend. |
| **frontend/src/pages/Prep.jsx** | Form; on submit → `initProfileFlow(formData)`; updates localStorage and message. |
| **frontend/src/pages/Ask.jsx** | Dropdown from localStorage; `getProfile(id)` for details; on Ask → `ask({ question, user_id })`; shows result. |
| **backend/app.py** | Flask app; CORS; registers ask_bp and profile_bp; `GET /`, `GET /health`. |
| **backend/api/profile.py** | POST `/api/prep-guide` and `/api/profile/init` (form → parse, validate, JD fetch, store, retriever, summary, n8n); GET `/api/profile/<id>`. |
| **backend/api/ask.py** | POST `/api/ask` (load profile, build context, prompt, LLM, return JSON). |
| **backend/models.py** | `data/profile_context.json`: ensure_data_dir, load/save map, store_profile_context, get_profile_context. |
| **backend/services/jd_fetcher.py** | Fetch JD from URL; extract company name from URL or JD text. |
| **backend/services/document_parser.py** | Extract text from uploaded resume (PDF, DOCX, TXT). |
| **backend/services/n8n_client.py** | POST payload to n8n webhook URL. |
| **backend/services/profile_summary.py** | Background: Gemini summarizes resume+JD, updates profile in `profile_context.json`. |
| **backend/services/retriever.py** | Chunk and append to `data/chunks.json` (Ask currently uses full profile context, not retrieval). |
| **backend/services/prompt_templates.py** | `build_ask_prompt(question, retrieved_context)` for Ask. |
| **backend/services/llm_provider.py** | `get_ask_provider()` (Groq if key set), `generate_json()` → call LLM, parse JSON. |
| **backend/services/security.py** | `redact_pii(question)` before sending to LLM. |

---

## 5. Data flow in one picture

```
User browser
    │
    ├─► [Prep]  Prep.jsx ──► api.js (initProfileFlow, postForm) ──► POST /api/profile/init
    │                                                                      │
    │                                                    backend/app.py ───┘
    │                                                                      ▼
    │                                                          profile.py (init_profile_flow)
    │                                                                      │
    │                    ┌─────────────────────────────────────────────────┼─────────────────────────────────────┐
    │                    ▼                 ▼                 ▼             ▼                 ▼                     ▼
    │            document_parser    jd_fetcher         models.py    retriever    profile_summary    n8n_client
    │            (file → text)   (URL→JD, company)   (profile_context.json) (chunks.json)  (async Gemini)   (webhook)
    │                    │                 │                 │             │                 │                     │
    │                    └─────────────────────────────────────────────────┴─────────────────┴─────────────────────┘
    │                                                                      │
    │◄─────────────────────────────────────────────────────────────────────┘
    │   profile_id, company_name, message
    │
    ├─► [Ask]   Ask.jsx ──► api.js (getProfile) ──► GET /api/profile/:id ──► app.py ──► profile.py (get_profile) ──► models.py
    │
    │   Ask.jsx ──► api.js (ask) ──► POST /api/ask ──► app.py ──► ask.py
    │                                                                 │
    │                                         models.get_profile_context ──► profile_context.json
    │                                         prompt_templates.build_ask_prompt
    │                                         llm_provider.get_ask_provider + generate_json ──► Groq (or other)
    │                                                                 │
    │◄────────────────────────────────────────────────────────────────┘
    │   answer, improvements, confidence, sources
```

This is the full flow: which file gets triggered and in what order for both Prep Guide and Ask.
