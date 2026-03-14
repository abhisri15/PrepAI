const API_BASE = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '')
const N8N_BASE = (import.meta.env.VITE_N8N_WEBHOOK_BASE_URL || '').replace(/\/$/, '')
const USE_N8N_PROXY = import.meta.env.VITE_USE_N8N_PROXY === 'true'

function buildUrl(base, path) {
  if (!base) return path
  return `${base}${path}`
}

function apiUrl(path) {
  return buildUrl(API_BASE, path)
}

function n8nUrl(path) {
  return buildUrl(N8N_BASE, path)
}

async function parseError(r) {
  const text = await r.text()
  try {
    const data = JSON.parse(text)
    return data.error || data.message || text || `Request failed: ${r.status}`
  } catch {
    return text || `Request failed: ${r.status}`
  }
}

function looksLikeBackendHealth(data) {
  return data && data.service === 'PrepAI' && data.status === 'ok'
}

async function postJson(url, body) {
  const r = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!r.ok) throw new Error(await parseError(r))
  return r.json()
}

async function postWithFallback({ primaryUrl, primaryBody, fallbackUrl, fallbackBody, isValid }) {
  const data = await postJson(primaryUrl, primaryBody)
  if (looksLikeBackendHealth(data) || (isValid && !isValid(data))) {
    return postJson(fallbackUrl, fallbackBody)
  }
  return data
}

export async function health() {
  const r = await fetch(apiUrl('/health'))
  if (!r.ok) throw new Error(await parseError(r))
  return r.json()
}

export async function ask({ question, context = '', user_id = 'anonymous' }) {
  if (USE_N8N_PROXY && N8N_BASE && API_BASE) {
    return postWithFallback({
      primaryUrl: n8nUrl('/prepai-webhook'),
      primaryBody: { action: 'ask', question, context, user_id },
      fallbackUrl: apiUrl('/api/ask'),
      fallbackBody: { question, context, user_id },
      isValid: (data) => typeof data?.answer === 'string',
    })
  }

  return postJson(USE_N8N_PROXY && N8N_BASE ? n8nUrl('/prepai-webhook') : apiUrl('/api/ask'),
    USE_N8N_PROXY && N8N_BASE ? { action: 'ask', question, context, user_id } : { question, context, user_id })
}

export async function evaluate({ question, candidate_answer }) {
  if (USE_N8N_PROXY && N8N_BASE && API_BASE) {
    return postWithFallback({
      primaryUrl: n8nUrl('/prepai-webhook'),
      primaryBody: { action: 'evaluate', question, candidate_answer },
      fallbackUrl: apiUrl('/api/evaluate'),
      fallbackBody: { question, candidate_answer },
      isValid: (data) => typeof data?.score !== 'undefined',
    })
  }

  return postJson(USE_N8N_PROXY && N8N_BASE ? n8nUrl('/prepai-webhook') : apiUrl('/api/evaluate'),
    USE_N8N_PROXY && N8N_BASE ? { action: 'evaluate', question, candidate_answer } : { question, candidate_answer })
}

export async function prepare({ resume_text, jd_text }) {
  if (USE_N8N_PROXY && N8N_BASE && API_BASE) {
    return postWithFallback({
      primaryUrl: n8nUrl('/resume-to-questions'),
      primaryBody: { resume: resume_text, jd: jd_text },
      fallbackUrl: apiUrl('/api/prepare'),
      fallbackBody: { resume_text, jd_text },
      isValid: (data) => Array.isArray(data?.strengths) || Array.isArray(data?.key_topics),
    })
  }

  return postJson(USE_N8N_PROXY && N8N_BASE ? n8nUrl('/resume-to-questions') : apiUrl('/api/prepare'),
    USE_N8N_PROXY && N8N_BASE ? { resume: resume_text, jd: jd_text } : { resume_text, jd_text })
}

export async function fetchJd(jd_url) {
  return postJson(apiUrl('/api/fetch-jd'), { jd_url })
}

export async function submitToN8n({ name, email, role, jd_url, jd_text, resume, additional_notes }) {
  const body = { name, email, role, jd_url, jd_text, resume, additional_notes }

  if (N8N_BASE && API_BASE) {
    return postWithFallback({
      primaryUrl: n8nUrl('/prepai-submit'),
      primaryBody: body,
      fallbackUrl: apiUrl('/api/n8n/submit'),
      fallbackBody: body,
      isValid: (data) => typeof data?.message === 'string' || data?.status === 'accepted',
    })
  }

  return postJson(N8N_BASE ? n8nUrl('/prepai-submit') : apiUrl('/api/n8n/submit'), body)
}

export async function upload(text, doc_id) {
  return postJson(apiUrl('/api/upload'), { text, doc_id })
}
