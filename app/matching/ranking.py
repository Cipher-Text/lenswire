from __future__ import annotations


def rank_articles(rows: list[dict]) -> list[dict]:
    return sorted(
        rows,
        key=lambda row: row.get("publication_time") or row.get("fetched_time") or "",
        reverse=True,
    )
