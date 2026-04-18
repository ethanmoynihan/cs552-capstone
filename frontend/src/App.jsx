import { useState } from 'react'
import { MathJaxContext } from 'better-react-mathjax'
import { generateLatex } from './services/api'
import { EquationDisplay } from './components/EquationDisplay'
import { VoiceInput } from './components/VoiceInput'
import { TranscriptPane } from './components/TranscriptPane'
import { EditCommand } from './components/EditCommand'
import './App.css'

const mathJaxConfig = {
  loader: { load: ['[tex]/ams'] },
  tex: { packages: { '[+]': ['ams'] } },
}

function App() {
  const [transcript, setTranscript] = useState('')
  const [latex, setLatex] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  async function handleSubmit() {
    setLoading(true)
    setError(null)
    try {
      const res = await generateLatex(transcript)
      setLatex(res.latex)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <MathJaxContext version={3} config={mathJaxConfig}>
      <div className="app">
        <header>
          <h1>Voice-Driven LaTeX (Phase 3)</h1>
          <p>Speak or type an equation &rarr; edit with follow-up commands.</p>
        </header>
        <VoiceInput onTranscript={setTranscript} disabled={loading} />
        <TranscriptPane
          value={transcript}
          onChange={setTranscript}
          onSubmit={handleSubmit}
          loading={loading}
        />
        {error && <div className="error">{error}</div>}
        <EquationDisplay latex={latex} />
        {latex && <EditCommand currentLatex={latex} onEdit={setLatex} />}
      </div>
    </MathJaxContext>
  )
}

export default App
