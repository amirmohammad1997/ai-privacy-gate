"""
Application configuration.

Loads settings from environment variables and .env file.
"""
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings."""

    # ─── Application ───
    APP_NAME: str = "AI Privacy Gateway"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: str = Field(
        default="development",
        description="development | staging | production",
    )

    # ─── Server ───
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    LOG_LEVEL: str = "INFO"

    # ─── LLM ───
    LLM_PROVIDER: str = "openai"
    LLM_API_KEY: str = ""
    LLM_BASE_URL: str = "https://api.openai.com/v1"
    LLM_MODEL: str = "gpt-4o-mini"
    LLM_TIMEOUT: float = 60.0

    # ─── Security ───
    JWT_SECRET_KEY: str = ""
    SESSION_ENCRYPTION_KEY: str = ""

    # ─── Database (filled later) ───
    DATABASE_URL: str = ""
    REDIS_URL: str = ""

    # ─── CORS ───
    ALLOWED_ORIGINS: str = "*"

    # ─── Limits ───
    MAX_INPUT_LENGTH: int = 8000

    # ─── Computed Properties ───
    @property
    def origins(self) -> list[str]:
        """Parse ALLOWED_ORIGINS as a list."""
        if self.ALLOWED_ORIGINS == "*":
            return ["*"]
        return [x.strip() for x in self.ALLOWED_ORIGINS.split(",")]

    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT == "development"

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


# ─── Singleton ───
settings = Settings()