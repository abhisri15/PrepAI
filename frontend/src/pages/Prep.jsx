import { useState } from 'react'
import { prepare, fetchJd, submitToN8n } from '../api'

export default function Prep() {
  const [mode, setMode] = useState('instant')
  const [resume, setResume] = useState('')
  const [jd, setJd] = useState('')
  const [jdUrl, setJdUrl] = useState('')
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [role, setRole] = useState('')
  const [notes, setNotes] = useState('')
  const [result, setResult] = useState(null)
  const [n8nMessage, setN8nMessage] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleInstant = async (e) => {
    e.preventDefault()
    setError('')
    setResult(null)
    setLoading(true)
    try {
      let jdText = jd
      if (jdUrl.trim()) {
        const { jd_text } = await fetchJd(jdUrl.trim())
        jdText = jd_text
      }
      if (!jdText && !jdUrl) {
        throw new Error('Paste job description or provide JD URL')
      }
      const data = await prepare({ resume_text: resume, jd_text: jdText })
      setResult(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleN8n = async (e) => {
    e.preventDefault()
    setError('')
    setN8nMessage(null)
    setLoading(true)
    try {
      const payload = {
        name,
        email,
        role: role || 'Software Engineer',
        resume,
        additional_notes: notes,
      }
      if (jdUrl.trim()) payload.jd_url = jdUrl.trim()
      else if (jd.trim()) payload.jd_text = jd
      else throw new Error('Provide job description URL or paste JD text')
      const data = await submitToN8n(payload)
      setN8nMessage(data.message || 'Check your email for the full guide!')
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-2xl">
      <h2 className="text-lg font-semibold text-slate-200 mb-4">Prep Guide</h2>
      <div className="flex gap-2 mb-4">
        <button
          type="button"
          onClick={() => { setMode('instant'); setError(''); setResult(null); setN8nMessage(null) }}
          className={`px-4 py-2 rounded-lg ${mode === 'instant' ? 'bg-amber-500 text-slate-900' : 'bg-slate-800 text-slate-400'}`}
        >
          Instant roadmap
        </button>
        <button
          type="button"
          onClick={() => { setMode('n8n'); setError(''); setResult(null); setN8nMessage(null) }}
          className={`px-4 py-2 rounded-lg ${mode === 'n8n' ? 'bg-amber-500 text-slate-900' : 'bg-slate-800 text-slate-400'}`}
        >
          Full guide via email
        </button>
      </div>
      <p className="text-slate-500 text-sm mb-4">
        {mode === 'instant'
          ? 'Paste resume and job description (or JD URL) for a quick roadmap.'
          : 'Submit for a detailed, seniority-based guide sent to your email (requires n8n).'}
      </p>

      {mode === 'instant' && (
        <form onSubmit={handleInstant} className="space-y-4">
          <div>
            <label className="block text-sm text-slate-400 mb-1">Resume</label>
            <textarea
              value={resume}
              onChange={(e) => setResume(e.target.value)}
              placeholder="Paste your resume..."
              className="w-full h-32 px-4 py-3 rounded-xl bg-slate-800 border border-slate-700 text-slate-100 placeholder-slate-500"
              required
            />
          </div>
          <div>
            <label className="block text-sm text-slate-400 mb-1">Job description URL (optional)</label>
            <input
              value={jdUrl}
              onChange={(e) => setJdUrl(e.target.value)}
              placeholder="https://..."
              className="w-full px-4 py-2 rounded-lg bg-slate-800 border border-slate-700 text-slate-100"
            />
          </div>
          <div>
            <label className="block text-sm text-slate-400 mb-1">Job description text (or leave empty if using URL)</label>
            <textarea
              value={jd}
              onChange={(e) => setJd(e.target.value)}
              placeholder="Paste job description..."
              className="w-full h-24 px-4 py-3 rounded-xl bg-slate-800 border border-slate-700 text-slate-100 placeholder-slate-500"
            />
          </div>
          <button
            type="submit"
            disabled={loading || (!jd.trim() && !jdUrl.trim())}
            className="px-6 py-2 rounded-lg bg-amber-500 text-slate-900 font-medium hover:bg-amber-400 disabled:opacity-50"
          >
            {loading ? 'Generating...' : 'Generate roadmap'}
          </button>
        </form>
      )}

      {mode === 'n8n' && (
        <form onSubmit={handleN8n} className="space-y-4">
          <div>
            <label className="block text-sm text-slate-400 mb-1">Your name</label>
            <input
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Jane Doe"
              className="w-full px-4 py-2 rounded-lg bg-slate-800 border border-slate-700 text-slate-100"
              required
            />
          </div>
          <div>
            <label className="block text-sm text-slate-400 mb-1">Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="jane@example.com"
              className="w-full px-4 py-2 rounded-lg bg-slate-800 border border-slate-700 text-slate-100"
              required
            />
          </div>
          <div>
            <label className="block text-sm text-slate-400 mb-1">Role you're applying for</label>
            <input
              value={role}
              onChange={(e) => setRole(e.target.value)}
              placeholder="ML Engineer"
              className="w-full px-4 py-2 rounded-lg bg-slate-800 border border-slate-700 text-slate-100"
            />
          </div>
          <div>
            <label className="block text-sm text-slate-400 mb-1">Resume</label>
            <textarea
              value={resume}
              onChange={(e) => setResume(e.target.value)}
              placeholder="Paste your resume..."
              className="w-full h-28 px-4 py-3 rounded-xl bg-slate-800 border border-slate-700 text-slate-100 placeholder-slate-500"
              required
            />
          </div>
          <div>
            <label className="block text-sm text-slate-400 mb-1">Job description URL (preferred)</label>
            <input
              value={jdUrl}
              onChange={(e) => setJdUrl(e.target.value)}
              placeholder="https://..."
              className="w-full px-4 py-2 rounded-lg bg-slate-800 border border-slate-700 text-slate-100"
            />
          </div>
          <div>
            <label className="block text-sm text-slate-400 mb-1">Or paste job description</label>
            <textarea
              value={jd}
              onChange={(e) => setJd(e.target.value)}
              placeholder="If no URL..."
              className="w-full h-20 px-4 py-3 rounded-xl bg-slate-800 border border-slate-700 text-slate-100 placeholder-slate-500"
            />
          </div>
          <div>
            <label className="block text-sm text-slate-400 mb-1">Additional notes</label>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Optional"
              className="w-full h-16 px-4 py-2 rounded-lg bg-slate-800 border border-slate-700 text-slate-100"
            />
          </div>
          <button
            type="submit"
            disabled={loading || (!jd.trim() && !jdUrl.trim())}
            className="px-6 py-2 rounded-lg bg-amber-500 text-slate-900 font-medium hover:bg-amber-400 disabled:opacity-50"
          >
            {loading ? 'Submitting...' : 'Get guide via email'}
          </button>
        </form>
      )}

      {error && (
        <div className="mt-4 p-4 rounded-xl bg-rose-500/10 text-rose-400">{error}</div>
      )}

      {n8nMessage && (
        <div className="mt-4 p-4 rounded-xl bg-emerald-500/10 text-emerald-400">{n8nMessage}</div>
      )}

      {result && (
        <div className="mt-6 space-y-4">
          <Section title="Strengths" items={result.strengths} />
          <Section title="Weaknesses" items={result.weaknesses} />
          <Section title="Key Topics" items={result.key_topics} />
          <Section title="Practice Questions" items={result.practice_questions} />
          <Section title="Study Plan" items={result.study_plan} />
        </div>
      )}
    </div>
  )
}

function Section({ title, items }) {
  if (!items?.length) return null
  return (
    <div className="p-4 rounded-xl bg-slate-800/80 border border-slate-700">
      <div className="text-xs text-slate-500 uppercase mb-2">{title}</div>
      <ul className="list-disc list-inside text-slate-300 space-y-1">
        {items.map((i, k) => (
          <li key={k}>{i}</li>
        ))}
      </ul>
    </div>
  )
}
