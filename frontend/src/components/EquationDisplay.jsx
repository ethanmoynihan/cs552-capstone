import { MathJax } from 'better-react-mathjax'

export function EquationDisplay({ latex }) {
  if (!latex) return null
  return (
    <div className="equation-display">
      <div className="rendered">
        <MathJax dynamic>{`\\[${latex}\\]`}</MathJax>
      </div>
      <pre className="latex-source">{latex}</pre>
    </div>
  )
}
