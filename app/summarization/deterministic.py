from __future__ import annotations

import re

from app.domain.article import Article, ArticleSummary, VerificationStatus


def _sentences(text: str) -> list[str]:
    clean = re.sub(r"\s+", " ", text).strip()
    if not clean:
        return []
    return [part.strip() for part in re.split(r"(?<=[.!?])\s+", clean) if part.strip()]


class DeterministicSummaryProvider:
    name = "deterministic"

    def __init__(self, language: str = "en") -> None:
        self.language = language

    async def summarize(self, article: Article, topic_keys: tuple[str, ...] = ()) -> ArticleSummary:
        basis = article.extracted_content or article.raw_description or article.original_headline
        selected = _sentences(basis)[:4]
        if not selected:
            selected = [article.original_headline]
        summary = " ".join(selected)
        if self.language == "bn":
            angle = (
                "সরকারি প্রতিক্রিয়া, আঞ্চলিক অবস্থান এবং স্বাধীন সূত্রে তথ্যটি "
                "সমর্থিত হচ্ছে কি না তা নজরে রাখা জরুরি।"
            )
        else:
            angle = (
                "Track official responses, regional reactions and whether additional sources "
                "corroborate the report."
            )
        status = (
            VerificationStatus.SINGLE_SOURCE
            if article.source_name
            else VerificationStatus.UNREVIEWED
        )
        return ArticleSummary(
            article_id=None,
            summary=summary,
            editorial_angle=angle,
            verification_status=status,
            language=self.language,
            provider=self.name,
        )
