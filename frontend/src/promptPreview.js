/**
 * Client-side prompt preview (mirrors backend templates for demo).
 * Shows what prompt structure is sent to the AI.
 */
export function buildAskPromptPreview(question, context) {
  const ctx = context || '(No additional context)'
  return `[System]
You are an expert interview preparation assistant...

[User]
Context (retrieved from knowledge base):
${ctx}

Question:
${question}

Return JSON: { answer, improvements, confidence, sources }`
}
