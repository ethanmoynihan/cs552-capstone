from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Stub vs real model. Flip to false once the GGUF is downloaded.
    use_stub_llama: bool = True

    # llama.cpp (GGUF) settings — default dev backend on Apple Silicon.
    llama_gguf_path: Path = BACKEND_DIR / "models" / "Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf"
    llama_n_ctx: int = 4096
    llama_n_gpu_layers: int = -1  # -1 = offload everything to Metal
    llama_max_new_tokens: int = 256
    llama_temperature: float = 0.1

    # Legacy/transformers name (used in Phase 5 deploy path).
    llama_model: str = "meta-llama/Meta-Llama-3.1-8B-Instruct"
    whisper_model: str = "small"

    cors_origins: list[str] = ["http://localhost:5173"]


settings = Settings()
