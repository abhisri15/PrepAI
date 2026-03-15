import { useCallback, useEffect, useState } from 'react'
import { ask, getProfile } from '../api'

const PREPAI_PROFILES_KEY = 'prepaiProfiles'
const PREPAI_PROFILE_ID_KEY = 'prepaiProfileId'

function loadProfileList() {
  try {
    const list = JSON.parse(localStorage.getItem(PREPAI_PROFILES_KEY) || '[]')
    if (Array.isArray(list) && list.length > 0) {
      const normalized = list.map((p) => ({
        id: p.id,
        companyName: p.companyName || 'Company',
        role: p.role || '',
      }))
      return normalized.reverse()
    }
  } catch (_) {}
  const singleId = localStorage.getItem(PREPAI_PROFILE_ID_KEY) || ''
  if (singleId) return [{ id: singleId, companyName: 'Saved profile', role: '' }]
  return []
}

export default function Ask() {
  const [question, setQuestion] = useState('')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [profileList, setProfileList] = useState([])
  const [selectedIndex, setSelectedIndex] = useState(0)
  const [profile, setProfile] = useState(null)

  const profileId = profileList[selectedIndex]?.id ?? ''

  const refreshProfile = useCallback((id) => {
    if (!id) {
      setProfile(null)
      return
    }
    getProfile(id)
      .then(setProfile)
      .catch(() => setProfile(null))
  }, [])

  useEffect(() => {
    const list = loadProfileList()
    setProfileList(list)
    setSelectedIndex(0)
    if (list.length > 0) refreshProfile(list[0].id)
  }, [refreshProfile])

  const handleProfileChange = (e) => {
    const index = Number(e.target.value)
    if (Number.isNaN(index) || index < 0 || index >= profileList.length) return
    setSelectedIndex(index)
    refreshProfile(profileList[index].id)
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setResult(null)
    setLoading(true)
    try {
      const data = await ask({ question, user_id: profileId || 'anonymous' })
      setResult(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-2xl">
      <h2 className="text-lg font-semibold text-slate-200 mb-4">Ask</h2>
      <p className="text-slate-500 text-sm mb-4">
        Select a profile (from Prep Guide) and ask interview questions. Answers use your summarized resume and JD for this role.
      </p>

      {profileList.length > 0 ? (
        <div className="mb-4 space-y-3">
          <label className="block text-sm text-slate-400">Profile (company / role)</label>
          <select
            value={selectedIndex}
            onChange={handleProfileChange}
            className="w-full px-4 py-2 rounded-lg bg-slate-800 border border-slate-700 text-slate-100 focus:ring-2 focus:ring-amber-500/50 focus:border-amber-500/50"
          >
            {profileList.map((p, index) => (
              <option key={`${p.id}-${index}`} value={index}>
                {p.companyName} {p.role ? ` — ${p.role}` : ''}
              </option>
            ))}
          </select>
          {profileId && (
            <div className="p-4 rounded-xl bg-slate-900/70 border border-slate-800 text-sm text-slate-300">
              <div className="text-slate-400">Summary status: {profile?.summary_status || 'pending'}</div>
              {profile?.summary && (
                <div className="mt-3 text-slate-400 line-clamp-6 whitespace-pre-wrap">{profile.summary}</div>
              )}
            </div>
          )}
        </div>
      ) : (
        <div className="mb-4 p-4 rounded-xl bg-rose-500/10 text-rose-300">
          Submit the <strong>Prep Guide</strong> form first (name, email, role, resume, JD link). Then come back here and select that profile to get personalized answers.
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <textarea
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Ask an interview question..."
          className="w-full h-24 px-4 py-3 rounded-xl bg-slate-800 border border-slate-700 text-slate-100 placeholder-slate-500 focus:ring-2 focus:ring-amber-500/50 focus:border-amber-500/50"
          required
        />
        <div className="flex gap-3">
          <button
            type="submit"
            disabled={loading || !profileId || profileList.length === 0}
            className="px-6 py-2 rounded-lg bg-amber-500 text-slate-900 font-medium hover:bg-amber-400 disabled:opacity-50"
          >
            {loading ? 'Thinking...' : 'Ask'}
          </button>
        </div>
      </form>

      {error && (
        <div className="mt-4 p-4 rounded-xl bg-rose-500/10 text-rose-400">
          {error}
        </div>
      )}

      {result && (
        <div className="mt-6 space-y-4">
          <div className="p-4 rounded-xl bg-slate-800/80 border border-slate-700">
            <div className="text-xs text-slate-500 uppercase mb-2">Answer</div>
            <div className="text-slate-200">{result.answer}</div>
          </div>
          {result.improvements?.length > 0 && (
            <div className="p-4 rounded-xl bg-slate-800/50">
              <div className="text-xs text-slate-500 uppercase mb-2">Improvements</div>
              <ul className="list-disc list-inside text-slate-300 space-y-1">
                {result.improvements.map((i, k) => (
                  <li key={k}>{i}</li>
                ))}
              </ul>
            </div>
          )}
          <div className="text-sm text-slate-500">
            Confidence: {(result.confidence * 100).toFixed(0)}%
          </div>
        </div>
      )}
    </div>
  )
}
