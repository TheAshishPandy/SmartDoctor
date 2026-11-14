"""Non-sensitive process health endpoint."""

from fastapi import APIRouter

from app.config import get_settings

router = APIRouter(tags=["health"])


@router.get("/health", summary="Check API process health")
async def health() -> dict[str, str]:
    settings = get_settings()
    return {"status": "ok", "service": "smartdoctor-api", "version": settings.app_version}
