from __future__ import annotations

from typing import Protocol

from app.domain.article import Article, ArticleSummary


class SummaryProvider(Protocol):
    async def summarize(
        self, article: Article, topic_keys: tuple[str, ...] = ()
    ) -> ArticleSummary: ...
