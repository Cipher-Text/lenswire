from __future__ import annotations

from app.ingestion.deduplication import titles_are_near_duplicates


def likely_same_story(title: str, candidate_title: str) -> bool:
    return titles_are_near_duplicates(title, candidate_title, threshold=0.84)
