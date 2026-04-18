import { useState } from 'react'
import { editEquation } from '../services/api'
import { VoiceInput } from './VoiceInput'

export function EditCommand({ currentLatex, onEdit }) {
  const [command, setCommand] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  async function submit() {
    if (!command.trim() || !currentLatex) return
    setLoading(true)
    setError(null)
    try {
      const res = await editEquation(currentLatex, command)
      onEdit(res.latex)
      setCommand('')
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <form
      className="edit-command"
      onSubmit={(e) => {
        e.preventDefault()
        submit()
      }}
    >
      <label htmlFor="edit-command">Edit the equation</label>
      <div className="edit-command-row">
        <input
          id="edit-command"
          type="text"
          value={command}
          onChange={(e) => setCommand(e.target.value)}
          placeholder='e.g. "replace minus 5 with plus 7"'
          disabled={loading}
        />
        <button type="submit" disabled={loading || !command.trim()}>
          {loading ? 'Editing\u2026' : 'Apply'}
        </button>
      </div>
      <VoiceInput onTranscript={setCommand} disabled={loading} />
      {error && <div className="error">{error}</div>}
    </form>
  )
}
