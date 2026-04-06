# Software Design Document: Voice-Driven Mathematical Equation Editor

**Project:** CS 552 Capstone — Voice-Driven Mathematical Equation Editor Using an LLM
**Author:** Ethan Moynihan
**Status:** Draft — Iterating

---

## 1. Overview

This document describes the software design for a web application that converts spoken mathematical expressions into rendered LaTeX equations. The system uses Whisper for speech-to-text, LLaMA 3 8B for natural language to LaTeX conversion, and a React frontend for rendering and interaction.

---

## 2. Speech Recognition: Approach Comparison

The core focus of this project is the LLM-driven LaTeX generation, not the speech-to-text pipeline itself. The ASR component is an input mechanism. That said, the choice affects architecture complexity and user experience.

### Option A: Browser Web Speech API

- **Pros:** Zero backend work, no model hosting, instant integration, works offline in Chrome
- **Cons:** Accuracy varies by browser/OS, no control over the model, limited language/accent support, not available in all browsers (Firefox support is spotty)
- **Verdict:** Fastest path to a working demo. Frees up all effort for the LLM side.

### Option B: Server-Side Whisper

- **Pros:** High accuracy, full control over model size and configuration, consistent behavior across browsers, demonstrates end-to-end ML pipeline
- **Cons:** Requires sending audio to the backend (latency + bandwidth), need to host Whisper alongside or separately from LLaMA, adds infrastructure complexity
- **Verdict:** Best accuracy and most impressive for a capstone, but adds hosting burden.

### Option C: Client-Side Whisper (WASM)

- **Pros:** Runs in browser, no server round-trip for ASR, good accuracy
- **Cons:** Large model download on first load (~40-150MB), slower than native Whisper, browser memory pressure, still experimental
- **Verdict:** Interesting technically but risky for reliability and adds frontend complexity that isn't the project's focus.

### Decision

**Option B (Server-Side Whisper)** is the primary design. It pairs well with the FastAPI backend already needed for LLM inference and demonstrates a complete ML pipeline.

The ASR module will be designed behind a common interface so the frontend always works the same way regardless of which provider is active. The frontend's `VoiceInput` component will accept a transcript string — it does not care where that string came from.

### Development Strategy: Web Speech API as Scaffolding

During early development (Phases 1-2), the **Web Speech API (Option A)** will be used as a lightweight stand-in for Whisper. This allows the frontend, LLM pipeline, and UI to be built and tested end-to-end without needing a GPU or the Whisper backend running.

The swap is clean because the integration point is a single function:

```
// services/speechProvider.js

// Development: uses browser-native Web Speech API (no backend needed)
export function transcribeWithWebSpeech() → Promise<string>

// Production: sends audio to /transcribe endpoint (Whisper)
export function transcribeWithWhisper(audioBlob) → Promise<string>
```

The active provider is selected by environment config. Once the Whisper `/transcribe` endpoint is built in Phase 2, the switch is a one-line config change. The Web Speech API provider remains available as a fallback for demos on machines without GPU access.

---

## 3. System Architecture

```
┌─────────────────────────────────────────────────────┐
│                    Frontend (React + Vite)           │
│                                                     │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────┐ │
│  │ Voice Input  │  │ Transcript   │  │ Equation   │ │
│  │ Controls     │  │ Display &    │  │ Display    │ │
│  │ (Record/Stop)│  │ Text Edit    │  │ (MathJax)  │ │
│  └──────┬───────┘  └──────┬───────┘  └─────▲──────┘ │
│         │                 │                │        │
│         │ audio blob      │ text           │ LaTeX  │
│         ▼                 ▼                │        │
│  ┌─────────────────────────────────────────┘        │
│  │            API Client Layer                      │
│  └──────────────────┬──────────────────────         │
│                     │ HTTP POST                     │
└─────────────────────┼───────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────┐
│                 Backend (FastAPI + Python)           │
│                                                     │
│  ┌──────────────┐       ┌─────────────────────────┐ │
│  │ /transcribe  │       │ /generate-latex         │ │
│  │              │       │                         │ │
│  │ Audio ──►    │       │ Text ──►                │ │
│  │ Whisper ──►  │       │ LLaMA 3 8B ──►         │ │
│  │ Transcript   │       │ LaTeX string            │ │
│  └──────────────┘       └─────────────────────────┘ │
│                                                     │
│  ┌─────────────────────────────────────────────────┐ │
│  │ /edit-equation                                  │ │
│  │ (existing LaTeX + edit command) ──► LLaMA ──►   │ │
│  │ modified LaTeX                                  │ │
│  └─────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────┘
```

### Data Flow: Happy Path

1. User clicks record, speaks an equation
2. Frontend captures audio blob via MediaRecorder API
3. Audio is POST'd to `/transcribe` endpoint
4. Whisper processes audio, returns transcript text
5. Transcript is displayed to user (editable — user can fix ASR errors before submitting)
6. User confirms or edits transcript, then submits
7. Text is POST'd to `/generate-latex` endpoint
8. LLaMA 3 8B generates LaTeX string
9. Full LaTeX response is returned to frontend
10. MathJax renders the equation
11. Raw LaTeX is displayed in an editable code pane

---

## 4. Frontend Design

### Tech Stack

- **React 18** with functional components and hooks
- **Vite** for build tooling
- **MathJax 3** for LaTeX rendering
- **MediaRecorder API** for audio capture

### Component Structure

```
App
├── Header
├── VoiceInput
│   ├── RecordButton (start/stop toggle)
│   └── RecordingIndicator
├── TranscriptPane
│   ├── TranscriptDisplay (editable text area)
│   └── SubmitButton
├── EquationDisplay
│   ├── RenderedEquation (MathJax output)
│   └── LatexSource (editable code block)
├── EquationHistory (session only, optional)
│   └── HistoryItem[] (clickable to reload)
├── ExportControls
│   └── CopyLatexButton
└── ErrorDisplay
```

### Key UI Behaviors

- **Record toggle:** Single button toggles recording on/off. Visual indicator (pulsing dot or similar) when recording.
- **Transcript editing:** After ASR returns text, user sees it in an editable text area. This is the correction step before LLM processing.
- **Equation rendering:** MathJax renders the full LaTeX string once the complete response arrives from the backend.
- **LaTeX source pane:** Always visible below the rendered equation. User can manually tweak LaTeX and re-render.
- **Copy/Export:** Button to copy raw LaTeX to clipboard.

---

## 5. Backend Design

### Tech Stack

- **Python 3.11+**
- **FastAPI** for the REST API
- **Whisper** (OpenAI open-source) for ASR
- **LLaMA 3 8B** via Hugging Face Transformers + PyTorch
- **Uvicorn** as the ASGI server

### API Endpoints

#### `POST /transcribe`

Accepts audio, returns transcript.

```
Request:
  Content-Type: multipart/form-data
  Body: audio file (webm/opus from MediaRecorder)

Response (200):
  {
    "transcript": "x squared plus 2x minus 5 equals 0"
  }

Response (422):
  {
    "error": "Audio file could not be processed"
  }
```

#### `POST /generate-latex`

Accepts natural language text, returns LaTeX.

```
Request:
  Content-Type: application/json
  {
    "text": "x squared plus 2x minus 5 equals 0"
  }

Response (200):
  {
    "latex": "x^{2} + 2x - 5 = 0",
    "tokens_used": 24,
    "inference_time_ms": 850
  }
```

#### `POST /edit-equation`

Accepts existing LaTeX + a natural language edit command, returns modified LaTeX.

```
Request:
  Content-Type: application/json
  {
    "current_latex": "x^{2} + 2x - 5 = 0",
    "edit_command": "replace the minus 5 with plus 7"
  }

Response (200):
  {
    "latex": "x^{2} + 2x + 7 = 0",
    "tokens_used": 30,
    "inference_time_ms": 920
  }
```

### LLM Prompt Design

The LLaMA model will be prompted with a system prompt constraining it to LaTeX-only output. Draft prompt:

```
System: You are a LaTeX equation generator. Given a natural language
description of a mathematical expression, output ONLY the LaTeX math
code. Do not include any explanation, markdown, or surrounding text.
Do not include dollar signs or \begin{equation} wrappers. Output only
the raw LaTeX math expression.

User: the integral from 0 to infinity of e to the negative x squared dx

Expected output: \int_{0}^{\infty} e^{-x^{2}} \, dx
```

For the edit endpoint, the prompt will include the current LaTeX as context:

```
System: You are a LaTeX equation editor. You will be given an existing
LaTeX expression and a natural language edit instruction. Output ONLY
the modified LaTeX math code. Do not include explanation or surrounding text.

Current LaTeX: x^{2} + 2x - 5 = 0
Edit instruction: replace the minus 5 with plus 7

Expected output: x^{2} + 2x + 7 = 0
```

### Model Loading and Inference

- Model loaded once at application startup into GPU memory
- Tokenizer and model kept as module-level singletons
- Inference uses `model.generate()` with constrained parameters:
  - `max_new_tokens`: 256 (sufficient for even complex equations)
  - `temperature`: 0.1 (low creativity — we want deterministic LaTeX)
  - `do_sample`: False (greedy decoding for consistency)

### Whisper Configuration

- Model: `whisper-small` or `whisper-medium` (balance of speed vs accuracy)
- Loaded once at startup alongside LLaMA
- Audio preprocessing handled by Whisper's built-in pipeline

---

## 6. Communication: Request/Response vs Streaming vs WebSockets

### Why Request/Response (for now)

The proposal identified token streaming as a potential source of rendering bugs — partial LaTeX strings like `\frac{x^{2` will cause MathJax to error. The options:

| Approach | Pros | Cons |
|----------|------|------|
| **Simple request/response** | Simplest implementation, no partial render issues, MathJax always gets valid LaTeX | User waits for full generation before seeing anything |
| **SSE streaming** | User sees tokens appearing in real-time, feels responsive | Partial LaTeX breaks MathJax, need error-tolerant rendering or a separate "raw tokens" display |
| **WebSockets** | Bidirectional, could support interrupt/cancel mid-generation | Most complex, overkill for this use case |

**Decision: Start with simple request/response.** The LLaMA 8B generation for a single equation should complete in 1-3 seconds. The user already has a natural wait point (reviewing/editing the transcript), so the perceived latency is acceptable. A loading spinner during generation is sufficient feedback.

---

## 7. Hosting and Deployment

### Development Environment

- **Backend:** Run locally with `uvicorn` — LLaMA 3 8B and Whisper loaded on local GPU (M4 chip)
- **Frontend:** Vite dev server with proxy to local backend
- **Requirements:** Machine with 16-24GB VRAM GPU for local LLaMA inference

### Production Deployment

- **Backend + Models:** Hugging Face Inference Endpoints (dedicated GPU instance running the FastAPI app with both Whisper and LLaMA)
- **Frontend:** Netlify (static site hosting, free tier sufficient)
- **CORS:** Backend configured to accept requests from the Netlify frontend domain

### Environment Configuration

```
# .env (development)
BACKEND_URL=http://localhost:8000
WHISPER_MODEL=small
LLAMA_MODEL=meta-llama/Meta-Llama-3-8B-Instruct

# .env.production
BACKEND_URL=https://<hf-endpoint-url>
WHISPER_MODEL=small
LLAMA_MODEL=meta-llama/Meta-Llama-3-8B-Instruct
```

---

## 8. Project Structure

```
cs552-capstone/
├── PROPOSAL.md
├── SDD.md
├── README.md
├── frontend/
│   ├── package.json
│   ├── vite.config.js
│   ├── index.html
│   ├── public/
│   └── src/
│       ├── main.jsx
│       ├── App.jsx
│       ├── components/
│       │   ├── VoiceInput.jsx
│       │   ├── TranscriptPane.jsx
│       │   ├── EquationDisplay.jsx
│       │   ├── LatexSource.jsx
│       │   ├── EquationHistory.jsx
│       │   └── ExportControls.jsx
│       ├── hooks/
│       │   ├── useAudioRecorder.js
│       │   └── useEquationHistory.js
│       ├── services/
│       │   └── api.js
│       └── styles/
│           └── App.css
├── backend/
│   ├── requirements.txt
│   ├── main.py
│   ├── routers/
│   │   ├── transcribe.py
│   │   └── generate.py
│   ├── services/
│   │   ├── whisper_service.py
│   │   └── llama_service.py
│   ├── prompts/
│   │   ├── generate.txt
│   │   └── edit.txt
│   └── config.py
└── evaluation/
    ├── test_cases.json
    ├── evaluate_accuracy.py
    └── evaluate_latency.py
```

---

## 9. Implementation Phases

### Phase 1: Core Pipeline (Priority — build this first)

**Goal:** Text in, LaTeX out, rendered on screen. 
**Reasoning** Makes sure that the model works independent of the speech to text.

1. Set up FastAPI backend with `/generate-latex` endpoint
2. Load LLaMA 3 8B locally, wire up inference with the system prompt
3. Set up React + Vite frontend with a simple text input
4. Connect frontend to backend — type a math description, see rendered LaTeX
5. Add MathJax rendering + raw LaTeX display pane


### Phase 2: Voice Input

**Goal:** Speak an equation, see it rendered. 
**Reasoning** Speech to text added allowing for actual goal of this project.
1. Add `/transcribe` endpoint with Whisper
2. Add MediaRecorder audio capture in the frontend
3. Wire VoiceInput -> /transcribe -> TranscriptPane -> /generate-latex -> EquationDisplay
4. Add transcript editing step between ASR and LLM

### Phase 3: Editing and Polish

**Goal:** Users can refine equations with voice or text commands.
**Reasoning** Adds final functionality independant of other setup.
1. Add `/edit-equation` endpoint
2. Add edit command input (text-based first)
3. Wire voice commands through the same ASR -> edit pipeline
4. Add copy-to-clipboard / export functionality
5. Add equation session history (in-memory, lost on refresh)

### Phase 4: Evaluation

**Goal:** Collect the metrics defined in the proposal.
**Reasoning** Need to evaluate the end to end project, this can be done mostly locally as the model will be properly running.
1. Build test case set (natural language -> expected LaTeX pairs)
2. Script accuracy evaluation (edit distance, exact match, render success)
3. Measure and log latency (ASR time, LLM inference time, total round-trip)
4. Measure resource usage (GPU memory, utilization)
5. Test with ambiguous phrasing and complex equations

### Phase 5: Deployment

**Goal:** Live, publicly accessible demo.
**Reasoning** Final goal of the project. This will cost money so saving it to the end and the actual project submission is the best method.

1. Deploy backend to Hugging Face Inference Endpoints
2. Deploy frontend to Netlify
3. Configure CORS and environment variables
4. End-to-end smoke test on production

---

## 10. Future Considerations (Out of Scope for Initial Build)

These are interesting extensions that should not be attempted until Phases 1-5 are complete:

- **Complex voice editing commands:** Semantic edits like "move the exponent to the denominator" or "wrap that in a square root" — these require the LLM to understand LaTeX structure, not just text substitution. The `/edit-equation` endpoint is already designed to support this (the LLM receives the full LaTeX + instruction), but the prompt engineering and testing would need significant work. Scoped out for the initial build but could be added if theres time.
- **Multi-equation documents:** Supporting a full document with multiple equations, text between them, and structural commands. Not within the original proposal.
- **Persistent equation history:** Saving equations across sessions (would need a database or local storage). Not useful for the actual testing. 
- **Collaborative editing:** Multiple users working on equations simultaneously. Overkill for this assignment.
- **Alternative LLM backends:** Supporting different models or API-based LLMs (OpenAI, Anthropic) as alternatives to local LLaMA, not needed for the project and will add extra complications.