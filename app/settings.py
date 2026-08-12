from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _int(value: str | None, default: int) -> int:
    if value is None or value == "":
        return default
    return int(value)


def _float(value: str | None, default: float) -> float:
    if value is None or value == "":
        return default
    return float(value)


def _csv_ints(value: str | None) -> set[int]:
    if not value:
        return set()
    return {int(part.strip()) for part in value.split(",") if part.strip()}


def _csv_strings(value: str | None) -> tuple[str, ...]:
    if not value:
        return ()
    return tuple(part.strip() for part in value.split(",") if part.strip())


@dataclass(frozen=True, slots=True)
class Settings:
    telegram_bot_token: str
    newsapi_key: str | None
    database_path: Path
    source_config_path: Path
    editorial_telegram_ids: set[int]
    ingestion_interval_minutes: int
    delivery_interval_minutes: int
    similarity_threshold: float
    source_fetch_timeout_seconds: float
    max_articles_per_delivery: int
    summary_provider: str
    summary_output_language: str
    ai_provider: str
    ai_provider_order: str
    ai_request_timeout_seconds: float
    openrouter_api_key: str | None
    openrouter_api_base_url: str
    openrouter_model: str
    gemini_api_key: str | None
    gemini_api_base_url: str
    gemini_model: str
    article_cache_duration_minutes: int
    external_delivery_enabled: bool
    external_delivery_approval_required: bool
    auto_publish_trusted_sources: bool
    trusted_sources_only: bool
    telegram_channel_id: str | None
    channel_topic_keys: tuple[str, ...]
    channel_output_language: str
    channel_delivery_enabled: bool
    channel_delivery_interval_minutes: int
    channel_max_articles_per_run: int
    log_level: str
    manual_refresh_cooldown_seconds: int
    retention_delivery_history_days: int

    @classmethod
    def from_env(cls) -> Settings:
        return cls(
            telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN", ""),
            newsapi_key=os.getenv("NEWSAPI_KEY") or None,
            database_path=Path(os.getenv("DATABASE_PATH", "data/lenswire.sqlite3")),
            source_config_path=Path(os.getenv("SOURCE_CONFIG_PATH", "config/sources.yaml")),
            editorial_telegram_ids=_csv_ints(os.getenv("EDITORIAL_TELEGRAM_IDS")),
            ingestion_interval_minutes=_int(os.getenv("INGESTION_INTERVAL_MINUTES"), 30),
            delivery_interval_minutes=_int(os.getenv("DELIVERY_INTERVAL_MINUTES"), 30),
            similarity_threshold=_float(os.getenv("SIMILARITY_THRESHOLD"), 0.35),
            source_fetch_timeout_seconds=_float(os.getenv("SOURCE_FETCH_TIMEOUT_SECONDS"), 15.0),
            max_articles_per_delivery=_int(os.getenv("MAX_ARTICLES_PER_DELIVERY"), 5),
            summary_provider=os.getenv("SUMMARY_PROVIDER", "deterministic"),
            summary_output_language=os.getenv("SUMMARY_OUTPUT_LANGUAGE", "en"),
            ai_provider=os.getenv("AI_PROVIDER", "failover"),
            ai_provider_order=os.getenv("AI_PROVIDER_ORDER", "gemini,openrouter"),
            ai_request_timeout_seconds=_float(os.getenv("AI_REQUEST_TIMEOUT_SECONDS"), 30.0),
            openrouter_api_key=(os.getenv("OPENROUTER_API_KEY") or os.getenv("AI_API_KEY") or None),
            openrouter_api_base_url=os.getenv(
                "OPENROUTER_API_BASE_URL",
                os.getenv("AI_API_BASE_URL", "https://openrouter.ai/api/v1"),
            ),
            openrouter_model=os.getenv(
                "OPENROUTER_MODEL", os.getenv("AI_MODEL", "openrouter/free")
            ),
            gemini_api_key=os.getenv("GEMINI_API_KEY") or None,
            gemini_api_base_url=os.getenv(
                "GEMINI_API_BASE_URL", "https://generativelanguage.googleapis.com/v1beta"
            ),
            gemini_model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
            article_cache_duration_minutes=_int(os.getenv("ARTICLE_CACHE_DURATION_MINUTES"), 180),
            external_delivery_enabled=_bool(os.getenv("EXTERNAL_DELIVERY_ENABLED"), True),
            external_delivery_approval_required=_bool(
                os.getenv("EXTERNAL_DELIVERY_APPROVAL_REQUIRED"), False
            ),
            auto_publish_trusted_sources=_bool(os.getenv("AUTO_PUBLISH_TRUSTED_SOURCES"), True),
            trusted_sources_only=_bool(os.getenv("TRUSTED_SOURCES_ONLY"), True),
            telegram_channel_id=os.getenv("TELEGRAM_CHANNEL_ID") or None,
            channel_topic_keys=_csv_strings(os.getenv("CHANNEL_TOPIC_KEYS")),
            channel_output_language=os.getenv("CHANNEL_OUTPUT_LANGUAGE", "en"),
            channel_delivery_enabled=_bool(os.getenv("CHANNEL_DELIVERY_ENABLED"), False),
            channel_delivery_interval_minutes=_int(
                os.getenv("CHANNEL_DELIVERY_INTERVAL_MINUTES"), 30
            ),
            channel_max_articles_per_run=_int(os.getenv("CHANNEL_MAX_ARTICLES_PER_RUN"), 3),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            manual_refresh_cooldown_seconds=_int(os.getenv("MANUAL_REFRESH_COOLDOWN_SECONDS"), 180),
            retention_delivery_history_days=_int(os.getenv("RETENTION_DELIVERY_HISTORY_DAYS"), 90),
        )

    def validate_for_bot(self) -> None:
        if not self.telegram_bot_token or self.telegram_bot_token == "YOUR_TELEGRAM_BOT_TOKEN":
            raise ValueError("TELEGRAM_BOT_TOKEN is required")
        if self.summary_provider == "ai":
            ordered = [
                p.strip().lower() for p in self.ai_provider_order.split(",") if p.strip()
            ] or ["openrouter", "gemini"]
            has_key = any(
                (p == "openrouter" and self.openrouter_api_key)
                or (p == "gemini" and self.gemini_api_key)
                for p in ordered
            )
            if not has_key:
                raise ValueError(
                    "SUMMARY_PROVIDER=ai requires at least one AI API key "
                    "(OPENROUTER_API_KEY or GEMINI_API_KEY)"
                )


settings = Settings.from_env()
