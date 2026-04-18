export function TranscriptPane({ value, onChange, onSubmit, loading }) {
  const disabled = loading || !value.trim()
  return (
    <form
      className="transcript-pane"
      onSubmit={(e) => {
        e.preventDefault()
        if (!disabled) onSubmit()
      }}
    >
      <label htmlFor="transcript">Transcript (edit before submitting)</label>
      <textarea
        id="transcript"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder="Record your equation, or type here"
        rows={3}
      />
      <button type="submit" disabled={disabled}>
        {loading ? 'Generating\u2026' : 'Generate LaTeX'}
      </button>
    </form>
  )
}
