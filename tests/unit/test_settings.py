from app.settings import Settings


def test_simple_trusted_source_flow_defaults_enabled(monkeypatch):
    monkeypatch.delenv("EXTERNAL_DELIVERY_APPROVAL_REQUIRED", raising=False)
    monkeypatch.delenv("AUTO_PUBLISH_TRUSTED_SOURCES", raising=False)
    monkeypatch.delenv("TRUSTED_SOURCES_ONLY", raising=False)
    monkeypatch.delenv("TELEGRAM_CHANNEL_ID", raising=False)
    monkeypatch.delenv("CHANNEL_TOPIC_KEYS", raising=False)
    monkeypatch.delenv("CHANNEL_DELIVERY_ENABLED", raising=False)

    settings = Settings.from_env()

    assert not settings.external_delivery_approval_required
    assert settings.auto_publish_trusted_sources
    assert settings.trusted_sources_only
    assert settings.telegram_channel_id is None
    assert settings.channel_topic_keys == ()
    assert settings.channel_output_language == "en"
    assert not settings.channel_delivery_enabled
    assert settings.channel_delivery_interval_minutes == 10
    assert settings.channel_max_articles_per_run == 3


def test_channel_delivery_settings(monkeypatch):
    monkeypatch.setenv("TELEGRAM_CHANNEL_ID", "@factlens")
    monkeypatch.setenv("CHANNEL_TOPIC_KEYS", "china, diplomacy,global-trade")
    monkeypatch.setenv("CHANNEL_OUTPUT_LANGUAGE", "bn")
    monkeypatch.setenv("CHANNEL_DELIVERY_ENABLED", "true")
    monkeypatch.setenv("CHANNEL_DELIVERY_INTERVAL_MINUTES", "5")
    monkeypatch.setenv("CHANNEL_MAX_ARTICLES_PER_RUN", "2")

    settings = Settings.from_env()

    assert settings.telegram_channel_id == "@factlens"
    assert settings.channel_topic_keys == ("china", "diplomacy", "global-trade")
    assert settings.channel_output_language == "bn"
    assert settings.channel_delivery_enabled
    assert settings.channel_delivery_interval_minutes == 5
    assert settings.channel_max_articles_per_run == 2
