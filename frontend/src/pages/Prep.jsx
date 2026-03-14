import { useState } from 'react'
import { prepare } from '../api'

export default function Prep() {
  const [resume, setResume] = useState('')
  const [jd, setJd] = useState('')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setResult(null)
    setLoading(true)
    try {
      const data = await prepare({ resume_text: resume, jd_text: jd })
      setResult(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-2xl">
      <h2 className="text-lg font-semibold text-slate-200 mb-4">Prep Guide</h2>
      <p className="text-slate-500 text-sm mb-4">
        Paste resume and job description to get a preparation roadmap.
      </p>
      <form onSubmit={handleSubmit} className="space-y-4">
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
          <label className="block text-sm text-slate-400 mb-1">Job Description</label>
          <textarea
            value={jd}
            onChange={(e) => setJd(e.target.value)}
            placeholder="Paste job description..."
            className="w-full h-32 px-4 py-3 rounded-xl bg-slate-800 border border-slate-700 text-slate-100 placeholder-slate-500"
            required
          />
        </div>
        <button
          type="submit"
          disabled={loading}
          className="px-6 py-2 rounded-lg bg-amber-500 text-slate-900 font-medium hover:bg-amber-400 disabled:opacity-50"
        >
          {loading ? 'Generating...' : 'Generate Roadmap'}
        </button>
      </form>

      {error && (
        <div className="mt-4 p-4 rounded-xl bg-rose-500/10 text-rose-400">{error}</div>
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
