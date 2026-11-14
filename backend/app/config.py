"""Environment-backed application settings."""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "SmartDoctor API"
    app_env: str = "development"
    app_version: str = "0.2.0"
    cors_origins: str = "http://localhost:3000"
    database_url: str = "postgresql+psycopg://smartdoctor:smartdoctor_dev_only@localhost:5432/smartdoctor"
    oidc_issuer: str = ""
    oidc_audience: str = ""
    oidc_jwks_url: str = ""
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore", case_sensitive=False)
    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

@lru_cache
def get_settings() -> Settings:
    return Settings()
