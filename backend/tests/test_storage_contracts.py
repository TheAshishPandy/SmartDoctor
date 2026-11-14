"""Unit-level contracts for MongoDB ownership and Qdrant patient scoping."""
import asyncio
from types import SimpleNamespace

import pytest
from qdrant_client import models

from app.config import Settings
from app.storage.chat_mongo import ChatStore
from app.storage.qdrant_store import PatientKnowledgeStore


def test_storage_settings_have_local_development_defaults():
    settings = Settings()
    assert settings.mongodb_database == "smartdoctor"
    assert settings.qdrant_collection == "patient_records"
    assert settings.embedding_dimensions > 0


def test_chat_append_is_scoped_to_verified_owner_and_organization():
    store = ChatStore()
    captured = {}

    class FakeCollection:
        async def update_one(self, query, update):
            captured["query"] = query
            captured["update"] = update
            return SimpleNamespace(modified_count=1)

    store._collection = FakeCollection()
    result = asyncio.run(
        store.append_message(
            organization_id="org-1",
            owner_subject="oidc-subject-1",
            conversation_id="conversation-1",
            message={"role": "user", "content": "synthetic test"},
        )
    )

    assert result is True
    assert captured["query"] == {
        "organization_id": "org-1",
        "owner_subject": "oidc-subject-1",
        "conversation_id": "conversation-1",
    }
    asyncio.run(store.close())


def test_qdrant_patient_search_requires_both_tenant_filters():
    store = PatientKnowledgeStore()
    store._vector_size = 3
    captured = {}

    async def fake_query_points(**kwargs):
        captured.update(kwargs)
        return SimpleNamespace(points=[])

    store._client.query_points = fake_query_points
    asyncio.run(
        store.search_patient_context(
            organization_id="org-1",
            patient_id="patient-1",
            query_vector=[0.1, 0.2, 0.3],
            limit=8,
        )
    )

    conditions = captured["query_filter"].must
    assert len(conditions) == 2
    assert {condition.key for condition in conditions} == {
        "organization_id",
        "patient_id",
    }
    assert captured["limit"] == 8
    asyncio.run(store.close())


def test_qdrant_patient_search_rejects_wrong_embedding_dimension(monkeypatch):
    store = PatientKnowledgeStore()
    store._vector_size = 3

    async def fail_if_called(**kwargs):
        raise AssertionError("Qdrant must not be queried for invalid vector dimensions")

    monkeypatch.setattr(store._client, "query_points", fail_if_called)

    with pytest.raises(ValueError, match="Expected 3-dimensional"):
        asyncio.run(
            store.search_patient_context(
                organization_id="org-1",
                patient_id="patient-1",
                query_vector=[0.1, 0.2],
            )
        )
    asyncio.run(store.close())
