from __future__ import annotations

from difflib import SequenceMatcher

from app.settings import settings

SIMILARITY_THRESHOLD = settings.similarity_threshold


def match_articles(interests, articles, threshold=SIMILARITY_THRESHOLD):
    matches = []
    for article in articles:
        text = f"{article.get('title', '')} {article.get('description', '')}".lower()
        best_interest = ""
        best_score = 0.0
        for interest in interests:
            interest_text = interest.lower().strip()
            score = (
                1.0
                if interest_text and interest_text in text
                else SequenceMatcher(None, interest_text, text).ratio()
            )
            if score > best_score:
                best_interest = interest
                best_score = score
        if best_score >= threshold:
            matches.append(
                {**article, "matched_interest": best_interest, "score": round(best_score, 3)}
            )
    return sorted(matches, key=lambda item: item["score"], reverse=True)
