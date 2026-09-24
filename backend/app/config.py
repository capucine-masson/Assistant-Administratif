import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


def _require_secret_key() -> str:
    key = os.getenv("SECRET_KEY", "")
    if not key or key == "change-me-generate-a-random-secret":
        # Ne bloque pas le démarrage en dev, mais on prévient bien fort.
        print(
            "[WARNING] SECRET_KEY n'est pas défini ou utilise la valeur par défaut. "
            "Définissez une vraie valeur dans .env pour la production."
        )
        key = key or "dev-insecure-secret-key"
    return key


class Settings:
    SECRET_KEY: str = _require_secret_key()
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./data/app.db")
    CATALOG_PATH: Path = Path(os.getenv("CATALOG_PATH", "/app/data/demarches_catalog.json"))

    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "none").lower()

    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")


settings = Settings()
