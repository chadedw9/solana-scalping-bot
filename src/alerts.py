"""Background job that checks tracked prices and fires triggered alerts."""

from __future__ import annotations

import logging

from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from . import prices
from .handlers import _fmt_price
from .storage import Storage

logger = logging.getLogger(__name__)


def _triggered(direction: str, current: float, target: float) -> bool:
    return current >= target if direction == "above" else current <= target


async def check_alerts(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Poll prices for every stored alert; notify and delete the ones that fire.

    Prices are cached per query within a single pass so we hit the API once per
    token even when several users track the same one.
    """
    storage: Storage = context.application.bot_data["storage"]
    alerts = storage.all_alerts()
    if not alerts:
        return

    price_cache: dict[str, float | None] = {}

    for alert in alerts:
        if alert.query not in price_cache:
            try:
                result = await prices.get_price(alert.query)
                price_cache[alert.query] = result.price_usd if result else None
            except Exception as exc:  # network hiccup — skip this round, retry next
                logger.warning("Price check failed for %s: %s", alert.query, exc)
                price_cache[alert.query] = None

        current = price_cache[alert.query]
        if current is None:
            continue

        if _triggered(alert.direction, current, alert.target_price):
            try:
                await context.bot.send_message(
                    chat_id=alert.chat_id,
                    text=(
                        f"🚨 *{alert.symbol}* is now {_fmt_price(current)} "
                        f"({alert.direction} your target of {_fmt_price(alert.target_price)})!"
                    ),
                    parse_mode=ParseMode.MARKDOWN,
                )
                storage.delete_alert(alert.id)
            except Exception as exc:
                logger.warning("Failed to send alert #%s: %s", alert.id, exc)
