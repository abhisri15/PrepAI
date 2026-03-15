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
        throw new Error('Provide resume as file or paste text (your choice)')
      }

      if (!jd.trim() && !jdUrl.trim()) {
        throw new Error('Provide job description as URL or paste text (your choice)')
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
        const companyName = data.company_name || 'Company'
        const roleLabel = data.role || role || 'Software Engineer'
        const list = JSON.parse(localStorage.getItem('prepaiProfiles') || '[]')
        list.push({ id: data.profile_id, companyName, role: roleLabel })
        localStorage.setItem('prepaiProfiles', JSON.stringify(list))
      }
      setStatusMessage(data.message || 'Full prep guide will be sent via email. You can use Ask to get personalized answers for this role in the meantime.')
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
            <label className="block text-sm text-slate-400 mb-1">Resume — file or text (your choice)</label>
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
            <p className="text-xs text-slate-500 mt-1">Provide either a file (txt, pdf, docx) or paste text. Backend will use file content if both are provided.</p>
          </div>
          <div>
            <label className="block text-sm text-slate-400 mb-1">Job description — URL or text (your choice)</label>
            <input
              value={jdUrl}
              onChange={(e) => setJdUrl(e.target.value)}
              placeholder="Paste JD URL (e.g. https://...)"
              className="w-full px-4 py-2 rounded-lg bg-slate-800 border border-slate-700 text-slate-100 mb-2"
            />
            <textarea
              value={jd}
              onChange={(e) => setJd(e.target.value)}
              placeholder="Or paste job description text here..."
              className="w-full h-20 px-4 py-3 rounded-xl bg-slate-800 border border-slate-700 text-slate-100 placeholder-slate-500"
            />
            <p className="text-xs text-slate-500 mt-1">Provide either a link or pasted JD text. Backend will fetch from URL if given, else use pasted text.</p>
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
            <div className="mt-2 text-sm text-emerald-300">
              Profile saved. Open <strong>Ask</strong> and select this role to get personalized interview answers.
            </div>
          )}
        </div>
      )}
    </div>
  )
}
