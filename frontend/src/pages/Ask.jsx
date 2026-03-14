import { useState } from 'react'
import { ask } from '../api'
import PromptViewer from '../components/PromptViewer'
import { buildAskPromptPreview } from '../promptPreview'

export default function Ask() {
  const [question, setQuestion] = useState('')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [showPrompt, setShowPrompt] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setResult(null)
    setLoading(true)
    try {
      const data = await ask({ question, user_id: 'demo' })
      setResult(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const promptPreview = question ? buildAskPromptPreview(question, '') : ''

  return (
    <div className="max-w-2xl">
      <h2 className="text-lg font-semibold text-slate-200 mb-4">Interview Q&A</h2>
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
            disabled={loading}
            className="px-6 py-2 rounded-lg bg-amber-500 text-slate-900 font-medium hover:bg-amber-400 disabled:opacity-50"
          >
            {loading ? 'Thinking...' : 'Ask'}
          </button>
          <label className="flex items-center gap-2 text-sm text-slate-400 cursor-pointer">
            <input
              type="checkbox"
              checked={showPrompt}
              onChange={(e) => setShowPrompt(e.target.checked)}
            />
            Show prompt
          </label>
        </div>
      </form>

      <PromptViewer prompt={promptPreview} visible={showPrompt} />

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
