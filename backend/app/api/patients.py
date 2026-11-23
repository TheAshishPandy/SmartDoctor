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


@router.get("/", summary="List patients visible to the signed-in role")
def list_patients(principal: Principal = Depends(get_current_principal),
    db: Session = Depends(get_db)) -> list[dict]:
    from datetime import datetime, timezone
    from fastapi import HTTPException
    from sqlalchemy import select
    from app.models import AuditEvent, CareRelationship, ConsentGrant, Membership, Patient
    role = "admin" if "admin" in principal.roles else "receptionist" if "receptionist" in principal.roles else "doctor" if "clinician" in principal.roles else "patient" if "patient" in principal.roles else None
    if role is None:
        raise HTTPException(status_code=403, detail="A supported workspace role is required")
    if role == "patient":
        rows = db.scalars(select(Patient).where(Patient.owner_sub == principal.subject).limit(100)).all()
    else:
        membership_role = "clinician" if role == "doctor" else role
        membership = db.scalar(select(Membership).where(
            Membership.user_sub == principal.subject, Membership.role == membership_role,
            Membership.status == "active"))
        if membership is None:
            raise HTTPException(status_code=403, detail="An active clinic membership is required")
        if role in {"admin", "receptionist"}:
            rows = db.scalars(select(Patient).where(
                Patient.organization_id == membership.organization_id).order_by(Patient.created_at.desc()).limit(100)).all()
        else:
            now = datetime.now(timezone.utc)
            rows = db.scalars(select(Patient).join(CareRelationship,
                CareRelationship.patient_id == Patient.id).join(ConsentGrant,
                ConsentGrant.patient_id == Patient.id).where(
                Patient.organization_id == membership.organization_id,
                CareRelationship.clinician_sub == principal.subject,
                CareRelationship.organization_id == membership.organization_id,
                CareRelationship.status == "active",
                CareRelationship.starts_at <= now,
                (CareRelationship.ends_at.is_(None) | (CareRelationship.ends_at > now)),
                ConsentGrant.grantee_sub == principal.subject,
                ConsentGrant.scope == "patient.read",
                ConsentGrant.status == "active",
                ConsentGrant.revoked_at.is_(None),
                (ConsentGrant.expires_at.is_(None) | (ConsentGrant.expires_at > now)),
            ).order_by(Patient.created_at.desc()).limit(100)).all()
    db.add(AuditEvent(actor_sub=principal.subject, actor_role=",".join(sorted(principal.roles)),
        action="patient.list", resource_type="patient_directory", resource_id="self",
        outcome="allowed"))
    db.commit()
    return [{"id": str(row.id), "display_label": row.display_label,
        "created_at": row.created_at.isoformat()} for row in rows]
