"""FastAPI application entry point."""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.auth import router as auth_router
from app.api.health import router as health_router
from app.api.patients import router as patients_router
from app.api.workspace import router as workspace_router, chat_store
from app.api.management import router as management_router
from app.api.organizations import router as organizations_router
from app.api.themes import router as themes_router
from app.config import get_settings
from app.rag.service import rag_service

settings = get_settings()


@asynccontextmanager
async def lifespan(application: FastAPI):
    if getattr(application.state, "skip_external_services", False):
        yield
        return
    await chat_store.initialize()
    await rag_service.initialize()
    yield
    await chat_store.close()
    await rag_service.close()


app = FastAPI(
    title=settings.app_name, version=settings.app_version, lifespan=lifespan,
    description="SmartDoctor document workspace and evidence-grounded RAG prototype. Not a diagnostic or prescribing system.",
    docs_url="/docs" if settings.app_env != "production" else None, redoc_url=None,
)
app.add_middleware(
    CORSMiddleware, allow_origins=settings.allowed_origins, allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Correlation-ID"],
)
app.include_router(health_router)
app.include_router(auth_router)
app.include_router(patients_router)
app.include_router(workspace_router)
app.include_router(management_router)
app.include_router(organizations_router)
app.include_router(themes_router)
