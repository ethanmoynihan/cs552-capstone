from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel

from services.whisper_service import get_transcriber

router = APIRouter()


class TranscribeResponse(BaseModel):
    transcript: str
    inference_time_ms: int


@router.post("/transcribe", response_model=TranscribeResponse)
async def transcribe(audio: UploadFile = File(...)) -> TranscribeResponse:
    audio_bytes = await audio.read()
    if not audio_bytes:
        raise HTTPException(status_code=422, detail="Audio file is empty")
    try:
        transcript, elapsed = get_transcriber().transcribe(audio_bytes, audio.filename or "audio.webm")
    except Exception as exc:  # Whisper surfaces decoder/ffmpeg errors as plain exceptions
        raise HTTPException(status_code=422, detail=f"Audio file could not be processed: {exc}") from exc
    return TranscribeResponse(transcript=transcript, inference_time_ms=elapsed)
