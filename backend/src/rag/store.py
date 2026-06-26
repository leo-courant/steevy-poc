"""Qdrant vector store: connection, collection schema, upsert, and search."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from config import settings


@dataclass
class SearchHit:
    """One retrieved chunk with its similarity score and source metadata."""

    score: float
    text: str
    source_file: str
    record_id: str
    tag: str
    chunk_index: int


class QdrantStore:
    """Thin, explicit wrapper over the Qdrant collection used by this project."""

    def __init__(self) -> None:
        # Connect over REST (port 6333). `check_compatibility=False` skips the
        # version round-trip at construction, so building the store never touches
        # the network until you actually upsert or search.
        self.client = QdrantClient(
            url=settings.qdrant_url,
            api_key=settings.qdrant_api_key or None,
            check_compatibility=False,
        )
        self.collection = settings.qdrant_collection

    def ensure_collection(self, vector_size: int) -> None:
        """(Re)create the collection with an explicit, cosine-distance schema."""
        if self.client.collection_exists(self.collection):
            self.client.delete_collection(self.collection)
        self.client.create_collection(
            collection_name=self.collection,
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
        )

    def upsert(self, vectors: list[list[float]], payloads: list[dict]) -> int:
        """Upsert vectors + payloads as points. Returns the number written."""
        points = [
            PointStruct(id=str(uuid.uuid4()), vector=vector, payload=payload)
            for vector, payload in zip(vectors, payloads)
        ]
        self.client.upsert(collection_name=self.collection, points=points)
        return len(points)

    def search(self, query_vector: list[float], k: int) -> list[SearchHit]:
        """Return the top-`k` most similar chunks for a query vector."""
        response = self.client.query_points(
            collection_name=self.collection,
            query=query_vector,
            limit=k,
            with_payload=True,
        )
        hits: list[SearchHit] = []
        for point in response.points:
            payload = point.payload or {}
            hits.append(
                SearchHit(
                    score=point.score,
                    text=payload.get("text", ""),
                    source_file=payload.get("source_file", ""),
                    record_id=payload.get("record_id", ""),
                    tag=payload.get("tag", ""),
                    chunk_index=payload.get("chunk_index", 0),
                )
            )
        return hits
