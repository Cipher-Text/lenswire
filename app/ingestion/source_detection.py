from __future__ import annotations

from app.domain.source import Source, SourceType
from app.ingestion.normalization import domain_from_url
from app.persistence.repositories import Repository


def identify_main_source(
    repo: Repository, article_url: str, discovery_source: str = ""
) -> Source | None:
    domain = domain_from_url(article_url)
    source = repo.find_source_by_domain(domain)
    if source and source.source_type != SourceType.DISCOVERY_ONLY:
        return source
    if discovery_source:
        discovery = repo.find_source_by_domain(discovery_source)
        if discovery and discovery.source_type != SourceType.DISCOVERY_ONLY:
            return discovery
    return None
