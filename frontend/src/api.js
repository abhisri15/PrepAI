const API_BASE = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '')

function apiUrl(path) {
  if (!API_BASE) return path
  return `${API_BASE}${path}`
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

async function postForm(url, formData) {
  const r = await fetch(url, {
    method: 'POST',
    body: formData,
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

export async function health() {
  const r = await fetch(apiUrl('/health'))
  if (!r.ok) throw new Error(await parseError(r))
  return r.json()
}

export async function ask({ question, context = '', user_id = 'anonymous' }) {
  return postJson(apiUrl('/api/ask'), { question, context, user_id })
}

export async function initProfileFlow(payload) {
  if (!API_BASE) {
    throw new Error('VITE_API_BASE_URL is required for profile flow orchestration.')
  }
  if (payload instanceof FormData) {
    return postForm(apiUrl('/api/profile/init'), payload)
  }
  return postJson(apiUrl('/api/prep-guide'), payload)
}

export async function getProfile(profileId) {
  if (!API_BASE) {
    throw new Error('VITE_API_BASE_URL is required to fetch profile context.')
  }
  const r = await fetch(apiUrl(`/api/profile/${encodeURIComponent(profileId)}`))
  if (!r.ok) throw new Error(await parseError(r))
  return r.json()
}

export async function upload(input, doc_id, options = {}) {
  if (input instanceof File) {
    const formData = new FormData()
    formData.append('file', input)
    if (doc_id) formData.append('doc_id', doc_id)
    if (options.profile_id) formData.append('profile_id', options.profile_id)
    if (options.source) formData.append('source', options.source)
    return postForm(apiUrl('/api/upload'), formData)
  }

  return postJson(apiUrl('/api/upload'), {
    text: input,
    doc_id,
    profile_id: options.profile_id,
    source: options.source,
  })
}
