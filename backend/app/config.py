from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict

# Always find .env at the project root regardless of where uvicorn is run from
_ENV_FILE = str(Path(__file__).parent.parent.parent / ".env")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_ENV_FILE,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ──────────────────────────────────────────────────────────
    APP_NAME: str = "LungSight AI"
    APP_VERSION: str = "1.0.0"
    APP_ENV: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str = "lungs1ght-dev-secret-key-change-in-prod"
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:8000"

    @property
    def origins(self) -> List[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",")]

    # ── Database ─────────────────────────────────────────────────────────────
    DATABASE_URL: str = (
        "postgresql+asyncpg://lungs_user:lungs_pass@localhost:5432/lungsight_db"
    )
    DATABASE_URL_SYNC: str = (
        "postgresql://lungs_user:lungs_pass@localhost:5432/lungsight_db"
    )

    # ── Redis ─────────────────────────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"

    # ── JWT ──────────────────────────────────────────────────────────────────
    JWT_SECRET_KEY: str = "lungs1ght-jwt-secret-change-in-prod"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ── ML Models ────────────────────────────────────────────────────────────
    MODELS_DIR: str = "./backend/models/weights"
    DEVICE: str = "cuda"
    MODEL_BATCH_SIZE: int = 1
    IMAGE_SIZE: int = 224

    # ── File Storage ─────────────────────────────────────────────────────────
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE_MB: int = 50
    ALLOWED_EXTENSIONS: str = "png,jpg,jpeg,dcm,dicom"

    @property
    def allowed_extensions(self) -> List[str]:
        return [e.strip().lower() for e in self.ALLOWED_EXTENSIONS.split(",")]

    # ── Reports ───────────────────────────────────────────────────────────────
    REPORTS_DIR: str = "./reports/generated"
    HOSPITAL_NAME: str = "LungSight Medical Center"
    HOSPITAL_LOGO_PATH: str = "./static/logo.png"

    # ── TensorBoard ───────────────────────────────────────────────────────────
    TENSORBOARD_LOG_DIR: str = "./tb_logs"

    # ── Rate Limiting ─────────────────────────────────────────────────────────
    RATE_LIMIT_PER_MINUTE: int = 60

    def is_production(self) -> bool:
        return self.APP_ENV.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
