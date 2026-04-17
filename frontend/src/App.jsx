import { useState } from 'react'
import { MathJaxContext } from 'better-react-mathjax'
import { generateLatex } from './services/api'
import { EquationDisplay } from './components/EquationDisplay'
import './App.css'

const mathJaxConfig = {
  loader: { load: ['[tex]/ams'] },
  tex: { packages: { '[+]': ['ams'] } },
}

function App() {
  const [text, setText] = useState('')
  const [latex, setLatex] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  async function handleSubmit(e) {
    e.preventDefault()
    setLoading(true)
    setError(null)
    try {
      const res = await generateLatex(text)
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
          <h1>Voice-Driven LaTeX (Phase 1)</h1>
          <p>Text input &rarr; LLM (stub) &rarr; rendered equation.</p>
        </header>
        <form onSubmit={handleSubmit}>
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="e.g. x squared plus 2x minus 5 equals 0"
            rows={3}
          />
          <button type="submit" disabled={loading || !text.trim()}>
            {loading ? 'Generating\u2026' : 'Generate LaTeX'}
          </button>
        </form>
        {error && <div className="error">{error}</div>}
        <EquationDisplay latex={latex} />
      </div>
    </MathJaxContext>
  )
}

export default App
