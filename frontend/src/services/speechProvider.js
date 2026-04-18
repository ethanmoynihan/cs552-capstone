import { transcribeAudio } from './api'

const PROVIDER = import.meta.env.VITE_SPEECH_PROVIDER ?? 'whisper'

export function getProvider() {
  return PROVIDER
}

export async function transcribe(blob) {
  if (PROVIDER === 'webSpeech') {
    throw new Error(
      'webSpeech provider does not accept audio blobs — use startWebSpeechSession() instead',
    )
  }
  const { transcript, inference_time_ms } = await transcribeAudio(blob)
  return { transcript, inferenceTimeMs: inference_time_ms }
}

// Kept as a SDD §2 escape hatch for demos without a GPU backend.
// Returns a Promise<string> resolving to the final transcript when recognition ends.
export function startWebSpeechSession() {
  const SR = window.SpeechRecognition ?? window.webkitSpeechRecognition
  if (!SR) {
    return Promise.reject(new Error('Web Speech API not supported in this browser'))
  }
  const recognition = new SR()
  recognition.continuous = false
  recognition.interimResults = false
  recognition.lang = 'en-US'

  return new Promise((resolve, reject) => {
    recognition.onresult = (e) => resolve(e.results[0][0].transcript)
    recognition.onerror = (e) => reject(new Error(e.error || 'speech recognition error'))
    recognition.onend = () => {} // resolved via onresult
    recognition.start()
  })
}
