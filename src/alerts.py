"""Background job that checks tracked prices and fires triggered alerts."""

from __future__ import annotations

import logging

from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from . import prices, wallet
from .handlers import _fmt_price
from .storage import Storage

logger = logging.getLogger(__name__)

# Cap how many transactions we announce per wallet per poll, to avoid spamming
# a chat when a busy wallet does a burst of activity.
MAX_ACTIVITY_PER_POLL = 5


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


async def check_wallets(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Poll watched wallets for new transactions and notify their owners."""
    storage: Storage = context.application.bot_data["storage"]
    wallets = storage.all_wallets()
    if not wallets:
        return

    for w in wallets:
        try:
            newest, items = await wallet.fetch_new_activity(w.address, w.last_signature)
        except Exception as exc:  # network/rate-limit hiccup — retry next round
            logger.warning("Wallet check failed for %s: %s", w.address, exc)
            continue

        if not items:
            continue

        # Advance the high-water mark first so a send failure can't replay activity.
        storage.update_wallet_signature(w.id, newest)

        name = w.label or f"{w.address[:4]}...{w.address[-4:]}"
        overflow = len(items) - MAX_ACTIVITY_PER_POLL
        for activity in items[:MAX_ACTIVITY_PER_POLL]:
            status = "" if activity.success else " ⚠️ (failed tx)"
            detail = activity.description or "New transaction"
            try:
                await context.bot.send_message(
                    chat_id=w.chat_id,
                    text=(
                        f"💼 *{name}*{status}\n"
                        f"{detail}\n"
                        f"[View on Solscan]({activity.solscan_url})"
                    ),
                    parse_mode=ParseMode.MARKDOWN,
                    disable_web_page_preview=True,
                )
            except Exception as exc:
                logger.warning("Failed to send wallet activity to %s: %s", w.chat_id, exc)

        if overflow > 0:
            try:
                await context.bot.send_message(
                    chat_id=w.chat_id, text=f"…and {overflow} more recent tx from *{name}*.",
                    parse_mode=ParseMode.MARKDOWN,
                )
            except Exception:
                pass
