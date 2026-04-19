---
title: CS552 LaTeX Voice Backend
emoji: 🔢
colorFrom: indigo
colorTo: pink
sdk: docker
app_port: 7860
pinned: false
license: mit
---

# CS552 Voice-Driven LaTeX — Backend

FastAPI backend for the CS 552 capstone. Converts natural-language math into
rendered LaTeX via LLaMA 3 8B (with Whisper ASR upstream).

This README doubles as the Hugging Face Space metadata. The Space runs the
Dockerfile in this directory.

## Endpoints

- `POST /transcribe` — multipart audio → transcript
- `POST /generate-latex` — text → LaTeX
- `POST /edit-equation` — current LaTeX + instruction → revised LaTeX
- `GET /health` — stub-mode status

## Local dev

```bash
# From the repo root:
task install
task dev              # runs backend (:8000) + frontend (:5173)
```

See `../README.md` for full project context and `../SDD.md` for architecture.

## Hardware notes

- **CPU Basic** (default on Spaces) is only viable in stub mode — LLaMA 3 8B
  won't fit in memory, let alone serve requests in reasonable time.
- For real inference, upgrade the Space to a GPU instance and set
  `USE_STUB_LLAMA=false` / `USE_STUB_WHISPER=false` in Space secrets.
