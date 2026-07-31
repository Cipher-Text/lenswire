from app.ingestion.normalization import domain_from_url, normalize_title, normalize_url


def test_normalize_url_removes_tracking_and_www():
    assert (
        normalize_url("HTTPS://www.Example.com/path/?utm_source=x&b=2&a=1#frag")
        == "https://example.com/path?a=1&b=2"
    )


def test_normalize_title():
    assert normalize_title("  China: New Export Controls! ") == "china new export controls"


def test_domain_from_url():
    assert domain_from_url("https://www.reuters.com/world/") == "reuters.com"
