"""
Pydantic Settings — centralised environment variable definitions.

All values are read from environment variables (or a .env file when running
locally).  Import the singleton ``settings`` wherever config is needed:

    from app.config import settings
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application-wide configuration backed by env vars."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # ── Database ───────────────────────────────────────────────
    database_url: str = "postgresql+asyncpg://localhost:5432/moku"

    # ── Cloudflare R2 ─────────────────────────────────────────
    r2_access_key_id: str = ""
    r2_secret_access_key: str = ""  # NEVER expose to frontend
    r2_endpoint_url: str = ""  # https://<account_id>.r2.cloudflarestorage.com
    r2_bucket_name: str = "moku-archive"
    r2_public_url: str = ""  # e.g. https://pub-xxx.r2.dev

    # ── Auth / JWT ─────────────────────────────────────────────
    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_hours: int = 24
    moku_admin_password: str = ""

    # ── Analytics & Verification ───────────────────────────────
    ga_measurement_id: str = "G-M0EESK8HQK"
    google_site_verification: str = ""
    naver_site_verification: str = ""

    # ── CORS ───────────────────────────────────────────────────
    cors_origins: list[str] = [
        "http://localhost:3000",
        "https://moku.com",
        "https://www.moku.com",
    ]

    # ── Server ─────────────────────────────────────────────────
    debug: bool = False


settings = Settings()
