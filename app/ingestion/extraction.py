from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass

from app.domain.article import ExtractionStatus

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class ExtractionResult:
    content: str
    status: ExtractionStatus
    error: str | None = None


PROHIBITED_DOMAINS: set[str] = set()


def _extract_blocking(url: str, html: str | None = None) -> ExtractionResult:
    try:
        import trafilatura
    except Exception as exc:  # pragma: no cover - dependency availability branch
        return ExtractionResult("", ExtractionStatus.FAILED, f"trafilatura unavailable: {exc}")

    try:
        downloaded = html if html is not None else trafilatura.fetch_url(url)
        if not downloaded:
            return ExtractionResult("", ExtractionStatus.FAILED, "empty fetch")
        content = (
            trafilatura.extract(downloaded, include_comments=False, include_tables=False) or ""
        )
        if not content.strip():
            return ExtractionResult("", ExtractionStatus.FAILED, "no article content extracted")
        return ExtractionResult(content.strip(), ExtractionStatus.SUCCESS)
    except Exception as exc:
        logger.warning("article extraction failed", extra={"url": url, "error": str(exc)})
        return ExtractionResult("", ExtractionStatus.FAILED, str(exc))


async def extract_article_content(url: str, html: str | None = None) -> ExtractionResult:
    return await asyncio.to_thread(_extract_blocking, url, html)
