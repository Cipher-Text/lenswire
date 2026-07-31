from app.ingestion.deduplication import exact_duplicate_key, titles_are_near_duplicates


def test_exact_duplicate_key():
    assert (
        exact_duplicate_key("https://www.example.com/a?utm_campaign=x") == "https://example.com/a"
    )


def test_near_duplicate_titles():
    assert titles_are_near_duplicates(
        "China announces new strategic export controls",
        "China announces strategic export controls",
        threshold=0.75,
    )
