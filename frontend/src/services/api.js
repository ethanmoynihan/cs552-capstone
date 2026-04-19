// Dev: '/api' — Vite proxies to http://localhost:8000.
// Prod: set VITE_API_BASE_URL to the deployed Space URL (e.g. https://<user>-<space>.hf.space).
const API_BASE = import.meta.env.VITE_API_BASE_URL ?? '/api'

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

export async function editEquation(currentLatex, editCommand) {
  const res = await fetch(`${API_BASE}/edit-equation`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ current_latex: currentLatex, edit_command: editCommand }),
  })
  if (!res.ok) {
    throw new Error(`edit-equation failed: ${res.status}`)
  }
  return res.json()
}

export async function listTestCases() {
  const res = await fetch(`${API_BASE}/evaluation/test-cases`)
  if (!res.ok) {
    throw new Error(`test-cases failed: ${res.status}`)
  }
  return res.json()
}

export async function runTestCase(id) {
  const res = await fetch(`${API_BASE}/evaluation/run-case`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ id }),
  })
  if (!res.ok) {
    throw new Error(`run-case failed for ${id}: ${res.status}`)
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
