"""Application configuration using pydantic-settings."""

from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    PROJECT_NAME: str = "Archon FastAPI"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "AI-Native Distributed System Design Interview & Evaluation Platform"
    API_V1_PREFIX: str = "/api/v1"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # Database
    DATABASE_URL: str = Field(
        default="sqlite+aiosqlite:///./archon.db",
        description="Async database connection URL"
    )
    SYNC_DATABASE_URL: str = Field(
        default="sqlite:///./archon.db",
        description="Sync database connection URL for migrations and tools"
    )

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Security
    JWT_SECRET: str = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS
    FRONTEND_URLS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8080",
    ]

    # Kafka
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    KAFKA_TOPIC_INTERVIEW_EVENTS: str = "interview.events"
    KAFKA_TOPIC_AI_RESPONSES: str = "ai.responses"
    KAFKA_TOPIC_EVALUATIONS: str = "ai.evaluations"
    KAFKA_TOPIC_DLQ: str = "ai.dlq"
    ENABLE_CDC: bool = False

    # Qdrant Vector DB
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    QDRANT_COLLECTION: str = "archon_knowledge_base"

    # LLM Providers & Keys
    LLM_PROVIDER: str = "gemini"  # gemini, groq, or nvidia
    GEMINI_API_KEYS: List[str] = []
    GROQ_API_KEYS: List[str] = []
    NVIDIA_API_KEYS: List[str] = []

    # Temporal
    TEMPORAL_HOST: str = "localhost:7233"
    TEMPORAL_NAMESPACE: str = "default"
    TEMPORAL_TASK_QUEUE: str = "system-design-evaluation"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="allow",
    )


settings = Settings()
