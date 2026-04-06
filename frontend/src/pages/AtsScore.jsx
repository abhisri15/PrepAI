import { useCallback, useEffect, useState } from 'react'
import { getAtsScore, getProfile } from '../api'

const PREPAI_PROFILES_KEY = 'prepaiProfiles'
const PREPAI_PROFILE_ID_KEY = 'prepaiProfileId'

function loadProfileList() {
  try {
    const list = JSON.parse(localStorage.getItem(PREPAI_PROFILES_KEY) || '[]')
    if (Array.isArray(list) && list.length > 0) {
      return list.map((p) => ({
        id: p.id,
        companyName: p.companyName || 'Company',
        role: p.role || '',
      })).reverse()
    }
  } catch (_) {}
  const singleId = localStorage.getItem(PREPAI_PROFILE_ID_KEY) || ''
  if (singleId) return [{ id: singleId, companyName: 'Saved profile', role: '' }]
  return []
}

function ScoreRing({ score, size = 120 }) {
  const radius = (size - 12) / 2
  const circumference = 2 * Math.PI * radius
  const offset = circumference - (score / 100) * circumference
  const color = score >= 75 ? '#22c55e' : score >= 50 ? '#f59e0b' : '#ef4444'
  return (
    <svg width={size} height={size} className="block">
      <circle cx={size / 2} cy={size / 2} r={radius} fill="none" stroke="#1e293b" strokeWidth="10" />
      <circle
        cx={size / 2} cy={size / 2} r={radius} fill="none"
        stroke={color} strokeWidth="10" strokeLinecap="round"
        strokeDasharray={circumference} strokeDashoffset={offset}
        style={{ transform: 'rotate(-90deg)', transformOrigin: '50% 50%', transition: 'stroke-dashoffset 0.8s ease' }}
      />
      <text x="50%" y="50%" textAnchor="middle" dy="0.35em" className="fill-slate-100 text-2xl font-bold">
        {score}
      </text>
    </svg>
  )
}

function CategoryBar({ label, value }) {
  const color = value >= 75 ? 'bg-emerald-500' : value >= 50 ? 'bg-amber-500' : 'bg-rose-500'
  return (
    <div>
      <div className="flex justify-between text-sm mb-1">
        <span className="text-slate-400 capitalize">{label}</span>
        <span className="text-slate-300 font-medium">{value}%</span>
      </div>
      <div className="h-2 rounded-full bg-slate-700 overflow-hidden">
        <div className={`h-full rounded-full ${color} transition-all duration-700`} style={{ width: `${value}%` }} />
      </div>
    </div>
  )
}

export default function AtsScore() {
  const [profileList] = useState(loadProfileList)
  const [selectedIndex, setSelectedIndex] = useState(0)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [result, setResult] = useState(null)
  const [profile, setProfile] = useState(null)

  const profileId = profileList[selectedIndex]?.id ?? ''

  const loadProfile = useCallback((id) => {
    if (!id) return
    getProfile(id).then(setProfile).catch(() => setProfile(null))
  }, [])

  useEffect(() => {
    if (profileList.length > 0) loadProfile(profileList[0].id)
  }, [profileList, loadProfile])

  const handleProfileChange = (e) => {
    const idx = Number(e.target.value)
    setSelectedIndex(idx)
    setResult(null)
    setError('')
    loadProfile(profileList[idx]?.id)
  }

  const handleAnalyse = async () => {
    if (!profileId) return
    setLoading(true)
    setError('')
    setResult(null)
    try {
      const data = await getAtsScore(profileId)
      setResult(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-3xl">
      <h2 className="text-lg font-semibold text-slate-200 mb-1">ATS Score</h2>
      <p className="text-slate-500 text-sm mb-5">
        See how well your resume matches the job description. Get keyword analysis and actionable suggestions.
      </p>

      {profileList.length === 0 ? (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-sm">
          Submit a <strong>Prep Guide</strong> first, then come back to check your ATS score.
        </div>
      ) : (
        <>
          <div className="flex gap-3 items-end mb-6">
            <div className="flex-1">
              <label className="block text-sm text-slate-400 mb-1">Select profile</label>
              <select
                value={selectedIndex}
                onChange={handleProfileChange}
                className="w-full px-4 py-2 rounded-lg bg-slate-800 border border-slate-700 text-slate-100"
              >
                {profileList.map((p, i) => (
                  <option key={`${p.id}-${i}`} value={i}>
                    {p.companyName}{p.role ? ` — ${p.role}` : ''}
                  </option>
                ))}
              </select>
            </div>
            <button
              onClick={handleAnalyse}
              disabled={loading || !profileId}
              className="px-6 py-2 rounded-lg bg-amber-500 text-slate-900 font-medium hover:bg-amber-400 disabled:opacity-50 transition-colors whitespace-nowrap"
            >
              {loading ? 'Analysing...' : 'Analyse'}
            </button>
          </div>

          {error && (
            <div className="mb-5 p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 text-sm">{error}</div>
          )}

          {result && (
            <div className="space-y-5">
              {/* Score overview */}
              <div className="flex items-center gap-8 p-6 rounded-xl bg-slate-800/60 border border-slate-700">
                <ScoreRing score={result.score} />
                <div className="flex-1">
                  <h3 className="text-slate-200 font-semibold mb-1">Overall ATS Score</h3>
                  <p className="text-slate-400 text-sm leading-relaxed">{result.summary}</p>
                </div>
              </div>

              {/* Category scores */}
              {result.category_scores && Object.keys(result.category_scores).length > 0 && (
                <div className="p-5 rounded-xl bg-slate-800/40 border border-slate-700 space-y-3">
                  <h3 className="text-sm font-medium text-slate-300 mb-2">Category Breakdown</h3>
                  {Object.entries(result.category_scores).map(([key, val]) => (
                    <CategoryBar key={key} label={key} value={val} />
                  ))}
                </div>
              )}

              {/* Keywords */}
              <div className="grid grid-cols-2 gap-4">
                <div className="p-5 rounded-xl bg-slate-800/40 border border-slate-700">
                  <h3 className="text-sm font-medium text-emerald-400 mb-3">Matched Keywords</h3>
                  <div className="flex flex-wrap gap-2">
                    {(result.matched_keywords || []).map((kw, i) => (
                      <span key={i} className="px-2.5 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs">
                        {kw}
                      </span>
                    ))}
                    {(!result.matched_keywords || result.matched_keywords.length === 0) && (
                      <span className="text-slate-500 text-sm">None detected</span>
                    )}
                  </div>
                </div>
                <div className="p-5 rounded-xl bg-slate-800/40 border border-slate-700">
                  <h3 className="text-sm font-medium text-rose-400 mb-3">Missing Keywords</h3>
                  <div className="flex flex-wrap gap-2">
                    {(result.missing_keywords || []).map((kw, i) => (
                      <span key={i} className="px-2.5 py-1 rounded-full bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs">
                        {kw}
                      </span>
                    ))}
                    {(!result.missing_keywords || result.missing_keywords.length === 0) && (
                      <span className="text-slate-500 text-sm">None — great match!</span>
                    )}
                  </div>
                </div>
              </div>

              {/* Suggestions */}
              {result.suggestions && result.suggestions.length > 0 && (
                <div className="p-5 rounded-xl bg-slate-800/40 border border-slate-700">
                  <h3 className="text-sm font-medium text-amber-400 mb-3">Suggestions to Improve</h3>
                  <ul className="space-y-2">
                    {result.suggestions.map((s, i) => (
                      <li key={i} className="flex gap-2 text-sm text-slate-300">
                        <span className="text-amber-500 shrink-0 mt-0.5">→</span>
                        <span>{s}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </>
      )}
    </div>
  )
}
