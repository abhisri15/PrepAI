import { useState } from 'react'
import { ask, evaluate } from '../api'

export default function Demo() {
  const [mode, setMode] = useState('ask')
  const [question, setQuestion] = useState('How would you explain microservices to a non-technical stakeholder?')
  const [answer, setAnswer] = useState('')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleAsk = async () => {
    setError('')
    setResult(null)
    setLoading(true)
    try {
      const data = await ask({ question })
      setResult({ type: 'ask', data })
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleEvaluate = async () => {
    if (!answer.trim()) {
      setError('Enter a candidate answer first.')
      return
    }
    setError('')
    setResult(null)
    setLoading(true)
    try {
      const data = await evaluate({ question, candidate_answer: answer })
      setResult({ type: 'evaluate', data })
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-2xl">
      <h2 className="text-lg font-semibold text-slate-200 mb-4">Demo</h2>
      <p className="text-slate-500 text-sm mb-4">
        Quick demo flow: Ask a question, then evaluate an answer.
      </p>
      <div className="flex gap-2 mb-4">
        <button
          onClick={() => setMode('ask')}
          className={`px-4 py-2 rounded-lg ${mode === 'ask' ? 'bg-amber-500 text-slate-900' : 'bg-slate-800 text-slate-400'}`}
        >
          Ask
        </button>
        <button
          onClick={() => setMode('evaluate')}
          className={`px-4 py-2 rounded-lg ${mode === 'evaluate' ? 'bg-amber-500 text-slate-900' : 'bg-slate-800 text-slate-400'}`}
        >
          Evaluate
        </button>
      </div>

      <div className="space-y-4">
        <div>
          <label className="block text-sm text-slate-400 mb-1">Question</label>
          <textarea
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            className="w-full h-20 px-4 py-3 rounded-xl bg-slate-800 border border-slate-700 text-slate-100"
          />
        </div>
        {mode === 'evaluate' && (
          <div>
            <label className="block text-sm text-slate-400 mb-1">Candidate Answer</label>
            <textarea
              value={answer}
              onChange={(e) => setAnswer(e.target.value)}
              placeholder="Your answer to the question..."
              className="w-full h-24 px-4 py-3 rounded-xl bg-slate-800 border border-slate-700 text-slate-100 placeholder-slate-500"
            />
          </div>
        )}
        <button
          onClick={mode === 'ask' ? handleAsk : handleEvaluate}
          disabled={loading}
          className="px-6 py-2 rounded-lg bg-amber-500 text-slate-900 font-medium hover:bg-amber-400 disabled:opacity-50"
        >
          {loading ? 'Processing...' : mode === 'ask' ? 'Get Answer' : 'Evaluate'}
        </button>
      </div>

      {error && (
        <div className="mt-4 p-4 rounded-xl bg-rose-500/10 text-rose-400">{error}</div>
      )}

      {result && result.type === 'ask' && (
        <div className="mt-6 p-4 rounded-xl bg-slate-800/80 border border-slate-700">
          <div className="text-xs text-slate-500 uppercase mb-2">Answer</div>
          <div className="text-slate-200">{result.data.answer}</div>
          {result.data.improvements?.length > 0 && (
            <div className="mt-2 text-sm text-slate-400">
              Improvements: {result.data.improvements.join('; ')}
            </div>
          )}
        </div>
      )}

      {result && result.type === 'evaluate' && (
        <div className="mt-6 space-y-2 p-4 rounded-xl bg-slate-800/80 border border-slate-700">
          <div className="text-2xl font-semibold text-amber-400">
            Score: {result.data.score}/10
          </div>
          <div className="text-slate-300">{result.data.rationale}</div>
          {result.data.improvements?.length > 0 && (
            <ul className="list-disc list-inside text-slate-400 text-sm">
              {result.data.improvements.map((i, k) => (
                <li key={k}>{i}</li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  )
}
