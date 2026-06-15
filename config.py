"""Configuration loaded from environment variables (and an optional .env file)."""

import os

from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
CHECK_INTERVAL_SECONDS = int(os.getenv("CHECK_INTERVAL_SECONDS", "60"))
DATABASE_PATH = os.getenv("DATABASE_PATH", "alerts.db").strip()

# Wallet tracking. The public RPC works with no key but is rate-limited; for
# production point this at a Helius/QuickNode/Triton endpoint.
SOLANA_RPC_URL = os.getenv("SOLANA_RPC_URL", "https://api.mainnet-beta.solana.com").strip()
WALLET_CHECK_INTERVAL_SECONDS = int(os.getenv("WALLET_CHECK_INTERVAL_SECONDS", "90"))
# Optional: enables human-readable "swapped X for Y" descriptions.
HELIUS_API_KEY = os.getenv("HELIUS_API_KEY", "").strip()


def validate() -> None:
    """Fail fast with a helpful message if required config is missing."""
    if not TELEGRAM_BOT_TOKEN:
        raise SystemExit(
            "TELEGRAM_BOT_TOKEN is not set.\n"
            "Copy .env.example to .env and paste the token you got from @BotFather."
        )
