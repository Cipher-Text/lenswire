from app.settings import Settings


def test_simple_trusted_source_flow_defaults_enabled(monkeypatch):
    monkeypatch.delenv("EXTERNAL_DELIVERY_APPROVAL_REQUIRED", raising=False)
    monkeypatch.delenv("AUTO_PUBLISH_TRUSTED_SOURCES", raising=False)
    monkeypatch.delenv("TRUSTED_SOURCES_ONLY", raising=False)

    settings = Settings.from_env()

    assert not settings.external_delivery_approval_required
    assert settings.auto_publish_trusted_sources
    assert settings.trusted_sources_only
