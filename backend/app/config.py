"""
PatentPilot Configuration Module.

Loads application settings from environment variables and .env file
using pydantic-settings.
"""

from pathlib import Path

from pydantic_settings import BaseSettings


BACKEND_ENV_FILE = Path(__file__).resolve().parents[1] / ".env"


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    MONGODB_URI: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "patentpilot"
    EPO_CONSUMER_KEY: str = ""
    EPO_CONSUMER_SECRET: str = ""
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.0-flash"
    SURECHEMBL_BASE_URL: str = "https://www.surechembl.org/api"
    EPO_OPS_BASE_URL: str = "https://ops.epo.org/3.2/rest-services"
    EPO_OPS_AUTH_URL: str = "https://ops.epo.org/3.2/auth/accesstoken"
    TOP_N_PATENTS: int = 5
    SIMILARITY_THRESHOLD: float = 0.7

    model_config = {
        "env_file": BACKEND_ENV_FILE,
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


# Singleton instance
settings = Settings()
