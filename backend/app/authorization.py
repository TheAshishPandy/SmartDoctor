"""Patient-resource authorization and security audit recording."""
from datetime import datetime, timezone
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models import AuditEvent, CareRelationship, ConsentGrant, Membership, Patient
from app.security import Principal

PATIENT_READ_SCOPE = "patient.read"

def _is_future(value: datetime | None, now: datetime) -> bool:
    if value is None:
        return True
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value > now

def authorize_patient_read(db: Session, principal: Principal, patient_id: UUID, correlation_id: str | None = None) -> Patient:
    patient = db.get(Patient, patient_id)
    if patient is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")
    allowed = "patient" in principal.roles and patient.owner_sub == principal.subject
    if not allowed and "clinician" in principal.roles and patient.organization_id is not None:
        now = datetime.now(timezone.utc)
        membership = db.scalar(select(Membership).where(
            Membership.user_sub == principal.subject,
            Membership.organization_id == patient.organization_id,
            Membership.role == "clinician",
            Membership.status == "active",
        ))
        relationship = db.scalar(select(CareRelationship).where(
            CareRelationship.patient_id == patient.id,
            CareRelationship.clinician_sub == principal.subject,
            CareRelationship.organization_id == patient.organization_id,
            CareRelationship.status == "active",
            CareRelationship.ends_at.is_(None),
        ))
        consent = db.scalar(select(ConsentGrant).where(
            ConsentGrant.patient_id == patient.id,
            ConsentGrant.grantee_sub == principal.subject,
            ConsentGrant.scope == PATIENT_READ_SCOPE,
            ConsentGrant.status == "active",
            ConsentGrant.revoked_at.is_(None),
        ))
        allowed = membership is not None and relationship is not None and consent is not None and _is_future(consent.expires_at, now)
    db.add(AuditEvent(
        actor_sub=principal.subject,
        actor_role=",".join(sorted(principal.roles)) or "none",
        action="patient.read",
        resource_type="patient",
        resource_id=str(patient.id),
        outcome="allowed" if allowed else "denied",
        correlation_id=correlation_id,
    ))
    db.commit()
    if not allowed:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")
    return patient
