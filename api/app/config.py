import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv

# Explicitly load .env from the api/ directory so it works regardless of cwd
_env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_env_path, override=True)

# ── Branding ──────────────────────────────────────────────
APP_NAME = "Wellvio"
APP_SLUG = "wellvio"
APP_DESCRIPTION = "Track physical progress, meals, weigh-ins, goals, workouts, and professional notes."


def _fix_db_url(url: str) -> str:
    """Neon/Vercel Postgres provides postgres:// but SQLAlchemy needs postgresql://."""
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql://", 1)
    return url


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
    SQLALCHEMY_DATABASE_URI = _fix_db_url(
        os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/wellvio")
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}

    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "jwt-dev-secret")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(
        seconds=int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES", "900"))
    )
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(
        seconds=int(os.getenv("JWT_REFRESH_TOKEN_EXPIRES", "2592000"))
    )
    JWT_TOKEN_LOCATION = ["headers"]

    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10 MB upload limit

    STORAGE_BACKEND = os.getenv("STORAGE_BACKEND", "local")
    STORAGE_LOCAL_PATH = os.getenv("STORAGE_LOCAL_PATH", "uploads")

    S3_BUCKET = os.getenv("S3_BUCKET", "")
    S3_REGION = os.getenv("S3_REGION", "us-east-1")
    S3_ACCESS_KEY = os.getenv("S3_ACCESS_KEY", "")
    S3_SECRET_KEY = os.getenv("S3_SECRET_KEY", "")
    S3_ENDPOINT_URL = os.getenv("S3_ENDPOINT_URL", "")

    FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")
