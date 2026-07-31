from app.domain.article import Article
from app.matching.topics import keyword_topic_matches
from app.persistence.migrations import migrate
from app.persistence.repositories import Repository


def test_keyword_topic_classification(tmp_path):
    db = tmp_path / "test.sqlite3"
    migrate(db)
    topics = Repository(db).list_topics()
    article = Article(
        original_headline="China announces chip export controls after US talks",
        original_url="https://example.com/a",
        canonical_url="https://example.com/a",
        raw_description="The move affects semiconductor supply chains and US-China relations.",
    )
    keys = {match.topic_key for match in keyword_topic_matches(article, topics)}
    assert "china" in keys
    assert "semiconductors" in keys
