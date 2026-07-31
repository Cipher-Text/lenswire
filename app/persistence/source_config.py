from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]

REQUIRED_SOURCE_FIELDS = {
    "name",
    "domain",
    "source_type",
    "credibility_tier",
    "language",
    "country_or_region",
}


def load_source_config(path: Path | str) -> list[dict[str, Any]]:
    source_path = Path(path)
    if not source_path.exists():
        return []

    data = yaml.safe_load(source_path.read_text()) or {}
    sources = data.get("sources", [])
    if not isinstance(sources, list):
        raise ValueError("source config must contain a list named 'sources'")

    normalized: list[dict[str, Any]] = []
    for index, source in enumerate(sources, start=1):
        if not isinstance(source, dict):
            raise ValueError(f"source #{index} must be an object")
        missing = REQUIRED_SOURCE_FIELDS - set(source)
        if missing:
            raise ValueError(f"source #{index} missing required fields: {sorted(missing)}")
        normalized.append(
            {
                "name": str(source["name"]),
                "domain": str(source["domain"]).lower().removeprefix("www."),
                "source_type": str(source["source_type"]),
                "credibility_tier": str(source["credibility_tier"]),
                "language": str(source["language"]),
                "country_or_region": str(source["country_or_region"]),
                "rss_url": source.get("rss_url") or None,
                "enabled": bool(source.get("enabled", True)),
            }
        )
    return normalized
