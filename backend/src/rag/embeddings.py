"""Local text embeddings via FastEmbed (ONNX, CPU, no API key).

The model is loaded once and cached. The first run downloads model weights.
"""

from __future__ import annotations

from functools import lru_cache

from fastembed import TextEmbedding

from config import settings


@lru_cache(maxsize=1)
def _model() -> TextEmbedding:
    return TextEmbedding(model_name=settings.embedding_model)


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed a batch of texts into vectors."""
    return [vector.tolist() for vector in _model().embed(texts)]


def embed_query(text: str) -> list[float]:
    """Embed a single query string into one vector."""
    return embed_texts([text])[0]
