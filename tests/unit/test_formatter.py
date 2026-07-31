from app.delivery.formatter import format_editorial_message, format_external_message


def test_formatter_escapes_html():
    row = {
        "original_headline": "<b>Bad</b>",
        "summary": "A & B",
        "why_it_matters": "C < D",
        "source_name": "Reuters",
        "publication_time": None,
        "canonical_url": "https://example.com/?a=1&b=2",
        "topics": "China",
        "verification_status": "SINGLE_SOURCE",
        "editorial_angle": "Watch <closely>",
    }
    message = format_editorial_message(row)
    assert "&lt;b&gt;Bad&lt;/b&gt;" in message
    assert "Watch &lt;closely&gt;" in message
    assert 'href="https://example.com/?a=1&amp;b=2"' in message


def test_external_message_excludes_editorial_angle():
    row = {
        "original_headline": "Title",
        "editorial_angle": "Internal",
        "canonical_url": "https://x.test",
    }
    assert "Internal" not in format_external_message(row)
