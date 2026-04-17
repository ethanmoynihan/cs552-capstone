from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    llama_model: str = "meta-llama/Meta-Llama-3-8B-Instruct"
    whisper_model: str = "small"
    use_stub_llama: bool = True
    cors_origins: list[str] = ["http://localhost:5173"]


settings = Settings()
