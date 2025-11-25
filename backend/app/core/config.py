"""Application configuration using pydantic-settings"""

from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Application
    app_version: str = "0.1.0"
    app_name: str = "AI Autonomous Platform"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    log_level: str = "INFO"

    # LLM Configuration
    openai_api_key: str = ""
    llm_provider: str = "openai"
    llm_model: str = "gpt-4"
    embedding_model: str = "text-embedding-3-small"

    # Database
    database_url: str = "postgresql+asyncpg://user:password@localhost:5432/ai_platform"
    vector_db_type: str = "pgvector"
    chroma_persist_directory: str = "./data/chroma"

    # Notion Integration
    notion_api_key: str = ""
    notion_database_id: str = ""

    # Security
    secret_key: str = "change-me-in-production"
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:8000"]

    # Voice
    whisper_model: str = "base"
    tts_provider: str = "openai"
    tts_voice: str = "alloy"

    # Rate Limiting
    rate_limit_requests: int = 100
    rate_limit_period: int = 60

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


# Global settings instance
settings = Settings()
