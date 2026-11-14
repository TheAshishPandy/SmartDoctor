"""MongoDB persistence for chat sessions and message history.

Identity fields must come from the verified API principal, never request-body claims.
Do not put clinical transactions or authorization decisions in this store.
"""
from datetime import UTC, datetime
from typing import Any

from pymongo import AsyncMongoClient, DESCENDING

from app.config import get_settings


class ChatStore:
    def __init__(self) -> None:
        settings = get_settings()
        self._client = AsyncMongoClient(settings.mongodb_url)
        self._collection = self._client[settings.mongodb_database]["conversations"]

    async def initialize(self) -> None:
        await self._collection.create_index(
            [("organization_id", 1), ("conversation_id", 1)], unique=True
        )
        await self._collection.create_index(
            [("organization_id", 1), ("owner_subject", 1), ("updated_at", DESCENDING)]
        )

    async def create_conversation(
        self,
        *,
        organization_id: str,
        owner_subject: str,
        conversation_id: str,
        patient_id: str | None = None,
    ) -> None:
        now = datetime.now(UTC)
        await self._collection.insert_one(
            {
                "organization_id": organization_id,
                "owner_subject": owner_subject,
                "conversation_id": conversation_id,
                "patient_id": patient_id,
                "messages": [],
                "created_at": now,
                "updated_at": now,
            }
        )

    async def append_message(
        self,
        *,
        organization_id: str,
        owner_subject: str,
        conversation_id: str,
        message: dict[str, Any],
    ) -> bool:
        """Append one message only to a conversation owned by this principal."""
        result = await self._collection.update_one(
            {
                "organization_id": organization_id,
                "owner_subject": owner_subject,
                "conversation_id": conversation_id,
            },
            {
                "$push": {"messages": message},
                "$set": {"updated_at": datetime.now(UTC)},
            },
        )
        return result.modified_count == 1

    async def get_conversation(
        self, *, organization_id: str, owner_subject: str, conversation_id: str
    ) -> dict[str, Any] | None:
        return await self._collection.find_one(
            {
                "organization_id": organization_id,
                "owner_subject": owner_subject,
                "conversation_id": conversation_id,
            },
            {"_id": 0},
        )

    async def close(self) -> None:
        await self._client.close()
