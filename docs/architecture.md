# Architecture

Lenswire is a modular monolith. Telegram polling, ingestion, matching, summarization, optional editorial workflow, delivery and persistence run in one deployable Python application.

The main boundaries are:

- `app/bot`: Telegram application, handlers, permissions, keyboards and message text.
- `app/ingestion`: RSS/API discovery, URL normalization, source identification, article extraction and duplicate detection (content-hash + near-duplicate headline checks).
- `app/matching`: keyword-based topic classification, used as fallback when AI classification is disabled or returns no results.
- `app/summarization`: provider interface, deterministic fallback, OpenRouter backend, Gemini backend and OpenRouter-first/Gemini failover routing.
- `app/editorial`: approval, rejection and saved-story workflow.
- `app/delivery`: safe Telegram formatting, user delivery helpers and channel delivery-history logic.
- `app/persistence`: SQLite connection handling, migrations and repositories.
- `app/domain`: small dataclasses and enums shared across modules.

SQLite is retained for the pilot and isolated behind repositories so PostgreSQL can be introduced later without changing Telegram handlers.

The editable source registry lives at `config/sources.yaml` and is synced into SQLite at startup.

When `SUMMARY_PROVIDER=ai`, the summarization prompt also asks the model to classify the article against the known topic list and return `matched_topics`. The pipeline uses these AI-assigned topics instead of keyword matching. Keyword matching remains the fallback when AI is disabled or the model returns an empty topic list.

Channel publishing is a scheduled delivery path, not a separate ingestion path. It uses the same trusted-source ingestion and topic classification as the bot, then filters stories by fixed `CHANNEL_TOPIC_KEYS` before posting to the configured Telegram channel.
