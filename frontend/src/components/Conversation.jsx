export default function Conversation({ messages }) {
  return (
    <div className="space-y-4">
      {messages.map((m, i) => (
        <div
          key={i}
          className={`p-4 rounded-xl ${
            m.role === 'user'
              ? 'bg-amber-500/10 border border-amber-500/20 ml-8'
              : 'bg-slate-800/80 border border-slate-700 mr-8'
          }`}
        >
          <div className="text-xs text-slate-500 mb-1 uppercase tracking-wider">
            {m.role}
          </div>
          <div className="text-slate-200">{m.content}</div>
        </div>
      ))}
    </div>
  )
}
