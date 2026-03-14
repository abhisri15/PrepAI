import { useState } from 'react'
import { upload } from '../api'

export default function Upload() {
  const [text, setText] = useState('')
  const [docId, setDocId] = useState('')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setResult(null)
    setLoading(true)
    try {
      const data = await upload(text, docId || undefined)
      setResult(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-2xl">
      <h2 className="text-lg font-semibold text-slate-200 mb-4">Upload Documents</h2>
      <p className="text-slate-500 text-sm mb-4">
        Add text for vector retrieval. Used for RAG context in the Ask tab.
      </p>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm text-slate-400 mb-1">Document ID (optional)</label>
          <input
            value={docId}
            onChange={(e) => setDocId(e.target.value)}
            placeholder="e.g. resume-1"
            className="w-full px-4 py-2 rounded-lg bg-slate-800 border border-slate-700 text-slate-100"
          />
        </div>
        <div>
          <label className="block text-sm text-slate-400 mb-1">Text content</label>
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="Paste your document content here..."
            className="w-full h-48 px-4 py-3 rounded-xl bg-slate-800 border border-slate-700 text-slate-100 placeholder-slate-500"
            required
          />
        </div>
        <button
          type="submit"
          disabled={loading}
          className="px-6 py-2 rounded-lg bg-amber-500 text-slate-900 font-medium hover:bg-amber-400 disabled:opacity-50"
        >
          {loading ? 'Indexing...' : 'Upload & Index'}
        </button>
      </form>

      {error && (
        <div className="mt-4 p-4 rounded-xl bg-rose-500/10 text-rose-400">{error}</div>
      )}

      {result && (
        <div className="mt-4 p-4 rounded-xl bg-emerald-500/10 text-emerald-400">
          ✓ {result.message}
          {result.chunks_indexed > 0 && (
            <span className="block text-sm mt-1">
              {result.chunks_indexed} chunks indexed.
            </span>
          )}
        </div>
      )}
    </div>
  )
}
