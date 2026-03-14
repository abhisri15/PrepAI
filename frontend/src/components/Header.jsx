import { useEffect } from 'react'

const API_BASE = '/api'

export default function Header({ health, setHealth }) {
  useEffect(() => {
    fetch('/health')
      .then((r) => r.json())
      .then(setHealth)
      .catch(() => setHealth({ status: 'error', provider: 'unknown' }))
  }, [setHealth])

  return (
    <header className="border-b border-slate-800 bg-slate-900/80 px-6 py-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold text-amber-400 tracking-tight">
          PrepAI
        </h1>
        <div className="flex items-center gap-4 text-sm">
          <span className="text-slate-500">Provider:</span>
          <span className="font-mono text-slate-300">
            {health.provider || health.model || 'mock'}
          </span>
          <span
            className={`w-2 h-2 rounded-full ${
              health.status === 'ok' ? 'bg-emerald-500' : 'bg-rose-500'
            }`}
            title={health.status}
          />
        </div>
      </div>
    </header>
  )
}
