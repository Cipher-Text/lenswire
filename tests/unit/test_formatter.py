from app.delivery.formatter import (
    format_channel_message,
    format_editorial_message,
    format_external_message,
)


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


def test_channel_message_uses_bangla_labels_and_topics():
    row = {
        "original_headline": "China trade talks",
        "summary": "বাংলা সারসংক্ষেপ &amp; বিশ্লেষণ",
        "why_it_matters": "বাংলা গুরুত্ব",
        "source_name": "Reuters",
        "publication_time": None,
        "canonical_url": "https://example.com",
        "topics": "China",
        "bangla_topics": "চীন",
    }

    message = format_channel_message(row, "bn")

    assert "চীন" in message
    assert "China trade talks" not in message
    assert "<b>সারসংক্ষেপ:</b>" in message
    assert "<b>কেন গুরুত্বপূর্ণ:</b>" in message
    assert "<b>সূত্র:</b>" in message
    assert "বাংলা সারসংক্ষেপ &amp; বিশ্লেষণ" in message


def test_channel_message_replaces_english_fallback_text_in_bangla_mode():
    row = {
        "summary": "Typhoon Dolphin has made landfall in eastern China.",
        "why_it_matters": "This story matters because it may affect diplomacy.",
        "source_name": "BBC News",
        "publication_time": None,
        "canonical_url": "https://example.com",
        "topics": "China",
        "bangla_topics": "চীন",
    }

    message = format_channel_message(row, "bn")

    assert "Typhoon Dolphin" not in message
    assert "This story matters" not in message
    assert "চীন বিষয়ে BBC News-এর একটি সাম্প্রতিক প্রতিবেদন" in message
    assert "এই খবরটি গুরুত্বপূর্ণ" in message
