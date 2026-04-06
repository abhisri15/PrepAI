import { useCallback, useEffect, useState } from 'react'
import { getProfile } from '../api'

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

function ChipList({ items, color }) {
  const colorMap = {
    green: 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300',
    red: 'bg-rose-500/10 border-rose-500/30 text-rose-300',
    blue: 'bg-sky-500/10 border-sky-500/30 text-sky-300',
    amber: 'bg-amber-500/10 border-amber-500/30 text-amber-300',
  }
  if (!items || items.length === 0) return <span className="text-slate-500 text-sm italic">Not available yet</span>
  return (
    <div className="flex flex-wrap gap-2">
      {items.map((item, i) => (
        <span key={i} className={`px-3 py-1.5 rounded-full border text-xs font-medium ${colorMap[color] || colorMap.blue}`}>
          {item}
        </span>
      ))}
    </div>
  )
}

export default function GapAnalysis() {
  const [profileList] = useState(loadProfileList)
  const [selectedIndex, setSelectedIndex] = useState(0)
  const [profile, setProfile] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const profileId = profileList[selectedIndex]?.id ?? ''

  const loadProfile = useCallback((id) => {
    if (!id) { setProfile(null); return }
    setLoading(true)
    setError('')
    getProfile(id)
      .then((p) => { setProfile(p); setLoading(false) })
      .catch((err) => { setError(err.message); setProfile(null); setLoading(false) })
  }, [])

  useEffect(() => {
    if (profileList.length > 0) loadProfile(profileList[0].id)
  }, [profileList, loadProfile])

  const handleProfileChange = (e) => {
    const idx = Number(e.target.value)
    setSelectedIndex(idx)
    loadProfile(profileList[idx]?.id)
  }

  const summaryReady = profile && profile.summary_status === 'complete'
  const hasFitHighlights = profile?.fit_highlights?.length > 0
  const hasLikelyGaps = profile?.likely_gaps?.length > 0
  const hasFocusAreas = profile?.focus_areas?.length > 0
  const hasData = hasFitHighlights || hasLikelyGaps || hasFocusAreas

  return (
    <div className="max-w-3xl">
      <h2 className="text-lg font-semibold text-slate-200 mb-1">Gap Analysis</h2>
      <p className="text-slate-500 text-sm mb-5">
        See your strengths, gaps, and focus areas based on your resume vs the job description.
      </p>

      {profileList.length === 0 ? (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-sm">
          Submit a <strong>Prep Guide</strong> first. The AI will analyse your profile and surface gaps here.
        </div>
      ) : (
        <>
          <div className="mb-6">
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

          {loading && <div className="text-slate-500 text-sm">Loading profile...</div>}
          {error && <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 text-sm">{error}</div>}

          {profile && !loading && (
            <div className="space-y-5">
              {/* Status */}
              <div className="flex items-center gap-3 p-4 rounded-xl bg-slate-800/60 border border-slate-700">
                <div className={`w-2.5 h-2.5 rounded-full shrink-0 ${
                  summaryReady ? 'bg-emerald-500' : profile.summary_status === 'failed' ? 'bg-rose-500' : 'bg-amber-500 animate-pulse'
                }`} />
                <div className="flex-1">
                  <span className="text-sm text-slate-300 font-medium">
                    {profile.company_name}{profile.role ? ` — ${profile.role}` : ''}
                  </span>
                  <span className="text-slate-500 text-sm ml-3">
                    Summary: {profile.summary_status}
                  </span>
                </div>
              </div>

              {!summaryReady && !hasData && (
                <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-300 text-sm">
                  {profile.summary_status === 'failed'
                    ? 'Summary generation failed. Try submitting again via Prep Guide.'
                    : 'Summary is still being generated. Refresh in a few seconds.'}
                </div>
              )}

              {/* Summary */}
              {profile.summary && (
                <div className="p-5 rounded-xl bg-slate-800/40 border border-slate-700">
                  <h3 className="text-sm font-medium text-slate-300 mb-2">Profile Summary</h3>
                  <p className="text-slate-400 text-sm leading-relaxed whitespace-pre-wrap">{profile.summary}</p>
                </div>
              )}

              {/* Resume summary */}
              {profile.resume_summary && (
                <div className="p-5 rounded-xl bg-slate-800/40 border border-slate-700">
                  <h3 className="text-sm font-medium text-sky-400 mb-2">Resume Highlights</h3>
                  <p className="text-slate-400 text-sm leading-relaxed whitespace-pre-wrap">{profile.resume_summary}</p>
                </div>
              )}

              {/* JD summary */}
              {profile.jd_summary && (
                <div className="p-5 rounded-xl bg-slate-800/40 border border-slate-700">
                  <h3 className="text-sm font-medium text-violet-400 mb-2">Role Expectations</h3>
                  <p className="text-slate-400 text-sm leading-relaxed whitespace-pre-wrap">{profile.jd_summary}</p>
                </div>
              )}

              {/* Fit Highlights */}
              {hasFitHighlights && (
                <div className="p-5 rounded-xl bg-slate-800/40 border border-slate-700">
                  <h3 className="text-sm font-medium text-emerald-400 mb-3">Your Strengths (Fit Highlights)</h3>
                  <ChipList items={profile.fit_highlights} color="green" />
                </div>
              )}

              {/* Likely Gaps */}
              {hasLikelyGaps && (
                <div className="p-5 rounded-xl bg-slate-800/40 border border-slate-700">
                  <h3 className="text-sm font-medium text-rose-400 mb-3">Gaps to Address</h3>
                  <ChipList items={profile.likely_gaps} color="red" />
                </div>
              )}

              {/* Focus Areas */}
              {hasFocusAreas && (
                <div className="p-5 rounded-xl bg-slate-800/40 border border-slate-700">
                  <h3 className="text-sm font-medium text-amber-400 mb-3">Focus Areas for Interview Prep</h3>
                  <ol className="space-y-2">
                    {profile.focus_areas.map((area, i) => (
                      <li key={i} className="flex gap-3 text-sm text-slate-300">
                        <span className="text-amber-500 font-mono text-xs mt-0.5 shrink-0">{String(i + 1).padStart(2, '0')}</span>
                        <span>{area}</span>
                      </li>
                    ))}
                  </ol>
                </div>
              )}
            </div>
          )}
        </>
      )}
    </div>
  )
}
