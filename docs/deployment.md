# Deployment

Lenswire runs continuously through Telegram polling. Do not launch it from cron.

## Docker Compose

1. Copy `.env.example` to `.env` and set `TELEGRAM_BOT_TOKEN`.
2. Optional: add `OPENROUTER_API_KEY` and `GEMINI_API_KEY` if you want AI summaries.
3. Optional: add `EDITORIAL_TELEGRAM_IDS` if you want review commands.
4. Run `docker compose up -d --build`.
5. Inspect logs with `docker compose logs -f lenswire`.

The Compose file uses persistent volumes for SQLite data and local caches, and mounts `./config` so `config/sources.yaml` can be edited on the VM without rebuilding.

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
