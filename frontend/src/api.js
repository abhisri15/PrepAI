/**
 * API client for PrepAI backend.
 * All endpoints use proxy: /api -> http://localhost:5000
 */
const BASE = ''

export async function health() {
  const r = await fetch(`${BASE}/health`)
  return r.json()
}

export async function ask({ question, context = '', user_id = 'anonymous' }) {
  const r = await fetch(`${BASE}/api/ask`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question, context, user_id }),
  })
  if (!r.ok) throw new Error(await r.text())
  return r.json()
}

export async function evaluate({ question, candidate_answer }) {
  const r = await fetch(`${BASE}/api/evaluate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question, candidate_answer }),
  })
  if (!r.ok) throw new Error(await r.text())
  return r.json()
}

export async function prepare({ resume_text, jd_text }) {
  const r = await fetch(`${BASE}/api/prepare`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ resume_text, jd_text }),
  })
  if (!r.ok) throw new Error(await r.text())
  return r.json()
}

export async function fetchJd(jd_url) {
  const r = await fetch(`${BASE}/api/fetch-jd`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ jd_url }),
  })
  if (!r.ok) throw new Error(await r.text())
  return r.json()
}

export async function submitToN8n({ name, email, role, jd_url, jd_text, resume, additional_notes }) {
  const r = await fetch(`${BASE}/api/n8n/submit`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, email, role, jd_url, jd_text, resume, additional_notes }),
  })
  if (!r.ok) {
    const err = await r.json().catch(() => ({}))
    throw new Error(err.error || err.message || `Request failed: ${r.status}`)
  }
  return r.json()
}

export async function upload(text, doc_id) {
  const r = await fetch(`${BASE}/api/upload`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text, doc_id }),
  })
  if (!r.ok) throw new Error(await r.text())
  return r.json()
}
