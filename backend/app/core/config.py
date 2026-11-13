"""Cấu hình ứng dụng, đọc từ biến môi trường / file .env."""

from functools import lru_cache

from pydantic import Field
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

    # Email: no SMTP means FAILED, never a simulated SENT.
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "no-reply@student-connect.local"
    SMTP_SSL: bool = False  # True for implicit TLS (usually port 465); otherwise STARTTLS.

    # Freelancer OTP: separate HMAC secret, never a source-code default.
    FREELANCER_OTP_SECRET: str = ""

    FREELANCER_FILE_SCAN_ENABLED: bool = False
    FREELANCER_SCAN_GATEWAY_URL: str = ""
    FREELANCER_SCAN_GATEWAY_TOKEN: str = ""
    FREELANCER_WORKER_LEASE_SECONDS: int = Field(default=120, ge=60, le=3600)
    FREELANCER_WORKER_MAX_ATTEMPTS: int = Field(default=12, ge=1, le=100)

    # Real-money services stay disabled until configured explicitly.
    FREELANCER_FINANCE_ENABLED: bool = False
    PAYOS_COLLECTION_ENABLED: bool = False
    PAYOS_PAYOUT_ENABLED: bool = False
    PAYOS_API_BASE_URL: str = "https://api-merchant.payos.vn"
    PAYOS_COLLECTION_CLIENT_ID: str = ""
    PAYOS_COLLECTION_API_KEY: str = ""
    PAYOS_COLLECTION_CHECKSUM_KEY: str = ""
    PAYOS_COLLECTION_CHANNEL: str = "freelancer-collection"
    PAYOS_COLLECTION_BANK_BIN: str = ""
    PAYOS_COLLECTION_ACCOUNT_NUMBER: str = ""
    PAYOS_PAYOUT_CLIENT_ID: str = ""
    PAYOS_PAYOUT_API_KEY: str = ""
    PAYOS_PAYOUT_CHECKSUM_KEY: str = ""
    PAYOS_RETURN_URL: str = ""
    PAYOS_CANCEL_URL: str = ""
    PAYOS_WEBHOOK_URL: str = ""
    PAYOS_TIMEOUT_SECONDS: float = Field(default=15, ge=1, le=60)
    PAYOS_ORDER_TTL_SECONDS: int = Field(default=900, ge=300, le=86400)
    # Distinct payout treasury: never assume received funds are moved automatically.
    PAYOS_PAYOUT_TREASURY_SEPARATE: bool = True
    PAYOS_PAYOUT_LOW_BALANCE_THRESHOLD: int = Field(default=100000, ge=0)
    FREELANCER_BANK_ENCRYPTION_KEY: str = ""
    FREELANCER_BANK_KEY_VERSION: str = "v1"
    FREELANCER_BANK_FINGERPRINT_KEY: str = ""
    FREELANCER_DAILY_COLLECTION_LIMIT: int = Field(default=200000000, gt=0)
    FREELANCER_DAILY_PAYOUT_LIMIT: int = Field(default=200000000, gt=0)

    # Private school signing key and trusted business CA; never frontend values.
    MOU_SCHOOL_PFX_PATH: str = ""
    MOU_SCHOOL_PFX_PASSWORD: str = ""
    MOU_TRUST_ROOT_PATH: str = ""

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
