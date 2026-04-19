import { useEffect, useMemo, useState } from 'react'
import { listTestCases, runTestCase } from '../services/api'

export function EvaluationPanel() {
  const [open, setOpen] = useState(false)
  const [cases, setCases] = useState([])
  const [results, setResults] = useState({}) // id -> RunCaseResponse
  const [running, setRunning] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (!open || cases.length > 0) return
    listTestCases()
      .then((d) => setCases(d.cases))
      .catch((err) => setError(err.message))
  }, [open, cases.length])

  async function runAll() {
    setRunning(true)
    setError(null)
    setResults({})
    for (const c of cases) {
      try {
        const r = await runTestCase(c.id)
        setResults((prev) => ({ ...prev, [c.id]: r }))
      } catch (err) {
        setError(err.message)
        break
      }
    }
    setRunning(false)
  }

  const summary = useMemo(() => buildSummary(Object.values(results)), [results])
  const completed = Object.keys(results).length

  return (
    <section className="evaluation-panel">
      <button
        type="button"
        className="evaluation-toggle"
        onClick={() => setOpen((v) => !v)}
      >
        {open ? '▾' : '▸'} Evaluation ({cases.length || '…'} test cases)
      </button>
      {open && (
        <div className="evaluation-body">
          <div className="evaluation-controls">
            <button type="button" onClick={runAll} disabled={running || cases.length === 0}>
              {running ? `Running ${completed}/${cases.length}…` : 'Run evaluation'}
            </button>
            {completed > 0 && (
              <span className="evaluation-progress">
                {completed}/{cases.length} complete
              </span>
            )}
          </div>
          {error && <div className="error">{error}</div>}
          {summary && <SummaryTiles s={summary} />}
          {cases.length > 0 && <ResultsTable cases={cases} results={results} />}
        </div>
      )}
    </section>
  )
}

function SummaryTiles({ s }) {
  const mathStr =
    s.mathEquivalentChecked > 0
      ? `${(s.mathEquivalentRate * 100).toFixed(0)}% (${s.mathEquivalentChecked} checked)`
      : 'n/a'
  return (
    <div className="summary-tiles">
      <Tile label="n" value={s.n} />
      <Tile label="exact match" value={`${(s.exactMatchRate * 100).toFixed(0)}%`} />
      <Tile label="math equivalent" value={mathStr} />
      <Tile label="parses ok" value={`${(s.parsesOkRate * 100).toFixed(0)}%`} />
      <Tile label="mean BLEU" value={s.meanBleu.toFixed(1)} />
      <Tile label="mean ROUGE-L" value={s.meanRougeL.toFixed(2)} />
      <Tile label="median ms" value={s.medianMs} />
    </div>
  )
}

function Tile({ label, value }) {
  return (
    <div className="tile">
      <div className="tile-value">{value}</div>
      <div className="tile-label">{label}</div>
    </div>
  )
}

function ResultsTable({ cases, results }) {
  return (
    <div className="results-table-wrapper">
      <table className="results-table">
        <thead>
          <tr>
            <th>id</th>
            <th>cat</th>
            <th>exact</th>
            <th>math</th>
            <th>parses</th>
            <th>BLEU</th>
            <th>ROUGE</th>
            <th>ms</th>
            <th>expected</th>
            <th>actual</th>
          </tr>
        </thead>
        <tbody>
          {cases.map((c) => {
            const r = results[c.id]
            const m = r?.metrics
            return (
              <tr key={c.id} className={r ? '' : 'pending'}>
                <td>{c.id}</td>
                <td>{c.category}</td>
                <td>{cell(m?.exact_match)}</td>
                <td>{cell(m?.math_equivalent)}</td>
                <td>{cell(m?.parses_ok)}</td>
                <td>{m ? m.bleu.toFixed(1) : ''}</td>
                <td>{m ? m.rouge_l.toFixed(2) : ''}</td>
                <td>{r ? r.inference_ms : ''}</td>
                <td><code>{c.expected_latex}</code></td>
                <td><code>{r?.actual ?? ''}</code></td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}

function cell(v) {
  if (v === true) return <span className="pass">✓</span>
  if (v === false) return <span className="fail">✗</span>
  return <span className="unchecked">—</span>
}

function buildSummary(runs) {
  if (runs.length === 0) return null
  const n = runs.length
  const exact = runs.filter((r) => r.metrics.exact_match).length
  const parses = runs.filter((r) => r.metrics.parses_ok).length
  const mathTrue = runs.filter((r) => r.metrics.math_equivalent === true).length
  const mathChecked = runs.filter((r) => r.metrics.math_equivalent !== null).length
  const mean = (xs) => (xs.length ? xs.reduce((a, b) => a + b, 0) / xs.length : 0)
  const median = (xs) => {
    if (!xs.length) return 0
    const sorted = [...xs].sort((a, b) => a - b)
    const mid = Math.floor(sorted.length / 2)
    return sorted.length % 2 ? sorted[mid] : (sorted[mid - 1] + sorted[mid]) / 2
  }
  return {
    n,
    exactMatchRate: exact / n,
    parsesOkRate: parses / n,
    mathEquivalentRate: mathChecked ? mathTrue / mathChecked : 0,
    mathEquivalentChecked: mathChecked,
    meanBleu: mean(runs.map((r) => r.metrics.bleu)),
    meanRougeL: mean(runs.map((r) => r.metrics.rouge_l)),
    medianMs: Math.round(median(runs.map((r) => r.inference_ms))),
  }
}
