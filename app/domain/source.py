from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class SourceType(StrEnum):
    PRIMARY = "PRIMARY"
    NEWS_AGENCY = "NEWS_AGENCY"
    MAJOR_OUTLET = "MAJOR_OUTLET"
    SPECIALIST_OUTLET = "SPECIALIST_OUTLET"
    DISCOVERY_ONLY = "DISCOVERY_ONLY"


class CredibilityTier(StrEnum):
    TIER_1 = "TIER_1"
    TIER_2 = "TIER_2"
    TIER_3 = "TIER_3"
    DISCOVERY = "DISCOVERY"


@dataclass(slots=True)
class Source:
    name: str
    domain: str
    source_type: SourceType
    credibility_tier: CredibilityTier
    language: str
    country_or_region: str
    rss_url: str | None = None
    enabled: bool = True
    id: int | None = None
