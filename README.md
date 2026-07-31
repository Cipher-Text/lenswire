# Telegram Interest-Based News Bot

Sends you news matching your chosen interests, pulled from RSS feeds and NewsAPI,
matched using semantic similarity (so "AI" also catches articles about "machine learning" or "LLMs").

## 1. Get a Telegram bot token

1. Open Telegram, message **@BotFather**
2. Send `/newbot` and follow the prompts
3. Copy the token it gives you

## 2. (Optional) Get a NewsAPI key

1. Sign up free at https://newsapi.org
2. Copy your API key (free tier: 100 requests/day, article delay of 24h — RSS feeds fill the gap for real-time news)

## 3. Install dependencies

```bash
cd telegram_news_bot
python3 -m venv venv
source venv/bin/activate   # on Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## 4. Set your credentials

Either edit `config.py` directly, or set environment variables:

```bash
export TELEGRAM_BOT_TOKEN="123456:ABC-your-token-here"
export NEWSAPI_KEY="your-newsapi-key-here"   # optional
```

## 5. Run the bot

```bash
python3 bot.py
```

First run will download the embedding model (~80MB) — needs internet, only happens once.

## 6. Use it in Telegram

- `/start` — register
- `/setinterests AI, climate change, football` — set what you care about (comma-separated)
- `/myinterests` — see current interests
- `/news` — force a check right now
- Otherwise, the bot automatically checks every 30 minutes (configurable in `config.py`) and pushes new matches

## Customizing

- **`config.py`** — add/remove RSS feeds, change check frequency, adjust match strictness (`SIMILARITY_THRESHOLD`, 0–1: higher = stricter)
- **`matcher.py`** — swap the embedding model, or add re-ranking logic
- Want per-user custom RSS feeds instead of a shared global list? Extend the `users` table in `db.py` with a `feeds` column.

## Notes

- Runs via polling (no public URL/webhook needed) — fine for personal use on your own machine.
- Uses SQLite (`news_bot.db`, created automatically) to track sent articles so you don't get duplicates.
- To keep it running persistently, use `tmux`/`screen`, or set it up as a systemd service / cron-launched process.
