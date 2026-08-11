import pytest

from app.domain.article import Article, VerificationStatus
from app.summarization.deterministic import DeterministicSummaryProvider


@pytest.mark.asyncio
async def test_deterministic_summary_uses_article_content():
    article = Article(
        original_headline="Headline",
        original_url="https://example.com/a",
        canonical_url="https://example.com/a",
        source_name="Reuters",
        extracted_content=(
            "First sentence. Second sentence. Third sentence. Fourth sentence. Fifth sentence."
        ),
    )
    summary = await DeterministicSummaryProvider().summarize(article)
    assert "First sentence." in summary.summary
    assert "Fifth sentence." not in summary.summary
    assert summary.verification_status == VerificationStatus.SINGLE_SOURCE


@pytest.mark.asyncio
async def test_deterministic_bangla_fallback_uses_bangla_metadata():
    article = Article(
        original_headline="Headline",
        original_url="https://example.com/a",
        canonical_url="https://example.com/a",
        source_name="Reuters",
        raw_description="English source sentence.",
    )

    summary = await DeterministicSummaryProvider("bn").summarize(article)

    assert "সরকারি প্রতিক্রিয়া" in summary.editorial_angle
    assert summary.language == "bn"
