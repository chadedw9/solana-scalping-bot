"""Configuration loaded from environment variables (and an optional .env file)."""

import os

from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
CHECK_INTERVAL_SECONDS = int(os.getenv("CHECK_INTERVAL_SECONDS", "60"))
DATABASE_PATH = os.getenv("DATABASE_PATH", "alerts.db").strip()


def validate() -> None:
    """Fail fast with a helpful message if required config is missing."""
    if not TELEGRAM_BOT_TOKEN:
        raise SystemExit(
            "TELEGRAM_BOT_TOKEN is not set.\n"
            "Copy .env.example to .env and paste the token you got from @BotFather."
        )
