# Solana Price Alert Bot 🤖📈

A Telegram bot that tracks **Solana token prices** and pings you the instant a
token crosses a target you set. Built in Python with a clean, extensible
architecture — works with any SPL token by **symbol or mint address**, no paid
API keys required.

> **Live demo:** message [@YourBotName](https://t.me/) on Telegram and try
> `/price SOL`. *(Replace with your bot's link once deployed.)*

---

## ✨ Features

- **Instant prices** — `/price SOL`, `/price BONK`, or paste any mint address.
- **Smart alerts** — `/track SOL above 200` notifies you the moment it triggers.
- **Wallet tracking** — `/watch <address>` pings you on any new wallet activity,
  with a Solscan link (and "swapped X for Y" descriptions if a Helius key is set).
- **Persistent** — alerts and watched wallets survive restarts (SQLite).
- **Efficient** — batches price lookups so 100 users tracking SOL = 1 API call.
- **Free data sources** — public DexScreener + Solana RPC (no keys required).
- **Handles micro-cap prices** — formats values like `$0.0000123` correctly.

## 🧰 Commands

| Command | Description |
|---|---|
| `/price <token>` | Current price (symbol or mint address) |
| `/track <token> above\|below <price>` | Set a price alert |
| `/alerts` | List your active alerts |
| `/untrack <id>` | Remove an alert |
| `/watch <address> [label]` | Watch a wallet for new activity |
| `/wallets` | List watched wallets |
| `/unwatch <id>` | Stop watching a wallet |
| `/help` | Show help |

## 🚀 Setup (5 minutes)

1. **Create a bot** — message [@BotFather](https://t.me/BotFather) on Telegram,
   send `/newbot`, and copy the token it gives you.
2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
3. **Configure:**
   ```bash
   cp .env.example .env
   # open .env and paste your TELEGRAM_BOT_TOKEN
   ```
4. **Run it:**
   ```bash
   python bot.py
   ```
5. Open Telegram, message your bot `/start`, and try `/price SOL`.

## 🏗️ Project structure

```
bot.py            # entry point — wires handlers + the alert checker
config.py         # environment configuration
src/
  prices.py       # DexScreener price lookups (by symbol or mint address)
  wallet.py       # Solana RPC wallet activity tracking (+ optional Helius enrich)
  storage.py      # SQLite persistence for alerts and watched wallets
  handlers.py     # Telegram command handlers
  alerts.py       # background jobs: price alerts + wallet activity
```

## ☁️ Deployment

Runs anywhere Python runs. For 24/7 uptime (and a public demo link you can put
in your gigs/proposals), follow **[DEPLOY.md](DEPLOY.md)** — step-by-step guides
for Railway (easiest), Render, and a VPS, plus a ready-to-use `Dockerfile`.

## 🛣️ Extending it

This is a solid base you can grow into a full trading toolkit:
- **Wallet tracking** — watch a wallet and report buys/sells & PnL.
- **New-pair sniping** — alert on freshly created liquidity pools.
- **Auto-trading** — connect a wallet to execute on Jupiter/Raydium.
- **Portfolio dashboards** — summary commands and charts.

## ⚠️ Disclaimer

This bot provides market data for informational purposes only. It is **not
financial advice**. Crypto trading carries significant risk — never trade more
than you can afford to lose, and always do your own research.

## 📄 License

MIT
