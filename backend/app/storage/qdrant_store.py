"""Qdrant adapter for tenant- and patient-scoped RAG chunks.

Embedding generation and source-document storage are deliberately separate concerns.
Only store chunks that have passed ingestion, provenance and access-control checks.
"""
from typing import Any

from qdrant_client import AsyncQdrantClient, models

from app.config import get_settings


class PatientKnowledgeStore:
    def __init__(self) -> None:
        settings = get_settings()
        self._client = AsyncQdrantClient(
            url=settings.qdrant_url,
            api_key=settings.qdrant_api_key or None,
        )
        self._collection = settings.qdrant_collection
        self._vector_size = settings.embedding_dimensions

    async def initialize(self) -> None:
        exists = await self._client.collection_exists(self._collection)
        if not exists:
            await self._client.create_collection(
                collection_name=self._collection,
                vectors_config=models.VectorParams(
                    size=self._vector_size,
                    distance=models.Distance.COSINE,
                ),
            )
        await self._client.create_payload_index(
            collection_name=self._collection,
            field_name="organization_id",
            field_schema=models.PayloadSchemaType.KEYWORD,
        )
        await self._client.create_payload_index(
            collection_name=self._collection,
            field_name="patient_id",
            field_schema=models.PayloadSchemaType.KEYWORD,
        )

    async def upsert_patient_chunks(
        self, *, organization_id: str, patient_id: str, points: list[models.PointStruct]
    ) -> None:
        """Persist already-embedded chunks with server-assigned tenant scope."""
        for point in points:
            payload = dict(point.payload or {})
            payload["organization_id"] = organization_id
            payload["patient_id"] = patient_id
            point.payload = payload
        await self._client.upsert(collection_name=self._collection, points=points)

    async def search_patient_context(
        self,
        *,
        organization_id: str,
        patient_id: str,
        query_vector: list[float],
        limit: int = 8,
    ) -> list[Any]:
        """Search only within the exact organization + patient boundary."""
        if len(query_vector) != self._vector_size:
            raise ValueError(
                f"Expected {self._vector_size}-dimensional embeddings, got {len(query_vector)}"
            )
        result = await self._client.query_points(
            collection_name=self._collection,
            query=query_vector,
            query_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="organization_id",
                        match=models.MatchValue(value=organization_id),
                    ),
                    models.FieldCondition(
                        key="patient_id",
                        match=models.MatchValue(value=patient_id),
                    ),
                ]
            ),
            limit=max(1, min(limit, 30)),
            with_payload=True,
        )
        return result.points

    async def close(self) -> None:
        await self._client.close()
