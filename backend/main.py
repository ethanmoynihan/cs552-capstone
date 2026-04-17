from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from routers import generate

app = FastAPI(title="CS552 Capstone API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(generate.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "stub_llama": str(settings.use_stub_llama)}
