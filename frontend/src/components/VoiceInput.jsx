import { useState } from 'react'
import { useAudioRecorder } from '../hooks/useAudioRecorder'
import { transcribe } from '../services/speechProvider'

export function VoiceInput({ onTranscript, disabled }) {
  const { isRecording, error: recError, start, stop } = useAudioRecorder()
  const [transcribing, setTranscribing] = useState(false)
  const [error, setError] = useState(null)

  async function handleClick() {
    setError(null)
    if (!isRecording) {
      await start()
      return
    }
    const blob = await stop()
    if (!blob || blob.size === 0) {
      setError('No audio captured')
      return
    }
    setTranscribing(true)
    try {
      const { transcript } = await transcribe(blob)
      onTranscript(transcript)
    } catch (err) {
      setError(err.message)
    } finally {
      setTranscribing(false)
    }
  }

  const busy = disabled || transcribing
  const label = transcribing
    ? 'Transcribing\u2026'
    : isRecording
      ? 'Stop Recording'
      : 'Record'

  return (
    <div className="voice-input">
      <button type="button" onClick={handleClick} disabled={busy}>
        {label}
      </button>
      {isRecording && <span className="recording-indicator" aria-live="polite">● recording</span>}
      {(error || recError) && <div className="error">{error || recError}</div>}
    </div>
  )
}
