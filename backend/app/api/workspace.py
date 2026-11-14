"""Synthetic demo workspace, patient document ingestion and evidence-grounded chat."""
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID, uuid4, uuid5
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.authorization import authorize_patient_read
from app.config import get_settings
from app.db import get_db
from app.ingestion.pipeline import extract_pages, chunk_pages, embedding_service
from app.models import Organization, Patient, PatientDocument, AuditEvent
from app.rag.service import rag_service
from app.security import Principal, get_current_principal, DEMO_ORGANIZATION_ID
from app.storage.chat_mongo import ChatStore

router = APIRouter(prefix="/api/v1/workspace", tags=["workspace"])
PERSONAL_WORKSPACE_NAMESPACE = UUID("7a70c4a1-8d21-4ad2-8d95-25c9d12b6f44")
chat_store = ChatStore()

class ChatRequest(BaseModel):
    patient_id: UUID
    question: str = Field(min_length=2, max_length=4000)
    conversation_id: str | None = None

def _audit(db: Session, principal: Principal, action: str, resource_id: str) -> None:
    db.add(AuditEvent(actor_sub=principal.subject, actor_role=",".join(principal.roles),
        action=action, resource_type="patient_document", resource_id=resource_id,
        outcome="allowed"))
    db.commit()

@router.post("/demo/bootstrap")
def bootstrap_demo(principal: Principal = Depends(get_current_principal), db: Session = Depends(get_db)) -> dict:
    settings = get_settings()
    if settings.app_env != "development" or not settings.dev_auth_enabled or not principal.is_demo:
        raise HTTPException(status_code=404, detail="Demo workspace is disabled")
    org_id = UUID(principal.organization_id or DEMO_ORGANIZATION_ID)
    org = db.get(Organization, org_id)
    if org is None:
        db.add(Organization(id=org_id, name="SmartDoctor Demo Clinic", status="active"))
        db.flush()
    patient = db.scalar(select(Patient).where(Patient.owner_sub == principal.subject, Patient.organization_id == org_id))
    if patient is None:
        patient = Patient(owner_sub=principal.subject, organization_id=org_id,
            display_label="Alex Morgan · Demo Patient")
        db.add(patient)
        db.commit()
        db.refresh(patient)
    return {"patient_id": str(patient.id), "display_label": patient.display_label,
        "organization_id": str(org_id), "mode": "synthetic-demo"}

@router.post("/bootstrap")
def bootstrap_workspace(principal: Principal = Depends(get_current_principal), db: Session = Depends(get_db)) -> dict:
    """Create or retrieve the authenticated user's personal patient workspace."""
    if principal.is_demo:
        raise HTTPException(status_code=403, detail="Use the demo bootstrap endpoint for demo access")
    if "patient" not in principal.roles:
        raise HTTPException(status_code=403, detail="A patient role is required to create a personal workspace")
    organization_id = uuid5(PERSONAL_WORKSPACE_NAMESPACE, principal.subject)
    organization = db.get(Organization, organization_id)
    if organization is None:
        organization = Organization(id=organization_id, name="Personal workspace", status="active")
        db.add(organization)
        db.flush()
    patient = db.scalar(select(Patient).where(Patient.owner_sub == principal.subject,
        Patient.organization_id == organization_id))
    if patient is None:
        patient = Patient(owner_sub=principal.subject, organization_id=organization_id,
            display_label="My patient profile")
        db.add(patient)
        db.commit()
        db.refresh(patient)
    else:
        db.commit()
    return {"patient_id": str(patient.id), "display_label": patient.display_label,
        "organization_id": str(organization_id), "mode": "authenticated"}

@router.post("/documents", status_code=201)
async def upload_document(patient_id: UUID, file: UploadFile = File(...),
    principal: Principal = Depends(get_current_principal), db: Session = Depends(get_db)) -> dict:
    patient = authorize_patient_read(db, principal, patient_id)
    if patient.organization_id is None:
        raise HTTPException(status_code=409, detail="Patient must belong to an organization")
    cfg = get_settings()
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in {".pdf", ".docx", ".txt", ".md"}:
        raise HTTPException(status_code=415, detail="Upload PDF, DOCX, TXT or Markdown")
    content = await file.read(cfg.max_upload_mb * 1024 * 1024 + 1)
    if not content or len(content) > cfg.max_upload_mb * 1024 * 1024:
        raise HTTPException(status_code=413, detail=f"File must be between 1 byte and {cfg.max_upload_mb} MB")
    document_id = uuid4()
    safe_name = Path(file.filename or "document").name[:255]
    root = Path(cfg.upload_directory)
    root.mkdir(parents=True, exist_ok=True)
    storage_key = f"{patient.id}/{document_id}{suffix}"
    destination = root / storage_key
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(content)
    document = PatientDocument(id=document_id, patient_id=patient.id,
        organization_id=patient.organization_id, uploaded_by=principal.subject,
        filename=safe_name, content_type=file.content_type or "application/octet-stream",
        storage_key=storage_key, status="processing")
    db.add(document)
    db.commit()
    try:
        pages = extract_pages(destination)
        chunks = chunk_pages(pages)
        if not chunks:
            raise ValueError("No readable text found. Scanned PDFs need OCR before ingestion.")
        vectors = embedding_service.embed([chunk["text"] for chunk in chunks])
        await rag_service.index_chunks(organization_id=str(patient.organization_id),
            patient_id=str(patient.id), document_id=str(document.id), filename=safe_name,
            chunks=chunks, vectors=vectors)
        document.status = "ready"
        document.chunk_count = len(chunks)
        document.indexed_at = datetime.now(timezone.utc)
        db.commit()
        _audit(db, principal, "document.ingest", str(document.id))
        return {"id": str(document.id), "filename": safe_name, "status": document.status,
            "chunk_count": document.chunk_count, "pages": len(pages)}
    except Exception as exc:
        document.status = "failed"
        document.error_message = str(exc)[:500]
        db.commit()
        raise HTTPException(status_code=422, detail=f"Document ingestion failed: {exc}") from exc

@router.get("/documents")
def list_documents(patient_id: UUID, principal: Principal = Depends(get_current_principal),
    db: Session = Depends(get_db)) -> list[dict]:
    patient = authorize_patient_read(db, principal, patient_id)
    rows = db.scalars(select(PatientDocument).where(
        PatientDocument.patient_id == patient.id,
        PatientDocument.organization_id == patient.organization_id
    ).order_by(PatientDocument.created_at.desc())).all()
    return [{"id": str(row.id), "filename": row.filename, "status": row.status,
        "chunk_count": row.chunk_count, "created_at": row.created_at.isoformat(),
        "error": row.error_message} for row in rows]

async def _generate_answer(question: str, contexts: list[dict]) -> tuple[str, str]:
    cfg = get_settings()
    if not contexts:
        return ("I could not find relevant information in the documents uploaded to this patient workspace. "
            "Please add a readable document or rephrase the question.", "no-evidence")
    evidence = "\n\n".join(f"[{i+1}] {item.get('filename')} (page {item.get('page')}): {item.get('text')}"
        for i, item in enumerate(contexts))
    if cfg.llm_base_url:
        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(base_url=cfg.llm_base_url, api_key=cfg.llm_api_key)
            response = await client.chat.completions.create(model=cfg.llm_model, temperature=0.1,
                messages=[
                    {"role": "system", "content": (
                        "You are SmartDoctor, a document-grounded health information assistant. "
                        "Answer only from supplied excerpts. If evidence is missing, say so. "
                        "Do not diagnose, prescribe, or recommend treatment. Cite sources as [1], [2]. "
                        "Mention uncertainty and advise clinician review for medical decisions."
                    )},
                    {"role": "user", "content": f"Question: {question}\n\nEvidence:\n{evidence}"},
                ])
            return (response.choices[0].message.content or "No answer was generated.", "llm")
        except Exception:
            pass
    answer = "I found these relevant passages in your uploaded records. This is a source summary, not a diagnosis:\n\n"
    answer += "\n\n".join(f"[{i+1}] {item.get('text','')}" for i, item in enumerate(contexts[:3]))
    answer += "\n\nPlease discuss clinical interpretation with a qualified healthcare professional."
    return answer, "extractive-fallback"

@router.post("/chat")
async def chat(request: ChatRequest, principal: Principal = Depends(get_current_principal),
    db: Session = Depends(get_db)) -> dict:
    patient = authorize_patient_read(db, principal, request.patient_id)
    if patient.organization_id is None:
        raise HTTPException(status_code=409, detail="Patient must belong to an organization")
    query_vector = embedding_service.embed([request.question])[0]
    contexts = await rag_service.search(organization_id=str(patient.organization_id),
        patient_id=str(patient.id), vector=query_vector, limit=6)
    answer, answer_mode = await _generate_answer(request.question, contexts)
    conversation_id = request.conversation_id or str(uuid4())
    if request.conversation_id is None:
        await chat_store.create_conversation(organization_id=str(patient.organization_id),
            owner_subject=principal.subject, conversation_id=conversation_id, patient_id=str(patient.id))
    else:
        existing = await chat_store.get_conversation(organization_id=str(patient.organization_id),
            owner_subject=principal.subject, conversation_id=conversation_id)
        if existing is None or existing.get("patient_id") != str(patient.id):
            raise HTTPException(status_code=404, detail="Conversation not found")
    await chat_store.append_message(organization_id=str(patient.organization_id),
        owner_subject=principal.subject, conversation_id=conversation_id,
        message={"role": "user", "content": request.question, "created_at": datetime.now(timezone.utc)})
    await chat_store.append_message(organization_id=str(patient.organization_id),
        owner_subject=principal.subject, conversation_id=conversation_id,
        message={"role": "assistant", "content": answer, "created_at": datetime.now(timezone.utc),
            "answer_mode": answer_mode})
    return {"conversation_id": conversation_id, "answer": answer, "answer_mode": answer_mode,
        "sources": [{"document_id": item.get("document_id"), "filename": item.get("filename"),
            "page": item.get("page"), "score": round(float(item.get("score", 0)), 4),
            "excerpt": item.get("text", "")[:360]} for item in contexts]}
