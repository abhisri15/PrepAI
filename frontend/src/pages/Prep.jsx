import { useState } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { initProfileFlow } from '../api'

const MODES = {
  instant: {
    label: 'Instant Guide',
    icon: '⚡',
    desc: 'Generate your prep guide right here — no email needed.',
    button: 'Generate Guide',
  },
  n8n: {
    label: 'Email via n8n',
    icon: '📧',
    desc: 'Qualify, classify, and receive a full prep guide in your inbox.',
    button: 'Submit & Email Guide',
  },
}

const LEVEL_LABELS = {
  fresher: { label: 'Fresher', color: 'text-sky-400 bg-sky-500/10 border-sky-500/30' },
  mid_level: { label: 'Mid-Level', color: 'text-amber-400 bg-amber-500/10 border-amber-500/30' },
  senior: { label: 'Senior', color: 'text-violet-400 bg-violet-500/10 border-violet-500/30' },
}

export default function Prep() {
  const [mode, setMode] = useState('instant')
  const [resumeFile, setResumeFile] = useState(null)
  const [resume, setResume] = useState('')
  const [jd, setJd] = useState('')
  const [jdUrl, setJdUrl] = useState('')
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [role, setRole] = useState('')
  const [notes, setNotes] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [result, setResult] = useState(null)   // { profile_id, message, guide?, level?, mode }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setResult(null)
    setLoading(true)

    try {
      if (!resume.trim() && !resumeFile) {
        throw new Error('Provide your resume as a file upload or pasted text.')
      }
      if (!jd.trim() && !jdUrl.trim()) {
        throw new Error('Provide the job description as a URL or pasted text.')
      }
      if (mode === 'n8n' && !email.trim()) {
        throw new Error('Email is required for the Email via n8n mode.')
      }

      const formData = new FormData()
      formData.append('mode', mode)
      formData.append('name', name)
      formData.append('email', email)
      formData.append('role', role || 'Software Engineer')
      formData.append('additional_notes', notes)
      if (jdUrl.trim()) formData.append('jd_url', jdUrl.trim())
      if (jd.trim()) formData.append('jd_text', jd.trim())
      if (resume.trim()) formData.append('resume_text', resume.trim())
      if (resumeFile) formData.append('resume_file', resumeFile)

      const data = await initProfileFlow(formData)

      if (data.profile_id) {
        localStorage.setItem('prepaiProfileId', data.profile_id)
        const companyName = data.company_name || 'Company'
        const roleLabel = role || 'Software Engineer'
        const list = JSON.parse(localStorage.getItem('prepaiProfiles') || '[]')
        list.push({ id: data.profile_id, companyName, role: roleLabel })
        localStorage.setItem('prepaiProfiles', JSON.stringify(list))
      }

      setResult(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const levelInfo = result?.level ? LEVEL_LABELS[result.level] : null

  return (
    <div className="max-w-3xl">
      <h2 className="text-lg font-semibold text-slate-200 mb-1">Prep Guide</h2>
      <p className="text-slate-500 text-sm mb-5">
        Submit your resume and the job description once. We store a summary so Ask can answer questions with your context.
      </p>

      {/* ── Mode selector ─────────────────────────────────────────────────── */}
      <div className="grid grid-cols-2 gap-3 mb-6">
        {Object.entries(MODES).map(([key, cfg]) => (
          <button
            key={key}
            type="button"
            onClick={() => { setMode(key); setResult(null); setError('') }}
            className={`text-left p-4 rounded-xl border transition-all ${
              mode === key
                ? 'border-amber-500 bg-amber-500/10 text-slate-100'
                : 'border-slate-700 bg-slate-800/60 text-slate-400 hover:border-slate-500'
            }`}
          >
            <div className="text-base font-medium mb-1">
              <span className="mr-2">{cfg.icon}</span>{cfg.label}
            </div>
            <div className="text-xs text-slate-500 leading-snug">{cfg.desc}</div>
          </button>
        ))}
      </div>

      {/* ── Form ──────────────────────────────────────────────────────────── */}
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
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
            <label className="block text-sm text-slate-400 mb-1">
              Email {mode === 'n8n' ? <span className="text-rose-400">*</span> : <span className="text-slate-600">(optional)</span>}
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="jane@example.com"
              className="w-full px-4 py-2 rounded-lg bg-slate-800 border border-slate-700 text-slate-100"
              required={mode === 'n8n'}
            />
          </div>
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
          <label className="block text-sm text-slate-400 mb-1">Resume — file or paste text</label>
          <input
            type="file"
            accept=".txt,.pdf,.docx"
            onChange={(e) => setResumeFile(e.target.files?.[0] || null)}
            className="w-full px-4 py-2 rounded-lg bg-slate-800 border border-slate-700 text-slate-300 mb-2"
          />
          <textarea
            value={resume}
            onChange={(e) => setResume(e.target.value)}
            placeholder="Or paste your resume text here..."
            className="w-full h-28 px-4 py-3 rounded-xl bg-slate-800 border border-slate-700 text-slate-100 placeholder-slate-500"
          />
        </div>

        <div>
          <label className="block text-sm text-slate-400 mb-1">Job description — URL or paste text</label>
          <input
            value={jdUrl}
            onChange={(e) => setJdUrl(e.target.value)}
            placeholder="Paste JD URL (https://...)"
            className="w-full px-4 py-2 rounded-lg bg-slate-800 border border-slate-700 text-slate-100 mb-2"
          />
          <textarea
            value={jd}
            onChange={(e) => setJd(e.target.value)}
            placeholder="Or paste job description text here..."
            className="w-full h-20 px-4 py-3 rounded-xl bg-slate-800 border border-slate-700 text-slate-100 placeholder-slate-500"
          />
        </div>

        <div>
          <label className="block text-sm text-slate-400 mb-1">Additional notes <span className="text-slate-600">(optional)</span></label>
          <textarea
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="Anything specific you want the guide to focus on..."
            className="w-full h-16 px-4 py-2 rounded-lg bg-slate-800 border border-slate-700 text-slate-100"
          />
        </div>

        <button
          type="submit"
          disabled={loading}
          className="px-6 py-2.5 rounded-lg bg-amber-500 text-slate-900 font-medium hover:bg-amber-400 disabled:opacity-50 transition-colors"
        >
          {loading
            ? (mode === 'instant' ? 'Generating guide...' : 'Submitting...')
            : MODES[mode].button}
        </button>
      </form>

      {/* ── Error ─────────────────────────────────────────────────────────── */}
      {error && (
        <div className="mt-5 p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 text-sm">
          {error}
        </div>
      )}

      {/* ── Result ────────────────────────────────────────────────────────── */}
      {result && (
        <div className="mt-6">
          {/* Status bar */}
          <div className="flex items-start gap-3 p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20 mb-4">
            <span className="text-emerald-400 mt-0.5">✓</span>
            <div className="flex-1 text-sm">
              <p className="text-emerald-300">{result.message}</p>
              {result.profile_id && (
                <p className="text-emerald-500 mt-1">
                  Profile saved. Open <strong>Ask</strong> and select this role for personalised answers.
                </p>
              )}
            </div>
            {levelInfo && (
              <span className={`shrink-0 px-2.5 py-1 rounded-full border text-xs font-medium ${levelInfo.color}`}>
                {levelInfo.label}
              </span>
            )}
          </div>

          {/* Instant guide content */}
          {result.mode === 'instant' && result.guide && (
            <div className="rounded-xl bg-slate-800/60 border border-slate-700 overflow-hidden">
              <div className="flex items-center justify-between px-5 py-3 border-b border-slate-700 bg-slate-800">
                <span className="text-sm font-medium text-slate-300">Your Personalised Prep Guide</span>
                <button
                  onClick={() => {
                    navigator.clipboard?.writeText(result.guide)
                  }}
                  className="text-xs text-slate-500 hover:text-slate-300 transition-colors"
                >
                  Copy
                </button>
              </div>
              <div className="px-6 py-5 prose prose-invert prose-sm max-w-none
                prose-headings:text-slate-200 prose-headings:font-semibold
                prose-h2:text-base prose-h2:mt-6 prose-h2:mb-2
                prose-h3:text-sm prose-h3:mt-4 prose-h3:mb-1
                prose-p:text-slate-400 prose-p:leading-relaxed
                prose-li:text-slate-400 prose-li:leading-relaxed
                prose-strong:text-slate-300
                prose-a:text-amber-400 prose-a:no-underline hover:prose-a:underline
                prose-code:text-amber-300 prose-code:bg-slate-700 prose-code:px-1 prose-code:rounded
                prose-hr:border-slate-700">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {result.guide}
                </ReactMarkdown>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
