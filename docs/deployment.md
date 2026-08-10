# Deployment

Lenswire runs continuously through Telegram polling. Do not launch it from cron.

## Docker Compose

1. Copy `.env.example` to `.env` and set `TELEGRAM_BOT_TOKEN`.
2. Optional: add `OPENROUTER_API_KEY` and `GEMINI_API_KEY` if you want AI summaries.
3. Optional: configure Telegram channel delivery with `TELEGRAM_CHANNEL_ID`, `CHANNEL_TOPIC_KEYS`, `CHANNEL_OUTPUT_LANGUAGE=bn`, `CHANNEL_DELIVERY_ENABLED=true` and `CHANNEL_DELIVERY_INTERVAL_MINUTES=30`.
4. Optional: add `EDITORIAL_TELEGRAM_IDS` if you want review commands.
5. Run `docker compose up -d --build`.
6. Inspect logs with `docker compose logs -f lenswire`.

The Compose file uses persistent volumes for SQLite data and local caches, and mounts `./config` so `config/sources.yaml` can be edited on the VM without rebuilding. The app no longer downloads Hugging Face embedding models; topic matching is keyword-based.

Use specific AI models for stable Bangla summaries:

```env
SUMMARY_PROVIDER=ai
SUMMARY_OUTPUT_LANGUAGE=bn
AI_PROVIDER=failover
AI_PROVIDER_ORDER=openrouter,gemini
OPENROUTER_MODEL=google/gemini-3.1-flash-lite
GEMINI_MODEL=gemini-3.1-flash-lite
```

## systemd

Create a virtual environment, install dependencies, create an `.env` file, and run:

```ini
[Unit]
Description=Lenswire Telegram bot
After=network-online.target

[Service]
WorkingDirectory=/opt/lenswire
EnvironmentFile=/opt/lenswire/.env
ExecStart=/opt/lenswire/.venv/bin/python -m app.main
Restart=always
User=lenswire
Group=lenswire

[Install]
WantedBy=multi-user.target
```

Use `systemctl enable --now lenswire`.
