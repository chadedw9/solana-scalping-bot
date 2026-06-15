"""Entry point for the Solana Telegram price-alert bot.

Run with:  python bot.py
"""

from __future__ import annotations

import logging

from telegram.ext import Application, CommandHandler

import config
from src import handlers
from src.alerts import check_alerts
from src.storage import Storage

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def main() -> None:
    config.validate()

    application = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()
    application.bot_data["storage"] = Storage(config.DATABASE_PATH)

    application.add_handler(CommandHandler("start", handlers.start))
    application.add_handler(CommandHandler("help", handlers.help_command))
    application.add_handler(CommandHandler("price", handlers.price))
    application.add_handler(CommandHandler("track", handlers.track))
    application.add_handler(CommandHandler("alerts", handlers.alerts))
    application.add_handler(CommandHandler("untrack", handlers.untrack))

    application.job_queue.run_repeating(
        check_alerts, interval=config.CHECK_INTERVAL_SECONDS, first=10
    )

    logger.info("Bot started. Press Ctrl+C to stop.")
    application.run_polling(allowed_updates=["message"])


if __name__ == "__main__":
    main()
