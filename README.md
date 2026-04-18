# cs552-capstone

Capstone project for CS 552 at WPI authored by Ethan Moynihan

---

The initial proposal is written in the PROPOSAL.md file and is the same as the original proposal submitted. It outlines the project and it's intended behavior. 

The SDD.md is a software design doc for this project. I have found these very useful at work tracking what needs to be done and properly scoping projects. This goes into the specifics of what needs to be done and how it's getting done with actual technical details.

## Running Locally

The current scaffold wires the text-in → LaTeX-out pipeline with a stubbed LLM so the frontend can be built end-to-end before the 8B model is loaded.

**Prerequisites:** [uv](https://docs.astral.sh/uv/) (backend), [pnpm](https://pnpm.io/) (frontend), [go-task](https://taskfile.dev/) (runner).

### One-liner

```
task install   # uv sync + pnpm install
task dev       # backend on :8000, frontend on :5173, in parallel
task stop      # kills anything on :8000 / :5173
```

Open [http://localhost:5173](http://localhost:5173), type a math description, submit, and MathJax renders the stubbed LaTeX. The Vite dev server proxies `/api/*` → `http://localhost:8000`, so the browser only ever talks to Vite.

### Useful subcommands

Run `task --list` to see everything. Highlights:

- `task backend:dev` / `task frontend:dev` — run just one side
- `task backend:install:model` — install torch / transformers / whisper once the stub is ready to go
- `task frontend:build` — production build
- `task lint` — ruff on backend, ESLint on frontend

### Notes

- Backend env vars are loaded from `backend/.env` (see `.env.example`). `USE_STUB_LLAMA=true` keeps the stub generator active — flip to `false` once the real LLaMA implementation lands.
- `frontend/.npmrc` pins the public npm registry so scaffolding doesn't hit a work CodeArtifact token.

