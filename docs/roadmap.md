# Lenswire Roadmap

Lenswire is being built as a modular monolith so the internal pilot can stay simple while leaving clear boundaries for later scale.

## Phase 1: Foundation

- Create the `app/` package structure.
- Move configuration into a validated settings object.
- Add `.env.example` and `.gitignore` entries for secrets, local databases, model caches, logs and virtual environments.
- Add domain models for users, topics, sources, articles, summaries and editorial workflow.
- Introduce repository interfaces over SQLite.
- Add migrations that preserve the legacy `users` and `sent_articles` tables.

## Phase 2: Ingestion

- Seed a source registry with trusted geopolitical sources.
- Normalize URLs and identify the main publisher separately from the discovery source.
- Extract article metadata and content with graceful failure statuses.
- Add language detection, content hashing, duplicate detection and source-level failure isolation.
- Store fetched articles once per ingestion cycle and avoid per-user source fetches.

## Phase 3: Editorial Intelligence

- Seed curated FactLens geopolitical topics.
- Replace unrestricted interests with topic subscriptions while retaining legacy interest strings.
- Classify stories under curated topics.
- Generate structured summary fields: `summary`, `why_it_matters`, `editorial_angle` and `verification_status`.
- Add deterministic summarization and an optional provider abstraction for AI summarization.
- Add basic story clustering and supporting-source matching.

## Phase 4: Telegram Workflows

- Add editorial authorization through environment-configured Telegram IDs.
- Add editorial review queue commands and actions for save, approve and reject.
- Add external topic subscription commands, language preferences, quiet hours, stop and delete account flows.
- Format messages with safely escaped Telegram HTML.
- Support the default simple trusted-source flow while preserving optional approval-gated delivery.

## Phase 5: Quality and Operations

- Add unit and integration tests that mock external HTTP and embedding providers.
- Add Ruff, formatting, type checking and CI.
- Add Docker and Docker Compose deployment files with persistent SQLite/model-cache volumes.
- Add structured logging, timeouts, retries, ingestion locking, graceful shutdown and failed-delivery recording.

## Current Implementation Limits

- Initial deterministic summarization is extractive and can miss nuance.
- Optional AI summarization supports OpenRouter first, then Gemini fallback.
- Supporting-source and primary-source detection are heuristic.
- Single-source stories are not treated as verified.
- Human editorial review is optional in the default flow, but still recommended before high-stakes public distribution.
