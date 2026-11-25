from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).resolve().parent.parent / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    GROQ_API_KEY: str
    LLM_MODEL: str = "llama-3.3-70b-versatile"
    QDRANT_URL: str
    QDRANT_API_KEY: str
    STORAGE_DIR: str = "../storage/repos"
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"

    @property
    def storage_path(self) -> Path:
        base = Path(__file__).resolve().parent.parent
        resolved = (base / self.STORAGE_DIR).resolve()
        resolved.mkdir(parents=True, exist_ok=True)
        return resolved


settings = Settings()