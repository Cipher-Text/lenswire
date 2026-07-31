from app.persistence.migrations import migrate
from app.persistence.repositories import Repository
from app.persistence.source_config import load_source_config


def test_load_source_config(tmp_path):
    config = tmp_path / "sources.yaml"
    config.write_text(
        """
sources:
  - name: Example News
    domain: www.example.com
    source_type: MAJOR_OUTLET
    credibility_tier: TIER_3
    language: en
    country_or_region: Global
    rss_url: https://example.com/rss
    enabled: false
"""
    )

    rows = load_source_config(config)

    assert rows == [
        {
            "name": "Example News",
            "domain": "example.com",
            "source_type": "MAJOR_OUTLET",
            "credibility_tier": "TIER_3",
            "language": "en",
            "country_or_region": "Global",
            "rss_url": "https://example.com/rss",
            "enabled": False,
        }
    ]


def test_migration_syncs_source_config_updates(tmp_path):
    db = tmp_path / "test.sqlite3"
    config = tmp_path / "sources.yaml"
    config.write_text(
        """
sources:
  - name: Example News
    domain: example.com
    source_type: MAJOR_OUTLET
    credibility_tier: TIER_3
    language: en
    country_or_region: Global
    rss_url: https://example.com/old.xml
    enabled: true
"""
    )
    migrate(db, config)

    config.write_text(
        """
sources:
  - name: Example News Updated
    domain: example.com
    source_type: SPECIALIST_OUTLET
    credibility_tier: TIER_3
    language: en
    country_or_region: Global
    rss_url: https://example.com/new.xml
    enabled: false
"""
    )
    migrate(db, config)

    source = Repository(db).find_source_by_domain("example.com")

    assert source is not None
    assert source.name == "Example News Updated"
    assert source.rss_url == "https://example.com/new.xml"
    assert not source.enabled
