import { useState } from 'react'
import { MathJax } from 'better-react-mathjax'

export function EquationDisplay({ latex }) {
  const [copied, setCopied] = useState(false)

  if (!latex) return null

  async function copy() {
    try {
      await navigator.clipboard.writeText(latex)
      setCopied(true)
      setTimeout(() => setCopied(false), 1500)
    } catch {
      setCopied(false)
    }
  }

  return (
    <div className="equation-display">
      <div className="rendered">
        <MathJax dynamic>{`\\[${latex}\\]`}</MathJax>
      </div>
      <div className="latex-row">
        <pre className="latex-source">{latex}</pre>
        <button type="button" onClick={copy} className="copy-button">
          {copied ? 'Copied!' : 'Copy LaTeX'}
        </button>
      </div>
    </div>
  )
}
