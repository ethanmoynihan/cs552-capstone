const API_BASE = '/api'

export async function generateLatex(text) {
  const res = await fetch(`${API_BASE}/generate-latex`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text }),
  })
  if (!res.ok) {
    throw new Error(`generate-latex failed: ${res.status}`)
  }
  return res.json()
}
