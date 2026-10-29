"""Cấu hình ứng dụng, đọc từ biến môi trường / file .env."""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # App
    APP_NAME: str = "Student Connect API"
    ENV: str = "development"  # development | staging | production
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"

    # Database
    DATABASE_URL: str = "mysql+pymysql://app:app@localhost:3306/student_connect?charset=utf8mb4"

    # JWT
    SECRET_KEY: str = "dev-only-secret-key-change-me-in-production-0123456789"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    RESET_TOKEN_EXPIRE_MINUTES: int = 30

    # CORS / Frontend
    CORS_ORIGINS: list[str] = ["http://localhost:5173"]
    FRONTEND_URL: str = "http://localhost:5173"

    # Upload
    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_MB: int = 10

    # Email (SMTP). Để trống SMTP_HOST ở dev => chỉ ghi log
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "no-reply@student-connect.local"

    # AI / NLP
    AI_PROVIDER: str = "gemini"  # gemini | openai | anthropic
    AI_API_KEY: str = ""
    AI_MODEL: str = ""

    @property
    def is_development(self) -> bool:
        return self.ENV == "development"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
