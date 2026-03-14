import { useState } from 'react'
import { initProfileFlow } from '../api'

export default function Prep() {
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

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setStatusMessage('')
    setLoading(true)
    try {
      if (!resume.trim() && !resumeFile) {
        throw new Error('Paste resume text or upload a resume file')
      }

      if (!jd.trim() && !jdUrl.trim()) {
        throw new Error('Provide a job description URL or paste JD text')
      }

      const formData = new FormData()
      formData.append('name', name)
      formData.append('email', email)
      formData.append('role', role || 'Software Engineer')
      formData.append('additional_notes', notes)
      if (jdUrl.trim()) formData.append('jd_url', jdUrl.trim())
      if (jd.trim()) formData.append('jd_text', jd.trim())
      if (resume.trim()) formData.append('resume_text', resume.trim())
      if (resumeFile) formData.append('resume_file', resumeFile)

      const data = await initProfileFlow(formData)
      setProfileId(data.profile_id || '')
      if (data.profile_id) {
        localStorage.setItem('prepaiProfileId', data.profile_id)
      }
      setStatusMessage(data.message || 'Detailed prep guide will be sent via email. Please prepare accordingly.')
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
        Submit your profile once. We will send a detailed prep guide to your email and also store a summary so Ask can answer using your resume and JD context.
      </p>

      <form onSubmit={handleSubmit} className="space-y-4">
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
            <label className="block text-sm text-slate-400 mb-1">Resume text</label>
            <textarea
              value={resume}
              onChange={(e) => setResume(e.target.value)}
              placeholder="Paste your resume here, or upload a file below..."
              className="w-full h-28 px-4 py-3 rounded-xl bg-slate-800 border border-slate-700 text-slate-100 placeholder-slate-500"
            />
          </div>
          <div>
            <label className="block text-sm text-slate-400 mb-1">Resume file (txt, pdf, docx)</label>
            <input
              type="file"
              accept=".txt,.pdf,.docx"
              onChange={(e) => setResumeFile(e.target.files?.[0] || null)}
              className="w-full px-4 py-2 rounded-lg bg-slate-800 border border-slate-700 text-slate-300"
            />
          </div>
          <div>
            <label className="block text-sm text-slate-400 mb-1">Job description URL</label>
            <input
              value={jdUrl}
              onChange={(e) => setJdUrl(e.target.value)}
              placeholder="https://..."
              className="w-full px-4 py-2 rounded-lg bg-slate-800 border border-slate-700 text-slate-100"
            />
          </div>
          <div>
            <label className="block text-sm text-slate-400 mb-1">Or paste job description text</label>
            <textarea
              value={jd}
              onChange={(e) => setJd(e.target.value)}
              placeholder="If you already have JD text, paste it here..."
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
            disabled={loading}
            className="px-6 py-2 rounded-lg bg-amber-500 text-slate-900 font-medium hover:bg-amber-400 disabled:opacity-50"
          >
            {loading ? 'Submitting...' : 'Submit And Email Guide'}
          </button>
      </form>

      {error && (
        <div className="mt-4 p-4 rounded-xl bg-rose-500/10 text-rose-400">{error}</div>
      )}

      {statusMessage && (
        <div className="mt-4 p-4 rounded-xl bg-emerald-500/10 text-emerald-400">
          <div>{statusMessage}</div>
          {profileId && (
            <div className="mt-2 text-sm text-emerald-300">Profile stored for Ask with id: {profileId}</div>
          )}
        </div>
      )}
    </div>
  )
}
