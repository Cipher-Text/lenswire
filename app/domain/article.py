from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum


class ArticleStatus(StrEnum):
    NEW = "NEW"
    REVIEW_PENDING = "REVIEW_PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"


class ExtractionStatus(StrEnum):
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    SKIPPED_PROHIBITED = "SKIPPED_PROHIBITED"


class VerificationStatus(StrEnum):
    UNREVIEWED = "UNREVIEWED"
    SINGLE_SOURCE = "SINGLE_SOURCE"
    MULTI_SOURCE = "MULTI_SOURCE"
    PRIMARY_SOURCE_FOUND = "PRIMARY_SOURCE_FOUND"
    EDITOR_APPROVED = "EDITOR_APPROVED"
    REJECTED = "REJECTED"
    DISPUTED = "DISPUTED"


@dataclass(slots=True)
class Article:
    original_headline: str
    original_url: str
    canonical_url: str
    source_id: int | None = None
    source_name: str = ""
    discovery_source: str = ""
    author: str | None = None
    publication_time: datetime | None = None
    fetched_time: datetime = field(default_factory=lambda: datetime.now(UTC))
    language: str = "unknown"
    raw_description: str = ""
    extracted_content: str = ""
    normalized_title: str = ""
    content_hash: str = ""
    status: ArticleStatus = ArticleStatus.NEW
    extraction_status: ExtractionStatus = ExtractionStatus.PENDING


@dataclass(slots=True)
class ArticleSummary:
    article_id: int | None
    summary: str
    editorial_angle: str
    verification_status: VerificationStatus
    language: str = "en"
    provider: str = "deterministic"
    status: str = "SUCCESS"
    matched_topics: list[str] = field(default_factory=list)
