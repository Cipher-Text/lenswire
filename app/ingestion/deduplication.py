from __future__ import annotations

from difflib import SequenceMatcher

from app.ingestion.normalization import normalize_title, normalize_url


def exact_duplicate_key(url: str) -> str:
    return normalize_url(url)


def titles_are_near_duplicates(left: str, right: str, threshold: float = 0.88) -> bool:
    left_norm = normalize_title(left)
    right_norm = normalize_title(right)
    if not left_norm or not right_norm:
        return False
    return SequenceMatcher(None, left_norm, right_norm).ratio() >= threshold
