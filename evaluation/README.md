# Phase 4 Evaluation

Measures what PROPOSAL.md §"Model Evaluation Criteria" calls for:

| Script | Criterion | Runs against |
|---|---|---|
| `evaluate_accuracy.py` | exact match, edit distance, math equivalence, render success | direct-import of backend generator (no server needed) |
| `evaluate_latency.py` | speech→render end-to-end, tokens/sec, RSS | direct-import; reads `audio_fixtures/` |
| `evaluate_concurrent.py` | scalability under parallel load | running FastAPI server on :8000 |

## Install

From repo root: `task install` (picks up eval deps automatically). Or from here: `task install`.

## Run

```bash
# Accuracy: text → LaTeX across 30 curated cases
task eval:accuracy

# Latency: add .webm/.wav/.mp3/.m4a files to audio_fixtures/ first
task eval:latency

# Concurrency: start the backend (task dev), then in another shell:
task eval:concurrent -- --concurrency 8 --total 32
```

Each run writes `results/<kind>-<timestamp>.{json,md}`. JSON for machine
consumption, markdown for inclusion in the final writeup.

## Metrics notes

- **Exact match**: whitespace-normalized string equality against the reference.
- **Edit distance**: Levenshtein, plus normalized (0.0 perfect → 1.0 totally different).
- **Parses ok**: pylatexenc walks the AST without raising. Proxy for MathJax render success.
- **Math equivalent**: sympy parses both sides and `simplify(a - b) == 0`. Returns **None** (not False) when sympy can't parse — matrices, integrals with bounds, matrix environments. Those cases surface for manual review, per PROPOSAL.md allowing "tracked by the tester".

## Why concurrency hits the server but accuracy doesn't

Accuracy/latency measure model quality — direct-import gives cleaner numbers.
Concurrency measures request-path behavior (FastAPI thread pool, Uvicorn),
which only manifests over HTTP.
