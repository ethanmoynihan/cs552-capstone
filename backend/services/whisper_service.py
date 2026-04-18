from __future__ import annotations

import tempfile
import time
from pathlib import Path
from typing import Protocol

from config import settings


class Transcriber(Protocol):
    def transcribe(self, audio_bytes: bytes, filename: str) -> tuple[str, int]: ...


class StubTranscriber:
    """Phase 2 stand-in. Returns a canned transcript so the voice pipeline works without Whisper."""

    def transcribe(self, audio_bytes: bytes, filename: str) -> tuple[str, int]:
        start = time.perf_counter()
        transcript = "x squared plus 2x minus 5 equals 0"
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        return transcript, elapsed_ms


class WhisperTranscriber:
    """Real ASR via openai-whisper against a local model."""

    def __init__(self) -> None:
        import whisper  # imported lazily so stub mode doesn't require the dep

        self._model = whisper.load_model(settings.whisper_model, device=settings.whisper_device)

    def transcribe(self, audio_bytes: bytes, filename: str) -> tuple[str, int]:
        start = time.perf_counter()
        suffix = Path(filename).suffix or ".webm"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=True) as tmp:
            tmp.write(audio_bytes)
            tmp.flush()
            result = self._model.transcribe(
                tmp.name,
                language=settings.whisper_language,
                fp16=False,
            )
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        return result["text"].strip(), elapsed_ms


_transcriber: Transcriber | None = None


def get_transcriber() -> Transcriber:
    global _transcriber
    if _transcriber is None:
        _transcriber = StubTranscriber() if settings.use_stub_whisper else WhisperTranscriber()
    return _transcriber


def warm_transcriber() -> None:
    """Call at app startup to pay the model-load cost up front."""
    get_transcriber()
