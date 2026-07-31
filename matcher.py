from sentence_transformers import SentenceTransformer, util

from config import EMBEDDING_MODEL, SIMILARITY_THRESHOLD

_model = None


def get_model():
    global _model
    if _model is None:
        # Downloads ~80MB on first run, then cached locally.
        _model = SentenceTransformer(EMBEDDING_MODEL)
    return _model


def match_articles(interests, articles, threshold=SIMILARITY_THRESHOLD):
    """
    interests: list[str], e.g. ["artificial intelligence", "football"]
    articles: list[dict] with at least 'title' and 'description'

    Returns matching articles (each tagged with matched_interest + score),
    sorted by score descending.
    """
    if not interests or not articles:
        return []

    model = get_model()
    interest_embeddings = model.encode(interests, convert_to_tensor=True)

    texts = [f"{a['title']}. {a.get('description', '')}" for a in articles]
    article_embeddings = model.encode(texts, convert_to_tensor=True)

    cosine_scores = util.cos_sim(article_embeddings, interest_embeddings)

    matches = []
    for i, article in enumerate(articles):
        best_score = cosine_scores[i].max().item()
        best_idx = cosine_scores[i].argmax().item()
        if best_score >= threshold:
            matches.append(
                {
                    **article,
                    "matched_interest": interests[best_idx],
                    "score": round(best_score, 3),
                }
            )

    matches.sort(key=lambda x: x["score"], reverse=True)
    return matches
