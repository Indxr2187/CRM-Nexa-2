import os
from datetime import timedelta
from dotenv import load_dotenv

# Load variables from .env file
load_dotenv()


class Config:

    SECRET_KEY = os.getenv(
        "SECRET_KEY",
        "dev-only-change-me"
    )

    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "sqlite:///crm.db"
    )

    # Convert Neon postgres URL for psycopg3
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace(
            "postgres://",
            "postgresql+psycopg://",
            1
        )

    elif DATABASE_URL.startswith("postgresql://"):
        DATABASE_URL = DATABASE_URL.replace(
            "postgresql://",
            "postgresql+psycopg://",
            1
        )

    SQLALCHEMY_DATABASE_URI = DATABASE_URL

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 300
    }

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"

    REMEMBER_COOKIE_HTTPONLY = True

    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)

    WTF_CSRF_TIME_LIMIT = None

    # Only enable secure cookies on Vercel HTTPS
    SESSION_COOKIE_SECURE = bool(os.getenv("VERCEL"))