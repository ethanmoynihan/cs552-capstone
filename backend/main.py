from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from routers import generate, transcribe
from services.llama_service import warm_generator
from services.whisper_service import warm_transcriber


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Load the models (stub or real) before serving the first request.
    warm_generator()
    warm_transcriber()
    yield


app = FastAPI(title="CS552 Capstone API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(generate.router)
app.include_router(transcribe.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "stub_llama": str(settings.use_stub_llama),
        "stub_whisper": str(settings.use_stub_whisper),
    }
