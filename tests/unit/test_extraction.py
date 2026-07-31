import pytest

from app.domain.article import ExtractionStatus
from app.ingestion.extraction import extract_article_content


@pytest.mark.asyncio
async def test_extraction_failure_is_status(monkeypatch):
    import app.ingestion.extraction as extraction

    def fake_extract(_url, _html=None):
        return extraction.ExtractionResult("", ExtractionStatus.FAILED, "blocked")

    monkeypatch.setattr(extraction, "_extract_blocking", fake_extract)
    result = await extract_article_content("https://example.com")
    assert result.status == ExtractionStatus.FAILED
    assert result.error == "blocked"
