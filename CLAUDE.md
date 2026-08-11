# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Lenswire is a curated geopolitical news and editorial intelligence bot for FactLens. It runs as a Python-based Telegram bot that ingests articles from RSS feeds and NewsAPI, classifies them by topic, generates summaries, and delivers them to subscribers and/or a Telegram channel on a schedule.

## Commands

**Setup:**
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # Edit .env — TELEGRAM_BOT_TOKEN is required
```

**Run:**
```bash
python -m app.main        # Primary entry point
python bot.py             # Legacy compatibility wrapper
```

**Test and lint:**
```bash
pytest                    # Run all tests
pytest tests/unit/test_foo.py::test_bar  # Run a single test
ruff format --check .     # Check formatting
ruff format .             # Auto-format
ruff check .              # Lint
mypy app                  # Type check
```

**Docker:**
```bash
docker compose up -d --build
docker compose logs -f lenswire
docker compose restart lenswire  # Required after editing config/sources.yaml
```

## Architecture

### Data Flow

1. **Ingestion** (scheduled every 30 min via bot job queue): `IngestionPipeline.run()` in `app/ingestion/pipeline.py` fetches RSS + NewsAPI, normalizes URLs, deduplicates, extracts content via trafilatura, matches topics by keyword, generates summaries, and saves to SQLite.

2. **Delivery**: `DeliveryService` in `app/delivery/service.py` queries subscribed topics for a user (or channel), filters articles not yet delivered, formats them as HTML, sends via Telegram, and records delivery to prevent re-sending.

3. **Editorial workflow** (optional): when `EXTERNAL_DELIVERY_APPROVAL_REQUIRED=true`, articles go through UNREVIEWED → REVIEW_PENDING → APPROVED/REJECTED before delivery. Editors use `/review`, `/approve`, `/reject`, `/save` commands handled in `app/bot/handlers/editorial.py`.

### Module Map

| Module | Purpose |
|---|---|
| `app/bot/application.py` | Bot startup, job queue, handler registration |
| `app/bot/handlers/public.py` | User-facing commands (`/start`, `/subscribe`, `/latest`, `/digest`, etc.) |
| `app/bot/handlers/editorial.py` | Editor commands (`/review`, `/approve`, `/reject`, `/save`) |
| `app/ingestion/pipeline.py` | Ingestion orchestration |
| `app/ingestion/rss.py` / `newsapi.py` | Feed fetchers |
| `app/ingestion/extraction.py` | Article content extraction (trafilatura) |
| `app/matching/topics.py` | Keyword-based topic classification |
| `app/summarization/` | `deterministic.py` (extractive, always works) + `ai_provider.py` (OpenRouter → Gemini failover) |
| `app/delivery/formatter.py` | Safe HTML formatting, including Bangla support |
| `app/persistence/migrations.py` | SQLite schema creation and topic/source seeding |
| `app/persistence/repositories.py` | All DB queries (DAO pattern) |
| `app/persistence/source_config.py` | Loads `config/sources.yaml` into SQLite at startup |
| `app/domain/` | Shared dataclasses/enums: `Article`, `Source`, `Topic`, `User` |
| `app/settings.py` | All config read from environment variables |

### Key Design Decisions

**Async + SQLite thread-pool:** All ingestion and Telegram handlers are `async`. SQLite (sync) is called via `asyncio.to_thread()` throughout `repositories.py`.

**AI summary failover:** `app/summarization/ai_provider.py` tries OpenRouter first; on timeout, 429, or invalid JSON it falls back to Gemini. Both expect JSON `{summary, why_it_matters, editorial_angle, verification_status}`. Deterministic extractive summary is the final fallback.

**Source config is YAML-driven:** `config/sources.yaml` is the source-of-truth for trusted sources. It is synced into the `sources` SQLite table on every startup. Edit the YAML and restart to add/remove sources.

**Deduplication is two-layered:** URL canonicalization (normalize protocol, trailing slash, query params) + SHA256 content hash. A similarity threshold (`SIMILARITY_THRESHOLD` env var) governs near-duplicate detection.

**Telegram HTML formatting:** All user-facing text goes through `html.escape(..., quote=False)` in `formatter.py` to preserve `href` attributes. Bangla content is detected via `BANGLA_RE` regex for language-aware fallback logic.

**User roles:** `UserRole.EXTERNAL` (subscribers) and `UserRole.EDITORIAL` (reviewers). Access control lives in `app/bot/permissions.py`.

### Configuration

All runtime config is in `.env` (see `.env.example`). Key variables:

| Variable | Purpose |
|---|---|
| `TELEGRAM_BOT_TOKEN` | Required |
| `DATABASE_PATH` | SQLite path (default: `data/lenswire.sqlite3`) |
| `SOURCE_CONFIG_PATH` | YAML source registry (default: `config/sources.yaml`) |
| `SUMMARY_PROVIDER` | `deterministic` (default) or `ai` |
| `AI_PROVIDER` | `failover` (OpenRouter → Gemini) |
| `EXTERNAL_DELIVERY_APPROVAL_REQUIRED` | Enable editorial review gate |
| `TELEGRAM_CHANNEL_ID` / `CHANNEL_TOPIC_KEYS` | Channel publishing |
| `INGESTION_INTERVAL_MINUTES` / `DELIVERY_INTERVAL_MINUTES` | Schedule tuning |

### Legacy Files

`bot.py`, `config.py`, and `db.py` at the repo root are legacy entry points kept for backward compatibility. The canonical application lives entirely under `app/`.

### Testing

All tests mock external HTTP calls — no internet access required. Tests live in `tests/unit/`. The `tests/integration/` directory is a placeholder for future work.
