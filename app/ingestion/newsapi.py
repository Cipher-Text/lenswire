from __future__ import annotations

import logging
from datetime import UTC, datetime

import httpx

from app.domain.article import Article, ArticleStatus, ExtractionStatus
from app.ingestion.deduplication import titles_are_near_duplicates
from app.ingestion.extraction import extract_article_content
from app.ingestion.normalization import normalize_title, normalize_url
from app.ingestion.source_detection import identify_main_source
from app.persistence.repositories import Repository, stable_content_hash

logger = logging.getLogger(__name__)


def _parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)


async def fetch_newsapi_articles(
    repo: Repository,
    api_key: str | None,
    timeout: float,
    query: str | None = None,
    extract_content: bool = True,
    trusted_sources_only: bool = True,
    auto_publish: bool = False,
) -> list[tuple[int, Article]]:
    if not api_key:
        return []
    endpoint = (
        "https://newsapi.org/v2/everything" if query else "https://newsapi.org/v2/top-headlines"
    )
    params: dict[str, str | int] = {
        "apiKey": api_key,
        "language": "en",
        "pageSize": 50,
    }
    if query:
        params.update({"q": query, "sortBy": "publishedAt"})
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
        response = await client.get(endpoint, params=params)
        response.raise_for_status()
    output: list[tuple[int, Article]] = []
    recent_titles = repo.recent_normalized_titles()
    for item in response.json().get("articles", []):
        title = item.get("title") or ""
        url = item.get("url") or ""
        if not title or not url:
            continue
        canonical_url = normalize_url(url)
        source_name = (item.get("source") or {}).get("name") or "NewsAPI"
        main_source = identify_main_source(repo, canonical_url, source_name)
        if trusted_sources_only and main_source is None:
            logger.info(
                "skipping unregistered NewsAPI publisher",
                extra={"url": canonical_url, "source": source_name},
            )
            continue
        extraction = await extract_article_content(canonical_url) if extract_content else None
        content = extraction.content if extraction else ""
        content_hash = stable_content_hash(content or item.get("description") or title)
        norm_title = normalize_title(title)
        if repo.article_exists_by_content_hash(content_hash):
            logger.debug(
                "skipping content-hash duplicate",
                extra={"url": canonical_url, "source": source_name},
            )
            continue
        if any(titles_are_near_duplicates(norm_title, t) for t in recent_titles):
            logger.debug(
                "skipping near-duplicate headline",
                extra={"url": canonical_url, "title": title},
            )
            continue
        article = Article(
            original_headline=title,
            original_url=url,
            canonical_url=canonical_url,
            source_id=main_source.id if main_source else None,
            source_name=main_source.name if main_source else source_name,
            discovery_source="NewsAPI",
            author=item.get("author"),
            publication_time=_parse_iso(item.get("publishedAt")),
            raw_description=item.get("description") or "",
            extracted_content=content,
            normalized_title=norm_title,
            content_hash=content_hash,
            status=ArticleStatus.APPROVED if auto_publish else ArticleStatus.NEW,
            extraction_status=extraction.status if extraction else ExtractionStatus.PENDING,
        )
        article_id = repo.upsert_article(article)
        recent_titles.append(norm_title)
        output.append((article_id, article))
    return output
