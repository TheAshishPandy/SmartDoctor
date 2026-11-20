"""Environment-backed application settings."""
from functools import lru_cache
from pydantic import model_validator
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
    auth_jwt_secret: str = ""
    auth_access_minutes: int = 15
    auth_refresh_days: int = 30
    auth_otp_minutes: int = 10
    auth_otp_max_attempts: int = 5
    auth_otp_resend_seconds: int = 60
    auth_dev_otp_enabled: bool = True
    auth_admin_emails: str = ""
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from_email: str = ""
    smtp_use_tls: bool = True
    llm_base_url: str = ""
    llm_api_key: str = "local-dev"
    llm_model: str = "qwen2.5:3b"
    oidc_issuer: str = ""
    oidc_audience: str = ""
    oidc_jwks_url: str = ""
    oidc_roles_claim: str = "roles"
    oidc_organization_claim: str = "organization_id"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore", case_sensitive=False)

    @model_validator(mode="after")
    def validate_production_auth(self):
        if self.app_env == "production":
            if len(self.auth_jwt_secret) < 32 or "replace-with" in self.auth_jwt_secret.lower() or "local-auth" in self.auth_jwt_secret.lower():
                raise ValueError("Production requires a unique AUTH_JWT_SECRET of at least 32 characters")
            if not self.smtp_host or not self.smtp_from_email:
                raise ValueError("Production requires SMTP_HOST and SMTP_FROM_EMAIL")
            if self.auth_dev_otp_enabled or self.dev_auth_enabled:
                raise ValueError("Development authentication and OTP exposure must be disabled in production")
        return self

    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
