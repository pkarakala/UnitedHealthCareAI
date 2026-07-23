from pydantic import model_validator
from pydantic_settings import BaseSettings
from typing import Optional

INSECURE_DEFAULTS = {
    "secret_key": "change-me-in-production",
    "encryption_key": "change-me-32-byte-key-for-aes256",
}


class Settings(BaseSettings):
    app_name: str = "Prior Authorization AI Platform"
    app_env: str = "development"
    debug: bool = True
    log_level: str = "INFO"

    # Database
    database_url: str = "postgresql+asyncpg://pa_user:pa_pass@localhost:5432/prior_auth"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Security
    secret_key: str = "change-me-in-production"
    encryption_key: str = "change-me-32-byte-key-for-aes256"
    access_token_expire_minutes: int = 60
    algorithm: str = "HS256"

    # Anthropic
    anthropic_api_key: str = ""
    default_model: str = "claude-haiku-4-5-20251001"
    max_tokens: int = 2048

    # Simulation
    # Set to False in production once real payer/EHR integrations exist.
    # When False, agents that simulate external calls will raise instead of writing
    # fabricated data to the database.
    simulation_mode: bool = True

    # CORS
    cors_origins: str = "http://localhost:3000,https://usahealthcare.ai"

    # Langfuse
    langfuse_public_key: Optional[str] = None
    langfuse_secret_key: Optional[str] = None
    langfuse_host: str = "http://localhost:3001"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",")]

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() in ("production", "prod")

    @model_validator(mode="after")
    def _refuse_insecure_production(self) -> "Settings":
        if not self.is_production:
            return self
        problems = []
        if self.secret_key == INSECURE_DEFAULTS["secret_key"]:
            problems.append("SECRET_KEY is the insecure default")
        if self.encryption_key == INSECURE_DEFAULTS["encryption_key"]:
            problems.append("ENCRYPTION_KEY is the insecure default")
        if self.debug:
            problems.append("DEBUG must be false in production")
        if "pa_user:pa_pass@" in self.database_url:
            problems.append("DATABASE_URL uses default dev credentials")
        if problems:
            raise ValueError(
                "Refusing to start in production with insecure settings: "
                + "; ".join(problems)
            )
        return self

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
