# Deploy the Bot 24/7 (so you have a live demo link to sell)

Your demo link is your #1 sales tool — buyers who can *try the bot* convert far
better than a screenshot. This guide gets it running around the clock. Pick ONE
option. **Railway is the easiest for beginners — start there.**

---

## ✅ Before you deploy (2 minutes)

1. Message [@BotFather](https://t.me/BotFather) on Telegram → send `/newbot`.
2. Pick a name and a username (must end in `bot`, e.g. `MySolAlertBot`).
3. Copy the **token** it gives you (looks like `123456789:AA...`). Keep it secret.
4. Note your bot's public link: `https://t.me/<your_bot_username>` — this is the
   link you'll put in your Fiverr gigs and Upwork proposals.

> ⚠️ Never commit your token. It goes in the platform's environment variables,
> never in the code. (`.env` is already gitignored.)

---

## Option A — Railway (recommended, ~5 min, no card to start)

1. Go to [railway.app](https://railway.app) and sign in with GitHub.
2. **New Project → Deploy from GitHub repo →** pick `solana-scalping-bot`.
3. Railway auto-detects the `Dockerfile` and builds it.
4. Open the service → **Variables** tab → add:
   - `TELEGRAM_BOT_TOKEN` = *(your BotFather token)*
   - *(optional)* `CHECK_INTERVAL_SECONDS` = `60`
5. Deploy. Watch the **Logs** tab for `Bot started.`
6. Open Telegram, message your bot `/start`, then `/price SOL`. 🎉

**Keeping data:** alerts are stored in `alerts.db`. To keep them across redeploys,
add a **Volume** mounted at `/app` (Railway → service → Variables/Volumes), and
set `DATABASE_PATH=/app/data/alerts.db` with the volume mounted at `/app/data`.
For a demo, the default (ephemeral) is fine.

---

## Option B — Render (free worker tier, ~7 min)

1. Go to [render.com](https://render.com) → sign in with GitHub.
2. **New → Background Worker →** connect the repo.
3. Environment: **Docker** (it'll use the `Dockerfile`). Start command is already
   set by the Dockerfile `CMD`.
4. Add environment variable `TELEGRAM_BOT_TOKEN`.
5. Create → wait for build → check logs for `Bot started.`

> Note: Render's free tier may sleep on inactivity. For an always-on demo, use
> Railway or a cheap VPS.

---

## Option C — Any VPS (full control, ~$5/mo, most reliable for clients)

Good once you have paying clients who need guaranteed uptime.

```bash
# On the server (Ubuntu example):
sudo apt update && sudo apt install -y python3-pip git
git clone https://github.com/chadedw9/solana-scalping-bot.git
cd solana-scalping-bot
pip3 install -r requirements.txt
cp .env.example .env
nano .env          # paste your TELEGRAM_BOT_TOKEN, save
```

Run it 24/7 with systemd so it restarts on crash/reboot:

```bash
sudo tee /etc/systemd/system/solbot.service >/dev/null <<'EOF'
[Unit]
Description=Solana Price Alert Bot
After=network.target

[Service]
WorkingDirectory=/root/solana-scalping-bot
EnvironmentFile=/root/solana-scalping-bot/.env
ExecStart=/usr/bin/python3 bot.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now solbot
sudo systemctl status solbot      # should say "active (running)"
journalctl -u solbot -f           # live logs
```

---

## Run locally with Docker (to test before deploying)

```bash
docker build -t solbot .
docker run -e TELEGRAM_BOT_TOKEN=your-token-here solbot
```

---

## After it's live — turn it into sales

1. Put `https://t.me/<your_bot_username>` in:
   - Every Fiverr gig description (`marketing/fiverr-gigs.md`)
   - Your Upwork proposals (`marketing/proposal-template.md`)
2. Record a 30–60s screen capture of `/price` and `/track` working → add to gigs.
3. Pin a screenshot to your Upwork portfolio entry.

A live bot + a 60-second video is what converts strangers into your first orders.
