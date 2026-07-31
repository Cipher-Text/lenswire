from app.domain.article import Article
from app.persistence.migrations import migrate
from app.persistence.repositories import Repository
from app.summarization.deterministic import DeterministicSummaryProvider


def test_subscription_review_and_delivery_flow(tmp_path):
    db = tmp_path / "test.sqlite3"
    migrate(db)
    repo = Repository(db)
    repo.upsert_user(1)
    assert repo.subscribe(1, "china")
    article_id = repo.upsert_article(
        Article(
            original_headline="China trade talks",
            original_url="https://reuters.com/a",
            canonical_url="https://reuters.com/a",
            source_name="Reuters",
        )
    )
    repo.set_article_topics(article_id, [("china", 0.9)])
    import asyncio

    summary = asyncio.run(
        DeterministicSummaryProvider().summarize(
            Article(
                "China trade talks",
                "https://reuters.com/a",
                "https://reuters.com/a",
                source_name="Reuters",
            )
        )
    )
    repo.save_summary(article_id, summary)
    assert repo.latest_for_topics(["china"], 5, approved_only=True) == []
    repo.review(article_id, 99, "APPROVE")
    assert len(repo.latest_for_topics(["china"], 5, approved_only=True)) == 1
    repo.record_delivery(1, article_id)
    assert repo.was_delivered(1, article_id)
