"""Application settings loaded from environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """JobPilot application settings."""

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}

    # Application
    app_env: str = "development"
    log_level: str = "INFO"
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # Database
    database_url: str = "postgresql+asyncpg://jobpilot:jobpilot_dev@localhost:5432/jobpilot"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Qdrant
    qdrant_url: str = "http://localhost:6333"

    # Temporal
    temporal_address: str = "localhost:7233"
    temporal_namespace: str = "default"
    temporal_task_queue: str = "jobpilot-tasks"

    # MinIO
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_bucket: str = "jobpilot-resumes"
    minio_secure: bool = False

    # LLM — supports OpenAI, Anthropic, or OpenRouter (via LiteLLM)
    # Set the provider you want to use. For OpenRouter, set OPENROUTER_API_KEY
    # and prefix models with "openrouter/" (e.g., "openrouter/google/gemini-2.5-flash")
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    openrouter_api_key: str = ""
    llm_primary_model: str = "openrouter/google/gemini-2.5-flash"
    llm_fast_model: str = "openrouter/google/gemini-2.5-flash"
    llm_fallback_model: str = "openrouter/anthropic/claude-sonnet-4"
    embedding_model: str = "openrouter/openai/text-embedding-3-small"

    # Third-party APIs
    serpapi_key: str = ""
    rapidapi_key: str = ""
    brightdata_username: str = ""
    brightdata_password: str = ""

    @property
    def is_dev(self) -> bool:
        return self.app_env == "development"


settings = Settings()
