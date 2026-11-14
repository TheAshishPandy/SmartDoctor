"""Unit-level contracts for storage configuration and Qdrant scope filters."""
import pytest

from app.config import Settings
from app.storage.qdrant_store import PatientKnowledgeStore


def test_storage_settings_have_local_development_defaults():
    settings = Settings()
    assert settings.mongodb_database == "smartdoctor"
    assert settings.qdrant_collection == "patient_records"
    assert settings.embedding_dimensions > 0


def test_qdrant_patient_search_rejects_wrong_embedding_dimension(monkeypatch):
    store = PatientKnowledgeStore()
    store._vector_size = 3

    async def fail_if_called(**kwargs):
        raise AssertionError("Qdrant must not be queried for invalid vector dimensions")

    monkeypatch.setattr(store._client, "query_points", fail_if_called)

    with pytest.raises(ValueError, match="Expected 3-dimensional"):
        import asyncio
        asyncio.run(
            store.search_patient_context(
                organization_id="org-1",
                patient_id="patient-1",
                query_vector=[0.1, 0.2],
            )
        )
