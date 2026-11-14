"""Patient endpoints protected by relationship and consent checks."""
from uuid import UUID
from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session
from app.authorization import authorize_patient_read
from app.db import get_db
from app.schemas import PatientRead
from app.security import Principal, get_current_principal

router = APIRouter(prefix="/api/v1/patients", tags=["patients"])

@router.get("/{patient_id}", response_model=PatientRead, summary="Read an authorized patient profile")
def read_patient(
    patient_id: UUID,
    correlation_id: str | None = Header(default=None, alias="X-Correlation-ID"),
    principal: Principal = Depends(get_current_principal),
    db: Session = Depends(get_db),
) -> PatientRead:
    patient = authorize_patient_read(db, principal, patient_id, correlation_id)
    return PatientRead.model_validate(patient)
