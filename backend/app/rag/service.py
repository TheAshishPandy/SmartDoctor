"""Patient-scoped Qdrant indexing and evidence retrieval."""
from qdrant_client import AsyncQdrantClient, models
from app.config import get_settings
from app.ingestion.pipeline import chunk_point_id


class PatientRagService:
    def __init__(self) -> None:
        cfg = get_settings()
        self.client = AsyncQdrantClient(url=cfg.qdrant_url, api_key=cfg.qdrant_api_key or None)
        self.collection = cfg.qdrant_collection
        self.dimensions = cfg.embedding_dimensions

    async def initialize(self) -> None:
        if not await self.client.collection_exists(self.collection):
            await self.client.create_collection(
                collection_name=self.collection,
                vectors_config=models.VectorParams(size=self.dimensions, distance=models.Distance.COSINE),
            )
        collection_info = await self.client.get_collection(self.collection)
        existing_indexes = getattr(collection_info, "payload_schema", {}) or {}
        for field in ("organization_id", "patient_id", "document_id"):
            if field in existing_indexes:
                continue
            await self.client.create_payload_index(
                collection_name=self.collection, field_name=field,
                field_schema=models.PayloadSchemaType.KEYWORD,
            )

    async def index_chunks(self, *, organization_id: str, patient_id: str, document_id: str,
                           filename: str, chunks: list[dict], vectors: list[list[float]]) -> None:
        if len(chunks) != len(vectors):
            raise ValueError("Chunk and embedding counts do not match")
        points = []
        for chunk, vector in zip(chunks, vectors):
            if len(vector) != self.dimensions:
                raise ValueError(f"Expected {self.dimensions}-dimensional embeddings")
            points.append(models.PointStruct(
                id=chunk_point_id(__import__("uuid").UUID(document_id), chunk["chunk_index"]),
                vector=vector,
                payload={
                    "organization_id": organization_id, "patient_id": patient_id,
                    "document_id": document_id, "filename": filename,
                    "page": chunk["page"], "chunk_index": chunk["chunk_index"],
                    "text": chunk["text"],
                },
            ))
        if points:
            await self.client.upsert(collection_name=self.collection, points=points, wait=True)

    async def search(self, *, organization_id: str, patient_id: str,
                     vector: list[float], limit: int = 6) -> list[dict]:
        if len(vector) != self.dimensions:
            raise ValueError("Query embedding dimension does not match Qdrant collection")
        result = await self.client.query_points(
            collection_name=self.collection, query=vector,
            query_filter=models.Filter(must=[
                models.FieldCondition(key="organization_id", match=models.MatchValue(value=organization_id)),
                models.FieldCondition(key="patient_id", match=models.MatchValue(value=patient_id)),
            ]),
            limit=max(1, min(limit, 12)), with_payload=True,
        )
        return [
            {"score": point.score, **(point.payload or {})}
            for point in result.points
        ]

    async def close(self) -> None:
        await self.client.close()


rag_service = PatientRagService()
