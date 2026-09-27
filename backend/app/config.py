import logging
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

_INSECURE_DEFAULTS = {"", "change-me-generate-a-random-secret", "secret"}


def _require_secret_key() -> str:
    environment = os.getenv("ENVIRONMENT", "development").lower()
    key = os.getenv("SECRET_KEY", "")

    if key not in _INSECURE_DEFAULTS:
        return key

    if environment == "production":
        raise RuntimeError(
            "SECRET_KEY manquant ou utilise une valeur par défaut non sécurisée. "
            "Générez-en une avec `python -c \"import secrets; print(secrets.token_hex(32))\"` "
            "et définissez-la dans .env avant de démarrer en production."
        )

    logger.warning(
        "SECRET_KEY n'est pas défini ou utilise la valeur par défaut. "
        "Définissez une vraie valeur dans .env avant de déployer en production."
    )
    return key or "dev-insecure-secret-key"


class Settings:
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development").lower()
    SECRET_KEY: str = _require_secret_key()
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./data/app.db")
    CATALOG_PATH: Path = Path(os.getenv("CATALOG_PATH", "/app/data/demarches_catalog.json"))

    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "none").lower()

    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")


settings = Settings()
