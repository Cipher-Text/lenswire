from __future__ import annotations

import asyncio

from app.ingestion.rss import fetch_rss_feed
from app.persistence.migrations import migrate
from app.persistence.repositories import Repository
from app.settings import settings


async def _fetch_all_articles_async(query=None):
    migrate(settings.database_path)
    repo = Repository(settings.database_path)
    articles = []
    for source in repo.list_sources():
        if not source.rss_url:
            continue
        for entry in await fetch_rss_feed(source.rss_url, settings.source_fetch_timeout_seconds):
            articles.append(
                {
                    "title": entry["title"],
                    "description": entry["description"],
                    "url": entry["url"],
                    "source": entry["source"],
                }
            )
    return articles


def fetch_all_articles(query=None):
    return asyncio.run(_fetch_all_articles_async(query))
