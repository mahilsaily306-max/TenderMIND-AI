import json

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql+asyncpg://tenderpilot:tenderpilot@localhost:5432/tenderpilot"
    database_url_sync: str = "postgresql://tenderpilot:tenderpilot@localhost:5432/tenderpilot"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Auth
    secret_key: str = "dev-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 7
    encryption_key: str = "dev-encryption-key-change-in-production"

    # AI
    ai_provider: str = "openai"
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    ollama_base_url: str | None = "http://localhost:11434"
    ollama_model: str = "llama3"
    embedding_model: str = "text-embedding-3-small"
    llm_model: str = "gpt-4o"

    # Bid Readiness Weights (JSON string in env)
    bid_readiness_weights: str = json.dumps(
        {
            "compliance": 0.30,
            "experience": 0.25,
            "capacity": 0.20,
            "risk": 0.15,
            "past_performance": 0.10,
        }
    )

    # Storage
    storage_backend: str = "local"
    storage_path: str = "./storage"

    # App
    environment: str = "development"
    log_level: str = "DEBUG"
    cors_origins: str = "http://localhost:5173"
    app_name: str = "TenderPilot AI"

    @property
    def bid_readiness_weights_dict(self) -> dict:
        return json.loads(self.bid_readiness_weights)

    @property
    def cors_origins_list(self) -> list:
        return [o.strip() for o in self.cors_origins.split(",")]

    model_config = {"env_file": ".env", "case_sensitive": False}


settings = Settings()
