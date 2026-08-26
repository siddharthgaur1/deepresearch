from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # App
    app_name: str = "DeepResearch"
    api_key: str = Field(default="dev-key", description="Static API key for REST auth")
    environment: str = "development"

    # Database
    database_url: str = "postgresql+asyncpg://deepresearch:deepresearch@localhost:5432/deepresearch"
    database_url_sync: str = "postgresql+psycopg://deepresearch:deepresearch@localhost:5432/deepresearch"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # RabbitMQ / Celery
    celery_broker_url: str = "amqp://guest:guest@localhost:5672//"
    celery_result_backend: str = "redis://localhost:6379/1"

    # LLM providers (via LiteLLM). Free/local by default: Ollama needs no API key.
    # Set openai_api_key / anthropic_api_key / gemini_api_key + llm_model to opt into a paid provider.
    llm_model: str = "ollama/llama3.1"
    llm_max_tokens: int = 1024
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    gemini_api_key: str | None = None
    ollama_base_url: str = "http://localhost:11434"

    # Search. DuckDuckGo is free/no-key and is the default; Tavily/SerpAPI are optional paid fallbacks.
    search_provider: str = "duckduckgo"
    tavily_api_key: str | None = None
    serpapi_api_key: str | None = None

    # Embeddings. Local nomic-embed-text via Ollama by default (free); set embedding_model to an
    # OpenAI model + openai_api_key to opt into the paid embedding API.
    embedding_model: str = "ollama/nomic-embed-text"
    embedding_dims: int = 768

    # Research graph behavior
    max_retry_depth: int = 3
    max_sub_questions: int = 8
    fact_check_min_sources: int = 2

    # Rate limiting
    rate_limit_per_minute: int = 30

    # Observability
    prometheus_multiproc_dir: str | None = None


@lru_cache
def get_settings() -> Settings:
    return Settings()
