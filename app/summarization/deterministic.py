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

    async def summarize(self, article: Article) -> ArticleSummary:
        basis = article.extracted_content or article.raw_description or article.original_headline
        selected = _sentences(basis)[:4]
        if not selected:
            selected = [article.original_headline]
        summary = " ".join(selected)
        topic_hint = "the balance of power, diplomatic positioning or economic exposure"
        why = (
            f"This story matters because it may affect {topic_hint} connected to "
            f"{article.source_name or 'the reporting source'}."
        )
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
            why_it_matters=why,
            editorial_angle=angle,
            verification_status=status,
            language=self.language,
            provider=self.name,
        )
