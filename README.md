# Lenswire

A curated geopolitical news and editorial intelligence bot for FactLens.

Lenswire collects geopolitical news from configured trusted sources, identifies the main publisher, extracts article content where allowed, classifies stories under curated FactLens topics, generates concise summaries and delivers stories through Telegram.

Lenswire is not a full fact-checking platform. Automated summaries can contain errors, and a single-source story is not automatically verified. The default flow publishes from the configured trusted source registry; human review is still recommended before high-stakes public distribution.

## Audiences

- General users subscribe to topics and receive stories from the configured trusted source registry.
- Optional editorial users can still inspect source context and approve or reject stories, but the default flow does not require editorial review.

## Architecture

The app is a modular monolith:

- `app/bot`: Telegram commands, callbacks and permissions.
- `app/ingestion`: RSS/API discovery, URL normalization, source detection and extraction.
- `app/matching`: topic classification and story similarity helpers.
- `app/summarization`: summary provider abstraction and deterministic fallback.
- `app/editorial`: save, approve and reject workflow.
- `app/delivery`: message formatting and delivery deduplication.
- `app/persistence`: SQLite migrations and repositories.
- `app/domain`: shared domain models.

SQLite is used for the pilot and isolated behind repositories for a later PostgreSQL migration.

## Features

- Curated geopolitical topic subscriptions.
- Source registry with source type and credibility tier.
- Async RSS/API fetching and per-source failure isolation.
- Canonical URL and content-hash duplicate controls.
- Deterministic summary fallback with optional OpenRouter-first/Gemini AI failover.
- Optional editorial queue with authorization.
- Safe Telegram HTML escaping.
- Legacy `/setinterests` compatibility.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Set at minimum:

```bash
TELEGRAM_BOT_TOKEN=123456:telegram-token
```

Run locally:

```bash
python -m app.main
```

The compatibility entrypoint also works:

```bash
python bot.py
```

## Configuration

Configuration is read from environment variables. See `.env.example` for all options, including:

- `TELEGRAM_BOT_TOKEN`
- `NEWSAPI_KEY`
- `DATABASE_PATH`
- `SOURCE_CONFIG_PATH`
- `EDITORIAL_TELEGRAM_IDS`
- `INGESTION_INTERVAL_MINUTES`
- `SIMILARITY_THRESHOLD`
- `SUMMARY_PROVIDER`
- `SUMMARY_OUTPUT_LANGUAGE`
- `AI_PROVIDER`
- `AI_PROVIDER_ORDER`
- `AI_API_KEY`
- `AI_API_BASE_URL`
- `AI_MODEL`
- `OPENROUTER_API_KEY`
- `OPENROUTER_API_BASE_URL`
- `OPENROUTER_MODEL`
- `GEMINI_API_KEY`
- `GEMINI_API_BASE_URL`
- `GEMINI_MODEL`
- `AI_REQUEST_TIMEOUT_SECONDS`
- `EXTERNAL_DELIVERY_APPROVAL_REQUIRED`
- `AUTO_PUBLISH_TRUSTED_SOURCES`
- `TRUSTED_SOURCES_ONLY`
- `LOG_LEVEL`

Do not paste credentials into source files.

## AI Summaries

Lenswire works without AI. To enable OpenRouter-first summaries with Gemini fallback:

```env
SUMMARY_PROVIDER=ai
AI_PROVIDER=failover
AI_PROVIDER_ORDER=openrouter,gemini
OPENROUTER_API_KEY=your_openrouter_key
OPENROUTER_API_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_MODEL=openrouter/free
GEMINI_API_KEY=your_gemini_key
GEMINI_API_BASE_URL=https://generativelanguage.googleapis.com/v1beta
GEMINI_MODEL=gemini-2.5-flash
AI_REQUEST_TIMEOUT_SECONDS=30
```

Lenswire always tries OpenRouter first. If OpenRouter fails, hits a limit, returns 404 for a model, times out, or returns invalid JSON, Lenswire tries Gemini. If both AI providers fail, it uses the deterministic fallback summary and continues ingestion.

For zero-cost OpenRouter usage, use `openrouter/free` or a specific `:free` model. Do not use `openrouter/auto` if you want to avoid paid model routing.

## Source List

Trusted source and RSS settings live in:

```text
config/sources.yaml
```

Each source entry includes `name`, `domain`, `source_type`, `credibility_tier`, `language`, `country_or_region`, optional `rss_url` and `enabled`.

After editing `config/sources.yaml` on a VM, restart the bot:

```bash
docker compose restart lenswire
```

Lenswire syncs this file into SQLite at startup. Existing source rows are updated by domain.

## Telegram Commands

General:

- `/start`
- `/topics`
- `/subscribe <topic-key>`
- `/unsubscribe <topic-key>`
- `/mysubscriptions`
- `/latest`
- `/digest`
- `/language en|bn`
- `/quiettime 22:00 07:00`
- `/stop`
- `/deleteaccount`
- `/setinterests ...` and `/myinterests` for legacy compatibility

Optional editorial:

- `/review`
- `/latest`
- `/sources`
- `/context <article_id>`
- `/angle <article_id>`
- `/save <article_id>`
- `/approve <article_id>`
- `/reject <article_id>`
- `/breaking`

## Editorial Workflow

By default Lenswire runs in a simple trusted-source flow:

```env
EXTERNAL_DELIVERY_APPROVAL_REQUIRED=false
AUTO_PUBLISH_TRUSTED_SOURCES=true
TRUSTED_SOURCES_ONLY=true
```

That means stories discovered from registered enabled sources are visible to subscribed users after ingestion. NewsAPI stories from unregistered publishers are skipped when trusted-source-only mode is enabled.

The editorial workflow remains available if you later want review gates. Set `EXTERNAL_DELIVERY_APPROVAL_REQUIRED=true` and `AUTO_PUBLISH_TRUSTED_SOURCES=false` if you want stories to require approval before general users see them.

Verification statuses include `UNREVIEWED`, `SINGLE_SOURCE`, `MULTI_SOURCE`, `PRIMARY_SOURCE_FOUND`, `EDITOR_APPROVED`, `REJECTED` and `DISPUTED`.

## Testing

```bash
ruff format --check .
ruff check .
mypy app
pytest
```

Unit tests mock external network and embedding behavior. They do not require internet connectivity or model downloads.

## Docker Deployment

```bash
cp .env.example .env
docker compose up -d --build
docker compose logs -f lenswire
```

The container runs as a non-root user and uses volumes for SQLite data and cache directories. Use Docker Compose or systemd for continuous operation, not cron.

## Privacy Notes

Lenswire stores Telegram chat IDs, topic subscriptions, language preferences, quiet hours and delivery history. `/deleteaccount` removes subscription data for a user. Delivery-history retention is configurable.

## Limitations

- Deterministic summaries are extractive and may miss nuance.
- Primary-source detection is prepared but initially heuristic.
- Supporting-source matching is basic.
- Bangla output architecture exists, but deterministic summaries are strongest in English.
- Trusted source ingestion is not independent factual verification.

## Roadmap

See `docs/roadmap.md`.

## User Manual

See `docs/user-manual.md` for end-to-end bot usage, simple flow, optional editorial flow, commands, operations and troubleshooting.
