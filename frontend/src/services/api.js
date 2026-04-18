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

export async function transcribeAudio(blob) {
  const form = new FormData()
  const filename = blob.type.includes('webm') ? 'audio.webm' : 'audio.bin'
  form.append('audio', blob, filename)
  const res = await fetch(`${API_BASE}/transcribe`, {
    method: 'POST',
    body: form,
  })
  if (!res.ok) {
    const detail = await res.text()
    throw new Error(`transcribe failed: ${res.status} ${detail}`)
  }
  return res.json()
}
