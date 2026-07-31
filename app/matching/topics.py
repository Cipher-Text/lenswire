from __future__ import annotations

import re
from dataclasses import dataclass

from app.domain.article import Article
from app.domain.topic import Topic
from app.matching.embeddings import EmbeddingProvider, cosine_similarity

KEYWORD_HINTS = {
    "south-asia": {"south asia", "bangladesh", "india", "pakistan", "nepal", "sri lanka"},
    "bangladesh-foreign-policy": {"bangladesh", "dhaka", "foreign ministry", "foreign policy"},
    "india": {"india", "delhi", "modi"},
    "pakistan": {"pakistan", "islamabad"},
    "china": {"china", "beijing", "xi jinping"},
    "myanmar": {"myanmar", "burma", "naypyidaw"},
    "rohingya-rakhine": {"rohingya", "rakhine"},
    "middle-east": {"middle east", "gulf", "saudi", "qatar", "iraq", "syria"},
    "iran": {"iran", "tehran"},
    "israel-palestine": {"israel", "palestine", "gaza", "west bank", "hamas"},
    "turkey": {"turkey", "ankara", "erdogan"},
    "russia-ukraine": {"russia", "ukraine", "moscow", "kyiv"},
    "united-states": {"united states", "washington", "white house", "congress"},
    "european-union": {"european union", "brussels", "eu "},
    "us-china-relations": {
        "us-china",
        "u.s.-china",
        "washington and beijing",
        "united states and china",
    },
    "global-trade": {"trade", "tariff", "export", "import", "supply chain"},
    "strategic-minerals": {"lithium", "cobalt", "rare earth", "critical minerals"},
    "semiconductors": {"semiconductor", "chip", "chips", "tsmc", "asml"},
    "defence-security": {"defence", "defense", "military", "security", "missile"},
    "diplomacy": {"diplomacy", "diplomatic", "summit", "envoy", "talks"},
    "borders-nationalism": {"border", "nationalism", "sovereignty", "territory"},
    "climate-geopolitics": {"climate", "energy transition", "water security"},
}


@dataclass(slots=True)
class TopicMatch:
    topic_key: str
    score: float


def keyword_topic_matches(
    article: Article, topics: list[Topic], threshold: float = 0.2
) -> list[TopicMatch]:
    text = " ".join(
        [article.original_headline, article.raw_description, article.extracted_content[:2000]]
    ).lower()
    matches: list[TopicMatch] = []
    for topic in topics:
        hints = KEYWORD_HINTS.get(topic.key, set())
        score = sum(1 for hint in hints if re.search(rf"\b{re.escape(hint)}\b", text))
        if score:
            matches.append(TopicMatch(topic.key, min(1.0, threshold + score * 0.2)))
    matches.sort(key=lambda match: match.score, reverse=True)
    return matches[:5]


async def semantic_topic_matches(
    article: Article,
    topics: list[Topic],
    provider: EmbeddingProvider,
    threshold: float,
) -> list[TopicMatch]:
    article_text = ". ".join(
        [article.original_headline, article.raw_description, article.extracted_content[:3000]]
    )
    topic_texts = [f"{topic.english_name}. {topic.description or ''}".strip() for topic in topics]
    vectors = await provider.encode([article_text, *topic_texts])
    article_vector = vectors[0]
    matches = [
        TopicMatch(topic.key, cosine_similarity(article_vector, vector))
        for topic, vector in zip(topics, vectors[1:], strict=True)
    ]
    return sorted(
        (m for m in matches if m.score >= threshold), key=lambda m: m.score, reverse=True
    )[:5]
