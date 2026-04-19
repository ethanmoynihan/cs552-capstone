from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Stub vs real model. Default false: Space boots straight into real inference.
    use_stub_llama: bool = False

    # llama.cpp (GGUF) settings — default dev backend on Apple Silicon.
    llama_gguf_path: Path = BACKEND_DIR / "models" / "Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf"
    llama_n_ctx: int = 4096
    llama_n_gpu_layers: int = -1  # -1 = offload everything to Metal on M-series; 0 on CPU Spaces
    llama_max_new_tokens: int = 256
    llama_temperature: float = 0.1

    # If the GGUF at llama_gguf_path is missing, download it from the HF Hub on first
    # startup. Standard pattern for HF Spaces — keeps the Docker image small and lets
    # the weights live in the Space's persistent cache after the first boot.
    hf_model_repo: str = "bartowski/Meta-Llama-3.1-8B-Instruct-GGUF"
    hf_model_file: str = "Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf"

    # Legacy/transformers name (used in Phase 5 deploy path).
    llama_model: str = "meta-llama/Meta-Llama-3.1-8B-Instruct"

    # Whisper (ASR) settings. Default false: real transcription on boot.
    use_stub_whisper: bool = False
    whisper_model: str = "small"
    whisper_device: str = "cpu"  # "cuda" on GPU host, "cpu" elsewhere; Whisper picks fp16 automatically
    whisper_language: str | None = "en"  # None = auto-detect

    cors_origins: list[str] = ["http://localhost:5173"]

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_comma_separated(cls, v: object) -> object:
        # Accept "https://a.com,https://b.com" as a convenience for Space secrets,
        # alongside the default JSON list form pydantic-settings supports.
        if isinstance(v, str) and not v.strip().startswith("["):
            return [s.strip() for s in v.split(",") if s.strip()]
        return v


settings = Settings()
