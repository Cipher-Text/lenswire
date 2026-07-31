from __future__ import annotations

import asyncio
import email.utils
import logging
from datetime import UTC, datetime

import feedparser
import httpx

from app.domain.article import Article, ArticleStatus, ExtractionStatus
from app.ingestion.extraction import extract_article_content
from app.ingestion.normalization import domain_from_url, normalize_title, normalize_url
from app.ingestion.source_detection import identify_main_source
from app.persistence.repositories import Repository, stable_content_hash

logger = logging.getLogger(__name__)


def _parse_date(value: str | None) -> datetime | None:
    if not value:
        return None
    parsed = email.utils.parsedate_to_datetime(value)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


async def fetch_rss_feed(url: str, timeout: float) -> list[dict]:
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
        response = await client.get(url)
        response.raise_for_status()
    parsed = await asyncio.to_thread(feedparser.parse, response.text)
    source_name = parsed.feed.get("title", domain_from_url(url))
    entries: list[dict] = []
    for entry in parsed.entries[:20]:
        entries.append(
            {
                "title": entry.get("title", ""),
                "description": entry.get("summary", ""),
                "url": entry.get("link", ""),
                "source": source_name,
                "published": entry.get("published") or entry.get("updated"),
                "author": entry.get("author"),
            }
        )
    return entries


async def discover_rss_articles(
    repo: Repository,
    timeout: float,
    extract_content: bool = True,
    auto_publish: bool = False,
) -> list[tuple[int, Article]]:
    sources = [source for source in repo.list_sources() if source.rss_url]
    discovered: list[tuple[int, Article]] = []
    for source in sources:
        try:
            entries = await fetch_rss_feed(source.rss_url or "", timeout)
        except Exception as exc:
            logger.warning("rss source failed", extra={"source": source.name, "error": str(exc)})
            continue
        for entry in entries:
            if not entry["url"] or not entry["title"]:
                continue
            canonical_url = normalize_url(entry["url"])
            main_source = identify_main_source(repo, canonical_url, source.domain) or source
            extraction = await extract_article_content(canonical_url) if extract_content else None
            content = extraction.content if extraction else ""
            extraction_status = extraction.status if extraction else ExtractionStatus.PENDING
            body_for_hash = content or entry.get("description", "") or entry["title"]
            article = Article(
                original_headline=entry["title"],
                original_url=entry["url"],
                canonical_url=canonical_url,
                source_id=main_source.id,
                source_name=main_source.name,
                discovery_source=source.name,
                author=entry.get("author"),
                publication_time=_parse_date(entry.get("published")),
                raw_description=entry.get("description", ""),
                extracted_content=content,
                normalized_title=normalize_title(entry["title"]),
                content_hash=stable_content_hash(body_for_hash),
                status=ArticleStatus.APPROVED if auto_publish else ArticleStatus.NEW,
                extraction_status=extraction_status,
            )
            article_id = repo.upsert_article(article)
            discovered.append((article_id, article))
    return discovered
