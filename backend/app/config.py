"""Environment-backed application settings."""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "SmartDoctor API"
    app_env: str = "development"
    app_version: str = "0.3.0"
    cors_origins: str = "http://localhost:3000"
    database_url: str = "postgresql+psycopg://smartdoctor:smartdoctor_dev_only@localhost:5432/smartdoctor"
    redis_url: str = "redis://localhost:6379/0"
    mongodb_url: str = "mongodb://smartdoctor:smartdoctor_dev_only@localhost:27017/?authSource=admin"
    mongodb_database: str = "smartdoctor"
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str = ""
    qdrant_collection: str = "patient_records"
    embedding_dimensions: int = 384
    embedding_model: str = "BAAI/bge-small-en-v1.5"
    upload_directory: str = "/data/uploads"
    max_upload_mb: int = 20
    dev_auth_enabled: bool = False
    llm_base_url: str = ""
    llm_api_key: str = "local-dev"
    llm_model: str = "qwen2.5:3b"
    oidc_issuer: str = ""
    oidc_audience: str = ""
    oidc_jwks_url: str = ""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore", case_sensitive=False
    )

    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
