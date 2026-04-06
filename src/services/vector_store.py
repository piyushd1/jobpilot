"""Qdrant vector store client wrapper.

Manages two collections:
  - candidate_profiles: resume embeddings (full profile, skills, experience blocks)
  - job_descriptions: job description embeddings
"""

from __future__ import annotations

from typing import Any

from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from src.config.settings import settings
from src.utils.logging import get_logger

logger = get_logger(__name__)

CANDIDATE_PROFILES_COLLECTION = "candidate_profiles"
JOB_DESCRIPTIONS_COLLECTION = "job_descriptions"
EMBEDDING_DIM = 1536  # text-embedding-3-small


class VectorStore:
    """Async Qdrant client wrapper with collection management."""

    def __init__(self) -> None:
        self._client: AsyncQdrantClient | None = None

    async def connect(self) -> None:
        """Initialize the Qdrant client connection."""
        self._client = AsyncQdrantClient(url=settings.qdrant_url)
        logger.info("Connected to Qdrant", url=settings.qdrant_url)

    async def close(self) -> None:
        """Close the Qdrant client."""
        if self._client:
            await self._client.close()
            self._client = None

    @property
    def client(self) -> AsyncQdrantClient:
        if self._client is None:
            raise RuntimeError("VectorStore not connected. Call connect() first.")
        return self._client

    async def ensure_collections(self) -> None:
        """Create collections if they don't exist."""
        for collection_name in [CANDIDATE_PROFILES_COLLECTION, JOB_DESCRIPTIONS_COLLECTION]:
            collections = await self.client.get_collections()
            names = [c.name for c in collections.collections]
            if collection_name not in names:
                await self.client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(
                        size=EMBEDDING_DIM,
                        distance=Distance.COSINE,
                    ),
                )
                logger.info(f"Created collection: {collection_name}")

    async def upsert(
        self,
        collection: str,
        point_id: str,
        vector: list[float],
        payload: dict[str, Any],
    ) -> None:
        """Upsert a single point into a collection."""
        await self.client.upsert(
            collection_name=collection,
            points=[
                PointStruct(
                    id=point_id,
                    vector=vector,
                    payload=payload,
                )
            ],
        )

    async def upsert_batch(
        self,
        collection: str,
        points: list[dict[str, Any]],
    ) -> None:
        """Upsert multiple points. Each dict needs: id, vector, payload."""
        structs = [
            PointStruct(id=p["id"], vector=p["vector"], payload=p["payload"]) for p in points
        ]
        await self.client.upsert(collection_name=collection, points=structs)

    async def search(
        self,
        collection: str,
        query_vector: list[float],
        limit: int = 10,
        score_threshold: float | None = None,
        filter_conditions: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Cosine similarity search.

        Returns list of dicts with: id, score, payload.
        """
        from qdrant_client.models import Filter, FieldCondition, MatchValue

        qdrant_filter = None
        if filter_conditions:
            must = []
            for key, value in filter_conditions.items():
                must.append(FieldCondition(key=key, match=MatchValue(value=value)))
            qdrant_filter = Filter(must=must)

        results = await self.client.search(
            collection_name=collection,
            query_vector=query_vector,
            limit=limit,
            score_threshold=score_threshold,
            query_filter=qdrant_filter,
        )

        return [
            {
                "id": str(r.id),
                "score": r.score,
                "payload": r.payload,
            }
            for r in results
        ]

    async def delete(self, collection: str, point_ids: list[str]) -> None:
        """Delete points by IDs."""
        from qdrant_client.models import PointIdsList

        await self.client.delete(
            collection_name=collection,
            points_selector=PointIdsList(points=point_ids),
        )


# Singleton
vector_store = VectorStore()
