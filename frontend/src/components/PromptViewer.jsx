export default function PromptViewer({ prompt, visible }) {
  if (!visible || !prompt) return null
  return (
    <div className="mt-4 p-4 rounded-xl bg-slate-900 border border-slate-700 font-mono text-sm overflow-x-auto">
      <div className="text-slate-500 text-xs mb-2">PROMPT SENT TO AI</div>
      <pre className="whitespace-pre-wrap text-slate-300">{prompt}</pre>
    </div>
  )
}
