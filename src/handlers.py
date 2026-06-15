"""Telegram command handlers."""

from __future__ import annotations

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from . import prices, wallet
from .storage import Storage

WELCOME = (
    "👋 *Solana Price Alert & Wallet Bot*\n\n"
    "I track Solana token prices *and* wallet activity, and ping you in real time.\n\n"
    "*Price commands*\n"
    "• `/price <token>` — current price (symbol or mint address)\n"
    "• `/track <token> above|below <price>` — set a price alert\n"
    "• `/alerts` — list your active alerts\n"
    "• `/untrack <id>` — remove an alert\n\n"
    "*Wallet commands*\n"
    "• `/watch <address> [label]` — get pinged on new wallet activity\n"
    "• `/wallets` — list watched wallets\n"
    "• `/unwatch <id>` — stop watching a wallet\n\n"
    "*Examples*\n"
    "`/price BONK`\n"
    "`/track SOL above 200`\n"
    "`/watch 7xKX...9fG2 whale1`"
)


def _storage(context: ContextTypes.DEFAULT_TYPE) -> Storage:
    return context.application.bot_data["storage"]


def _fmt_price(value: float) -> str:
    """Human-friendly formatting for both large and tiny token prices."""
    if value >= 1:
        return f"${value:,.4f}"
    return f"${value:.10f}".rstrip("0").rstrip(".")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(WELCOME, parse_mode=ParseMode.MARKDOWN)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(WELCOME, parse_mode=ParseMode.MARKDOWN)


async def price(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("Usage: `/price <token>`", parse_mode=ParseMode.MARKDOWN)
        return

    query = context.args[0]
    try:
        result = await prices.get_price(query)
    except Exception:
        await update.message.reply_text("⚠️ Couldn't reach the price service. Try again shortly.")
        return

    if result is None:
        await update.message.reply_text(f"❓ Couldn't find a Solana token matching *{query}*.",
                                        parse_mode=ParseMode.MARKDOWN)
        return

    change = result.price_change_24h
    change_line = ""
    if change is not None:
        arrow = "🟢" if change >= 0 else "🔴"
        change_line = f"\n{arrow} 24h: {change:+.2f}%"

    await update.message.reply_text(
        f"*{result.symbol}* — {result.name}\n"
        f"💵 {_fmt_price(result.price_usd)}{change_line}\n"
        f"[Chart]({result.url})",
        parse_mode=ParseMode.MARKDOWN,
        disable_web_page_preview=True,
    )


async def track(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if len(context.args) < 3:
        await update.message.reply_text(
            "Usage: `/track <token> above|below <price>`\nExample: `/track SOL above 200`",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    query, direction, raw_price = context.args[0], context.args[1].lower(), context.args[2]

    if direction not in ("above", "below"):
        await update.message.reply_text("Direction must be `above` or `below`.",
                                        parse_mode=ParseMode.MARKDOWN)
        return

    try:
        target = float(raw_price.replace(",", "").lstrip("$"))
    except ValueError:
        await update.message.reply_text(f"'{raw_price}' is not a valid price.")
        return

    try:
        result = await prices.get_price(query)
    except Exception:
        await update.message.reply_text("⚠️ Couldn't reach the price service. Try again shortly.")
        return

    if result is None:
        await update.message.reply_text(f"❓ Couldn't find a Solana token matching *{query}*.",
                                        parse_mode=ParseMode.MARKDOWN)
        return

    alert_id = _storage(context).add_alert(
        chat_id=update.effective_chat.id,
        query=query,
        symbol=result.symbol,
        direction=direction,
        target_price=target,
    )
    await update.message.reply_text(
        f"✅ Alert *#{alert_id}* set: notify when *{result.symbol}* goes "
        f"*{direction}* {_fmt_price(target)}\n"
        f"(currently {_fmt_price(result.price_usd)})",
        parse_mode=ParseMode.MARKDOWN,
    )


async def alerts(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    rows = _storage(context).list_alerts(update.effective_chat.id)
    if not rows:
        await update.message.reply_text("You have no active alerts. Set one with `/track`.",
                                        parse_mode=ParseMode.MARKDOWN)
        return
    lines = [
        f"*#{a.id}* — {a.symbol} {a.direction} {_fmt_price(a.target_price)}" for a in rows
    ]
    await update.message.reply_text(
        "*Your alerts*\n" + "\n".join(lines) + "\n\nRemove with `/untrack <id>`.",
        parse_mode=ParseMode.MARKDOWN,
    )


async def untrack(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("Usage: `/untrack <id>`", parse_mode=ParseMode.MARKDOWN)
        return
    alert_id = int(context.args[0])
    removed = _storage(context).remove_alert(update.effective_chat.id, alert_id)
    if removed:
        await update.message.reply_text(f"🗑️ Removed alert #{alert_id}.")
    else:
        await update.message.reply_text(f"No alert #{alert_id} found for you.")


async def watch(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text(
            "Usage: `/watch <wallet_address> [label]`", parse_mode=ParseMode.MARKDOWN
        )
        return

    address = context.args[0]
    if not wallet.is_solana_address(address):
        await update.message.reply_text("That doesn't look like a valid Solana wallet address.")
        return

    label = " ".join(context.args[1:]).strip()

    # Baseline at the current newest tx so we only alert on *future* activity.
    try:
        baseline = await wallet.latest_signature(address)
    except Exception:
        await update.message.reply_text("⚠️ Couldn't reach the Solana network. Try again shortly.")
        return

    wallet_id = _storage(context).add_wallet(
        chat_id=update.effective_chat.id, address=address, label=label, last_signature=baseline
    )
    name = f" ({label})" if label else ""
    await update.message.reply_text(
        f"👀 Now watching wallet *#{wallet_id}*{name}.\n"
        f"`{address}`\n"
        "I'll ping you on new activity.",
        parse_mode=ParseMode.MARKDOWN,
    )


async def wallets(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    rows = _storage(context).list_wallets(update.effective_chat.id)
    if not rows:
        await update.message.reply_text("You're not watching any wallets. Add one with `/watch`.",
                                        parse_mode=ParseMode.MARKDOWN)
        return
    lines = []
    for w in rows:
        name = f" — {w.label}" if w.label else ""
        short = f"{w.address[:4]}...{w.address[-4:]}"
        lines.append(f"*#{w.id}*{name}  `{short}`")
    await update.message.reply_text(
        "*Watched wallets*\n" + "\n".join(lines) + "\n\nRemove with `/unwatch <id>`.",
        parse_mode=ParseMode.MARKDOWN,
    )


async def unwatch(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("Usage: `/unwatch <id>`", parse_mode=ParseMode.MARKDOWN)
        return
    wallet_id = int(context.args[0])
    removed = _storage(context).remove_wallet(update.effective_chat.id, wallet_id)
    if removed:
        await update.message.reply_text(f"🗑️ Stopped watching wallet #{wallet_id}.")
    else:
        await update.message.reply_text(f"No watched wallet #{wallet_id} found for you.")
