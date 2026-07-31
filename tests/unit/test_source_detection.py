from app.ingestion.source_detection import identify_main_source
from app.persistence.migrations import migrate
from app.persistence.repositories import Repository


def test_identifies_publisher_not_discovery_source(tmp_path):
    db = tmp_path / "test.sqlite3"
    migrate(db)
    repo = Repository(db)
    source = identify_main_source(repo, "https://www.reuters.com/world/example", "news.google.com")
    assert source is not None
    assert source.name == "Reuters"
