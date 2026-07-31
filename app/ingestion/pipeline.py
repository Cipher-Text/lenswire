from __future__ import annotations

import logging

from app.ingestion.newsapi import fetch_newsapi_articles
from app.ingestion.rss import discover_rss_articles
from app.matching.embeddings import EmbeddingProvider
from app.matching.topics import keyword_topic_matches, semantic_topic_matches
from app.persistence.repositories import Repository
from app.settings import Settings
from app.summarization.ai_provider import OptionalAISummaryProvider
from app.summarization.base import SummaryProvider
from app.summarization.deterministic import DeterministicSummaryProvider

logger = logging.getLogger(__name__)


class IngestionPipeline:
    def __init__(
        self,
        settings: Settings,
        repo: Repository,
        embedding_provider: EmbeddingProvider | None = None,
    ) -> None:
        self.settings = settings
        self.repo = repo
        self.embedding_provider = embedding_provider
        if settings.summary_provider == "ai":
            self.summary_provider: SummaryProvider = OptionalAISummaryProvider(settings)
        else:
            self.summary_provider = DeterministicSummaryProvider(settings.summary_output_language)

    async def run(self, query: str | None = None, extract_content: bool = True) -> int:
        discovered = []
        discovered.extend(
            await discover_rss_articles(
                self.repo,
                self.settings.source_fetch_timeout_seconds,
                extract_content=extract_content,
                auto_publish=self.settings.auto_publish_trusted_sources,
            )
        )
        discovered.extend(
            await fetch_newsapi_articles(
                self.repo,
                self.settings.newsapi_key,
                self.settings.source_fetch_timeout_seconds,
                query=query,
                extract_content=extract_content,
                trusted_sources_only=self.settings.trusted_sources_only,
                auto_publish=self.settings.auto_publish_trusted_sources,
            )
        )
        topics = self.repo.list_topics()
        for article_id, article in discovered:
            matches = keyword_topic_matches(article, topics)
            if not matches and self.embedding_provider:
                try:
                    matches = await semantic_topic_matches(
                        article,
                        topics,
                        self.embedding_provider,
                        self.settings.similarity_threshold,
                    )
                except Exception as exc:
                    logger.warning(
                        "semantic topic matching failed; continuing without embeddings",
                        extra={"article_url": article.canonical_url, "error": str(exc)},
                    )
            self.repo.set_article_topics(
                article_id, [(match.topic_key, match.score) for match in matches]
            )
            summary = await self.summary_provider.summarize(article)
            self.repo.save_summary(article_id, summary)
        logger.info("ingestion cycle complete", extra={"article_count": len(discovered)})
        return len(discovered)
