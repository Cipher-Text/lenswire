# Architecture

Lenswire is a modular monolith. Telegram polling, ingestion, matching, summarization, optional editorial workflow, delivery and persistence run in one deployable Python application.

The main boundaries are:

- `app/bot`: Telegram application, handlers, permissions, keyboards and message text.
- `app/ingestion`: RSS/API discovery, URL normalization, source identification and article extraction.
- `app/matching`: curated topic classification, embeddings and story similarity helpers.
- `app/summarization`: provider interface, deterministic fallback, OpenRouter backend, Gemini backend and OpenRouter-first/Gemini failover routing.
- `app/editorial`: approval, rejection and saved-story workflow.
- `app/delivery`: safe Telegram formatting and delivery-history logic.
- `app/persistence`: SQLite connection handling, migrations and repositories.
- `app/domain`: small dataclasses and enums shared across modules.

SQLite is retained for the pilot and isolated behind repositories so PostgreSQL can be introduced later without changing Telegram handlers.

The editable source registry lives at `config/sources.yaml` and is synced into SQLite at startup.
