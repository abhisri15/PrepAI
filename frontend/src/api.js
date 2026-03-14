const API_BASE = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '')
const N8N_BASE = (import.meta.env.VITE_N8N_WEBHOOK_BASE_URL || '').replace(/\/$/, '')

const N8N_ASK_URL = import.meta.env.VITE_N8N_ASK_WEBHOOK_URL || ''
const N8N_PREPARE_URL = import.meta.env.VITE_N8N_PREPARE_WEBHOOK_URL || ''
const N8N_SUBMIT_URL = import.meta.env.VITE_N8N_SUBMIT_WEBHOOK_URL || ''

const USE_N8N_PROXY = import.meta.env.VITE_USE_N8N_PROXY === 'true'
const N8N_ONLY_MODE = import.meta.env.VITE_N8N_ONLY_MODE === 'true'

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

function getAskEndpoint() {
  if (N8N_ASK_URL) return N8N_ASK_URL
  return n8nUrl('/prepai-webhook')
}

function getPrepareEndpoint() {
  if (N8N_PREPARE_URL) return N8N_PREPARE_URL
  return n8nUrl('/resume-to-questions')
}

function getSubmitEndpoint() {
  if (N8N_SUBMIT_URL) return N8N_SUBMIT_URL
  return n8nUrl('/prepai-submit')
}

async function parseError(r) {
  const text = await r.text()
  if (!text.trim()) {
    return `Request failed: ${r.status}`
  }
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

function extractJsonFromText(text) {
  const trimmed = (text || '').trim()
  if (!trimmed) return null

  const fenced = trimmed.match(/```(?:json)?\s*([\s\S]*?)\s*```/i)
  const candidate = fenced ? fenced[1].trim() : trimmed
  try {
    return JSON.parse(candidate)
  } catch {
    const objectLike = candidate.match(/\{[\s\S]*\}/)
    if (!objectLike) return null
    try {
      return JSON.parse(objectLike[0])
    } catch {
      return null
    }
  }
}

function unwrapN8nResponse(data) {
  if (Array.isArray(data) && data.length) {
    return unwrapN8nResponse(data[0])
  }
  if (!data || typeof data !== 'object') return data
  if (data.json && typeof data.json === 'object') return unwrapN8nResponse(data.json)
  if (data.body && typeof data.body === 'object') return unwrapN8nResponse(data.body)
  if (data.data && typeof data.data === 'object') return unwrapN8nResponse(data.data)
  if (data.message && typeof data.message === 'object' && typeof data.message.content === 'string') {
    const parsed = extractJsonFromText(data.message.content)
    return parsed || data
  }
  if (typeof data.output === 'string') {
    const parsed = extractJsonFromText(data.output)
    return parsed || data
  }
  return data
}

async function postJson(url, body) {
  const r = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!r.ok) throw new Error(await parseError(r))
  const text = await r.text()
  if (!text.trim()) {
    throw new Error('Received an empty response from the service.')
  }

  try {
    return unwrapN8nResponse(JSON.parse(text))
  } catch {
    const parsed = extractJsonFromText(text)
    if (parsed) return unwrapN8nResponse(parsed)
    throw new Error('Received an invalid JSON response from the service.')
  }
}

async function postWithFallback({ primaryUrl, primaryBody, fallbackUrl, fallbackBody, isValid }) {
  try {
    const data = await postJson(primaryUrl, primaryBody)
    if (looksLikeBackendHealth(data) || (isValid && !isValid(data))) {
      if (!fallbackUrl) {
        throw new Error('Primary webhook did not return expected payload.')
      }
      return postJson(fallbackUrl, fallbackBody)
    }
    return data
  } catch (error) {
    if (!fallbackUrl) {
      throw error
    }
    return postJson(fallbackUrl, fallbackBody)
  }
}

export async function health() {
  const r = await fetch(apiUrl('/health'))
  if (!r.ok) throw new Error(await parseError(r))
  return r.json()
}

export async function ask({ question, context = '', user_id = 'anonymous' }) {
  if (USE_N8N_PROXY && (N8N_BASE || N8N_ASK_URL)) {
    const primaryUrl = getAskEndpoint()
    const fallbackUrl = !N8N_ONLY_MODE && API_BASE ? apiUrl('/api/ask') : ''
    return postWithFallback({
      primaryUrl,
      primaryBody: { action: 'ask', question, context, user_id },
      fallbackUrl,
      fallbackBody: { question, context, user_id },
      isValid: (data) => typeof data?.answer === 'string',
    })
  }

  return postJson(USE_N8N_PROXY && N8N_BASE ? n8nUrl('/prepai-webhook') : apiUrl('/api/ask'),
    USE_N8N_PROXY && N8N_BASE ? { action: 'ask', question, context, user_id } : { question, context, user_id })
}

export async function evaluate({ question, candidate_answer }) {
  if (USE_N8N_PROXY && (N8N_BASE || N8N_ASK_URL)) {
    const primaryUrl = getAskEndpoint()
    const fallbackUrl = !N8N_ONLY_MODE && API_BASE ? apiUrl('/api/evaluate') : ''
    return postWithFallback({
      primaryUrl,
      primaryBody: { action: 'evaluate', question, candidate_answer },
      fallbackUrl,
      fallbackBody: { question, candidate_answer },
      isValid: (data) => typeof data?.score !== 'undefined',
    })
  }

  return postJson(USE_N8N_PROXY && N8N_BASE ? n8nUrl('/prepai-webhook') : apiUrl('/api/evaluate'),
    USE_N8N_PROXY && N8N_BASE ? { action: 'evaluate', question, candidate_answer } : { question, candidate_answer })
}

export async function prepare({ resume_text, jd_text }) {
  if (USE_N8N_PROXY && (N8N_BASE || N8N_PREPARE_URL || N8N_ASK_URL)) {
    const primaryUrl = getPrepareEndpoint() || getAskEndpoint()
    const primaryBody = N8N_PREPARE_URL || N8N_BASE
      ? { resume: resume_text, jd: jd_text }
      : { action: 'prepare', resume_text, jd_text }
    const fallbackUrl = !N8N_ONLY_MODE && API_BASE ? apiUrl('/api/prepare') : ''
    return postWithFallback({
      primaryUrl,
      primaryBody,
      fallbackUrl,
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

  if (N8N_BASE || N8N_SUBMIT_URL) {
    const fallbackUrl = !N8N_ONLY_MODE && API_BASE ? apiUrl('/api/n8n/submit') : ''
    return postWithFallback({
      primaryUrl: getSubmitEndpoint(),
      primaryBody: body,
      fallbackUrl,
      fallbackBody: body,
      isValid: (data) => typeof data?.message === 'string' || data?.status === 'accepted',
    })
  }

  return postJson(N8N_BASE ? n8nUrl('/prepai-submit') : apiUrl('/api/n8n/submit'), body)
}

export async function upload(text, doc_id) {
  return postJson(apiUrl('/api/upload'), { text, doc_id })
}
