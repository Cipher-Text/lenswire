from __future__ import annotations

import asyncio
from functools import lru_cache
from typing import Protocol


class EmbeddingProvider(Protocol):
    async def encode(self, texts: list[str]) -> list[list[float]]: ...


class SentenceTransformerEmbeddingProvider:
    def __init__(self, model_name: str) -> None:
        self.model_name = model_name
        self._model = None

    def _model_instance(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(self.model_name)
        return self._model

    async def encode(self, texts: list[str]) -> list[list[float]]:
        def _encode() -> list[list[float]]:
            vectors = self._model_instance().encode(texts, convert_to_tensor=False)
            return [list(map(float, vector)) for vector in vectors]

        return await asyncio.to_thread(_encode)


@lru_cache(maxsize=1)
def cached_provider(model_name: str) -> SentenceTransformerEmbeddingProvider:
    return SentenceTransformerEmbeddingProvider(model_name)


def cosine_similarity(left: list[float], right: list[float]) -> float:
    numerator = sum(a * b for a, b in zip(left, right, strict=False))
    left_norm = sum(a * a for a in left) ** 0.5
    right_norm = sum(b * b for b in right) ** 0.5
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return numerator / (left_norm * right_norm)
