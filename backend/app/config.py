"""NeuroNote AI - Configuration"""

from pydantic_settings import BaseSettings
from typing import List
import json


class Settings(BaseSettings):
    # Whisper
    whisper_model: str = "base"

    # Ollama
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3:latest"

    # Database
    database_url: str = "sqlite+aiosqlite:///./neuronote.db"

    # CORS
    cors_origins: str = '["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:8080", "http://127.0.0.1:8080"]'

    @property
    def cors_origins_list(self) -> List[str]:
        return json.loads(self.cors_origins)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
