"""Platform super-admin, tenant administration and patient clinic assistant APIs."""
from datetime import datetime, timezone
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.db import get_db
from app.models import AuthUser, AuditEvent, CareRelationship, ConsentGrant, Membership, Organization, Patient, WorkspaceEntry
from app.security import Principal, get_current_principal

router = APIRouter(prefix="/api/v1", tags=["organizations-and-clinic-assistant"])


def _super_admin(principal: Principal) -> None:
    if "super_admin" not in principal.roles:
        raise HTTPException(status_code=403, detail="Platform Super Admin access required")


def _organization_admin(db: Session, principal: Principal, organization_id: UUID) -> None:
    if "super_admin" in principal.roles:
        return
    membership = db.scalar(select(Membership).where(
        Membership.user_sub == principal.subject, Membership.organization_id == organization_id,
        Membership.role == "admin", Membership.status == "active"))
    if membership is None:
        raise HTTPException(status_code=403, detail="Active administrator membership required")


def _audit(db: Session, principal: Principal, action: str, kind: str, resource_id: str) -> None:
    db.add(AuditEvent(actor_sub=principal.subject, actor_role=",".join(sorted(principal.roles)),
        action=action, resource_type=kind, resource_id=resource_id, outcome="allowed"))


def _slot_matches(slot: str, preferred_at: datetime) -> bool:
    try:
        value = datetime.fromisoformat(str(slot).replace("Z", "+00:00"))
        target = preferred_at if preferred_at.tzinfo else preferred_at.replace(tzinfo=timezone.utc)
        value = value if value.tzinfo else value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc) == target.astimezone(timezone.utc)
    except (TypeError, ValueError):
        return False


class OrganizationCreate(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    chatbot_enabled: bool = True


class OrganizationUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=200)
    status: str | None = Field(default=None, pattern=r"^(active|suspended)$")
    chatbot_enabled: bool | None = None
    chatbot_welcome: str | None = Field(default=None, max_length=500)


class StaffAssign(BaseModel):
    user_id: UUID | None = None
    user_email: EmailStr | None = None
    role: str = Field(pattern=r"^(admin|doctor|receptionist)$")
    specialties: list[str] = Field(default_factory=list, max_length=20)
    availability: dict = Field(default_factory=dict)


class ClinicAssistantRequest(BaseModel):
    message: str = Field(min_length=2, max_length=2000)
    intent: str = Field(pattern=r"^(identify_doctor|find_doctor|book_appointment|general)$")
    specialty: str | None = Field(default=None, max_length=120)
    preferred_at: datetime | None = None
    reason: str | None = Field(default=None, max_length=1000)


@router.get("/super-admin/organizations")
def list_organizations(principal: Principal = Depends(get_current_principal), db: Session = Depends(get_db)) -> list[dict]:
    _super_admin(principal)
    rows = db.scalars(select(Organization).order_by(Organization.created_at.desc())).all()
    result = []
    for org in rows:
        counts = db.scalars(select(Membership).where(Membership.organization_id == org.id,
            Membership.status == "active")).all()
        result.append({"id": str(org.id), "name": org.name, "status": org.status,
            "staff_count": len(counts), "chatbot": org.chatbot_config or {}, "created_at": org.created_at.isoformat()})
    return result


@router.post("/super-admin/organizations", status_code=201)
def create_organization(payload: OrganizationCreate, principal: Principal = Depends(get_current_principal),
    db: Session = Depends(get_db)) -> dict:
    _super_admin(principal)
    org = Organization(name=payload.name.strip(), status="active",
        chatbot_config={"enabled": payload.chatbot_enabled, "welcome": "Welcome to our clinic. How can I help you?"})
    db.add(org); db.flush()
    _audit(db, principal, "organization.create", "organization", str(org.id)); db.commit()
    return {"id": str(org.id), "name": org.name, "status": org.status, "chatbot": org.chatbot_config}


@router.patch("/super-admin/organizations/{organization_id}")
def update_organization(organization_id: UUID, payload: OrganizationUpdate,
    principal: Principal = Depends(get_current_principal), db: Session = Depends(get_db)) -> dict:
    _super_admin(principal)
    org = db.get(Organization, organization_id)
    if org is None: raise HTTPException(status_code=404, detail="Organization not found")
    changes = payload.model_dump(exclude_unset=True)
    config = dict(org.chatbot_config or {})
    if "chatbot_enabled" in changes: config["enabled"] = changes.pop("chatbot_enabled")
    if "chatbot_welcome" in changes: config["welcome"] = changes.pop("chatbot_welcome")
    for key, value in changes.items(): setattr(org, key, value)
    org.chatbot_config = config
    _audit(db, principal, "organization.update", "organization", str(org.id)); db.commit()
    return {"id": str(org.id), "name": org.name, "status": org.status, "chatbot": org.chatbot_config}


@router.get("/organizations/{organization_id}/staff")
def list_organization_staff(organization_id: UUID, principal: Principal = Depends(get_current_principal),
    db: Session = Depends(get_db)) -> list[dict]:
    _organization_admin(db, principal, organization_id)
    rows = db.scalars(select(Membership).where(Membership.organization_id == organization_id)
        .order_by(Membership.created_at.desc())).all()
    output = []
    for row in rows:
        try: user = db.get(AuthUser, UUID(row.user_sub))
        except ValueError: user = None
        output.append({"id": str(row.id), "user_id": row.user_sub,
            "name": user.display_name if user else row.user_sub, "email": user.email if user else None,
            "role": "doctor" if row.role == "clinician" else row.role, "status": row.status,
            "specialties": row.specialties or [], "availability": row.availability or {}})
    return output


@router.post("/organizations/{organization_id}/staff", status_code=201)
def assign_organization_staff(organization_id: UUID, payload: StaffAssign,
    principal: Principal = Depends(get_current_principal), db: Session = Depends(get_db)) -> dict:
    _organization_admin(db, principal, organization_id)
    org = db.get(Organization, organization_id)
    if org is None or org.status != "active": raise HTTPException(status_code=404, detail="Active organization not found")
    if not payload.user_id and not payload.user_email:
        raise HTTPException(status_code=422, detail="Provide a verified user account ID or email")
    user = db.get(AuthUser, payload.user_id) if payload.user_id else db.scalar(
        select(AuthUser).where(AuthUser.email == str(payload.user_email).lower()))
    if user is None or not user.is_active or not user.is_verified:
        raise HTTPException(status_code=404, detail="Verified active user account not found")
    if user.role != payload.role:
        raise HTTPException(status_code=409, detail=f"The account must have the platform role '{payload.role}' first")
    role = "clinician" if payload.role == "doctor" else payload.role
    row = db.scalar(select(Membership).where(Membership.user_sub == str(user.id),
        Membership.organization_id == organization_id))
    if row is None:
        row = Membership(user_sub=str(user.id), organization_id=organization_id, role=role, status="active")
        db.add(row)
    row.role = role; row.status = "active"
    row.specialties = [s.strip() for s in payload.specialties if s.strip()] if role == "clinician" else []
    row.availability = payload.availability if role == "clinician" else {}
    _audit(db, principal, "organization.staff.assign", "membership", str(row.id)); db.commit()
    return {"id": str(row.id), "user_id": str(user.id), "role": payload.role,
        "specialties": row.specialties, "availability": row.availability, "status": row.status}


@router.get("/organizations/{organization_id}/doctors")
def find_doctors(organization_id: UUID, specialty: str | None = Query(default=None, max_length=120),
    principal: Principal = Depends(get_current_principal), db: Session = Depends(get_db)) -> list[dict]:
    if "super_admin" not in principal.roles:
        _organization_admin(db, principal, organization_id)
    org = db.get(Organization, organization_id)
    if org is None or org.status != "active": raise HTTPException(status_code=404, detail="Organization not found")
    rows = db.scalars(select(Membership).where(Membership.organization_id == organization_id,
        Membership.role == "clinician", Membership.status == "active")).all()
    result = []
    for row in rows:
        if specialty and specialty.casefold() not in [s.casefold() for s in (row.specialties or [])]: continue
        try: user = db.get(AuthUser, UUID(row.user_sub))
        except ValueError: user = None
        result.append({"doctor_id": row.user_sub, "name": user.display_name if user else "Clinic doctor",
            "specialties": row.specialties or [], "availability": row.availability or {}})
    return result


@router.get("/clinic/me/doctor")
def my_doctor(principal: Principal = Depends(get_current_principal), db: Session = Depends(get_db)) -> dict:
    patient = db.scalar(select(Patient).where(Patient.owner_sub == principal.subject).order_by(Patient.created_at.desc()))
    if patient is None or patient.organization_id is None: raise HTTPException(status_code=404, detail="Patient clinic profile not found")
    rel = db.scalar(select(CareRelationship).where(CareRelationship.patient_id == patient.id,
        CareRelationship.organization_id == patient.organization_id, CareRelationship.status == "active")
        .order_by(CareRelationship.starts_at.desc()))
    if rel is None: return {"assigned": False, "message": "A doctor has not been assigned to your care yet."}
    membership = db.scalar(select(Membership).where(Membership.user_sub == rel.clinician_sub,
        Membership.organization_id == patient.organization_id, Membership.role == "clinician", Membership.status == "active"))
    if membership is None: return {"assigned": False, "message": "A doctor has not been assigned to your care yet."}
    try: doctor = db.get(AuthUser, UUID(rel.clinician_sub))
    except ValueError: doctor = None
    return {"assigned": True, "doctor_id": rel.clinician_sub, "doctor_name": doctor.display_name if doctor else "Your doctor",
        "specialties": membership.specialties or [], "organization_id": str(patient.organization_id)}


@router.post("/clinic/chat")
def clinic_chat(payload: ClinicAssistantRequest, principal: Principal = Depends(get_current_principal),
    db: Session = Depends(get_db)) -> dict:
    if "patient" not in principal.roles: raise HTTPException(status_code=403, detail="Patient sign-in is required")
    patient = db.scalar(select(Patient).where(Patient.owner_sub == principal.subject).order_by(Patient.created_at.desc()))
    if patient is None or patient.organization_id is None: raise HTTPException(status_code=409, detail="Join a clinic before using its clinic assistant")
    org = db.get(Organization, patient.organization_id)
    if org is None or org.status != "active": raise HTTPException(status_code=403, detail="This clinic is currently unavailable")
    if not (org.chatbot_config or {}).get("enabled", True): raise HTTPException(status_code=403, detail="This clinic assistant is disabled")
    if payload.intent == "identify_doctor":
        relationship = db.scalar(select(CareRelationship).where(CareRelationship.patient_id == patient.id,
            CareRelationship.organization_id == patient.organization_id, CareRelationship.status == "active").order_by(CareRelationship.starts_at.desc()))
        if relationship is None:
            return {"intent": payload.intent, "assigned": False, "answer": "You do not have a doctor assigned yet. I can help find a doctor by specialty."}
        membership = db.scalar(select(Membership).where(Membership.user_sub == relationship.clinician_sub,
            Membership.organization_id == patient.organization_id, Membership.role == "clinician", Membership.status == "active"))
        try: doctor = db.get(AuthUser, UUID(relationship.clinician_sub))
        except ValueError: doctor = None
        return {"intent": payload.intent, "assigned": True, "doctor": {"name": doctor.display_name if doctor else "Your doctor",
            "specialties": membership.specialties if membership else []},
            "answer": f"Your assigned doctor is {doctor.display_name if doctor else 'your clinic doctor'}."}
    if payload.intent in {"find_doctor", "book_appointment"}:
        doctor_query = select(Membership).where(Membership.organization_id == patient.organization_id,
            Membership.role == "clinician", Membership.status == "active")
        if payload.intent == "book_appointment":
            doctor_query = doctor_query.with_for_update()
        rows = db.scalars(doctor_query).all()
        matches = []
        for row in rows:
            specialties = row.specialties or []
            if payload.specialty and payload.specialty.casefold() not in [s.casefold() for s in specialties]: continue
            try: user = db.get(AuthUser, UUID(row.user_sub))
            except ValueError: user = None
            slots = (row.availability or {}).get("slots", [])
            available = not payload.preferred_at or any(_slot_matches(slot, payload.preferred_at) for slot in slots)
            matches.append((row, user, available))
        if payload.intent == "find_doctor":
            return {"intent": payload.intent, "organization_id": str(patient.organization_id),
                "doctors": [{"doctor_id": m.user_sub, "name": u.display_name if u else "Clinic doctor",
                "specialties": m.specialties or [], "available_slots": (m.availability or {}).get("slots", [])} for m,u,_ in matches],
                "answer": (f"I found {len(matches)} doctor(s)" if matches else "I could not find a doctor matching that specialty in this clinic.")}
        if payload.preferred_at is None: raise HTTPException(status_code=422, detail="Choose a preferred appointment date and time")
        if payload.preferred_at.tzinfo is None or payload.preferred_at <= datetime.now(timezone.utc):
            raise HTTPException(status_code=422, detail="Choose a future appointment time with a timezone")
        chosen = next(((m,u) for m,u,available in matches if available), None)
        if chosen is None:
            return {"intent": payload.intent, "booked": False, "answer": "No matching doctor has that time available. Please choose one of the available slots shown by the clinic."}
        membership, doctor = chosen
        slots = (membership.availability or {}).get("slots", [])
        selected_slot = next(slot for slot in slots if _slot_matches(slot, payload.preferred_at))
        appointment_data = {"scheduled_at": payload.preferred_at.isoformat(), "visit_type": "Consultation",
            "doctor_id": membership.user_sub, "doctor_name": doctor.display_name if doctor else "Clinic doctor",
            "specialty": payload.specialty, "reason": payload.reason or payload.message, "source": "clinic_chatbot"}
        entry = WorkspaceEntry(resource_type="appointment", organization_id=patient.organization_id,
            patient_id=patient.id, owner_sub=principal.subject, data=appointment_data, status="confirmed",
            created_by=principal.subject, updated_by=principal.subject)
        membership.availability = {**(membership.availability or {}),
            "slots": [slot for slot in slots if not _slot_matches(slot, payload.preferred_at)]}
        db.add(entry); db.flush()
        _audit(db, principal, "chatbot.appointment.book", "appointment", str(entry.id)); db.commit()
        return {"intent": payload.intent, "booked": True, "appointment_id": str(entry.id),
            "doctor": doctor.display_name if doctor else "Clinic doctor", "scheduled_at": selected_slot,
            "status": "confirmed", "answer": f"Your appointment is confirmed with {doctor.display_name if doctor else 'your clinic doctor'} at {selected_slot}."}
    return {"intent": "general", "answer": (org.chatbot_config or {}).get("welcome", "Welcome to your clinic. I can help find a doctor or request an appointment.")}


class PatientEnroll(BaseModel):
    patient_user_id: UUID | None = None
    patient_email: EmailStr | None = None
    display_label: str = Field(default="Patient", min_length=2, max_length=120)


class PatientDoctorConsent(BaseModel):
    organization_id: UUID
    doctor_user_id: UUID
    consent: bool


@router.post("/organizations/{organization_id}/patients", status_code=201)
def enroll_patient(organization_id: UUID, payload: PatientEnroll,
    principal: Principal = Depends(get_current_principal), db: Session = Depends(get_db)) -> dict:
    _organization_admin(db, principal, organization_id)
    org = db.get(Organization, organization_id)
    if not payload.patient_user_id and not payload.patient_email:
        raise HTTPException(status_code=422, detail="Provide a verified patient account ID or email")
    user = db.get(AuthUser, payload.patient_user_id) if payload.patient_user_id else db.scalar(
        select(AuthUser).where(AuthUser.email == str(payload.patient_email).lower()))
    if org is None or org.status != "active" or user is None or user.role != "patient" or not user.is_active or not user.is_verified:
        raise HTTPException(status_code=404, detail="Active verified patient account or clinic not found")
    patient = db.scalar(select(Patient).where(Patient.owner_sub == str(user.id),
        Patient.organization_id == organization_id))
    if patient is None:
        patient = Patient(owner_sub=str(user.id), organization_id=organization_id,
            display_label=payload.display_label.strip())
        db.add(patient); db.flush()
    _audit(db, principal, "organization.patient.enroll", "patient", str(patient.id)); db.commit()
    return {"patient_id": str(patient.id), "organization_id": str(organization_id),
        "patient_name": patient.display_label, "consent_required": True}


@router.post("/clinic/consent")
def grant_doctor_consent(payload: PatientDoctorConsent,
    principal: Principal = Depends(get_current_principal), db: Session = Depends(get_db)) -> dict:
    if "patient" not in principal.roles:
        raise HTTPException(status_code=403, detail="Patient sign-in is required")
    patient = db.scalar(select(Patient).where(Patient.owner_sub == principal.subject,
        Patient.organization_id == payload.organization_id))
    if patient is None:
        raise HTTPException(status_code=404, detail="Clinic patient profile not found")
    doctor_sub = str(payload.doctor_user_id)
    if not payload.consent:
        grant = db.scalar(select(ConsentGrant).where(ConsentGrant.patient_id == patient.id,
            ConsentGrant.grantee_sub == doctor_sub, ConsentGrant.scope == "patient.read"))
        if grant is not None:
            grant.status = "revoked"; grant.revoked_at = datetime.now(timezone.utc)
        relationship = db.scalar(select(CareRelationship).where(CareRelationship.patient_id == patient.id,
            CareRelationship.clinician_sub == doctor_sub, CareRelationship.organization_id == payload.organization_id))
        if relationship is not None:
            relationship.status = "revoked"; relationship.ends_at = datetime.now(timezone.utc)
        _audit(db, principal, "patient.consent.revoke", "patient", str(patient.id)); db.commit()
        return {"consent": "revoked", "doctor_id": doctor_sub, "patient_id": str(patient.id)}
    doctor_membership = db.scalar(select(Membership).where(Membership.user_sub == doctor_sub,
        Membership.organization_id == payload.organization_id, Membership.role == "clinician",
        Membership.status == "active"))
    if doctor_membership is None:
        raise HTTPException(status_code=404, detail="Doctor is not active in this clinic")
    grant = db.scalar(select(ConsentGrant).where(ConsentGrant.patient_id == patient.id,
        ConsentGrant.grantee_sub == doctor_sub, ConsentGrant.scope == "patient.read"))
    if grant is None:
        grant = ConsentGrant(patient_id=patient.id, grantee_sub=doctor_sub,
            scope="patient.read", status="active")
        db.add(grant)
    else:
        grant.status = "active"; grant.revoked_at = None
    relationship = db.scalar(select(CareRelationship).where(CareRelationship.patient_id == patient.id,
        CareRelationship.clinician_sub == doctor_sub, CareRelationship.organization_id == payload.organization_id))
    if relationship is None:
        relationship = CareRelationship(patient_id=patient.id, clinician_sub=doctor_sub,
            organization_id=payload.organization_id, status="active")
        db.add(relationship)
    else:
        relationship.status = "active"; relationship.ends_at = None
    _audit(db, principal, "patient.consent.grant", "patient", str(patient.id)); db.commit()
    return {"consent": "active", "doctor_id": doctor_sub, "patient_id": str(patient.id)}


@router.get("/clinic/me/organization")
def my_organization(principal: Principal = Depends(get_current_principal),
    db: Session = Depends(get_db)) -> dict:
    membership = db.scalar(select(Membership).where(Membership.user_sub == principal.subject,
        Membership.role == "admin", Membership.status == "active").order_by(Membership.created_at.desc()))
    if membership is None:
        raise HTTPException(status_code=404, detail="Active organization administrator membership not found")
    org = db.get(Organization, membership.organization_id)
    if org is None or org.status != "active":
        raise HTTPException(status_code=404, detail="Active organization not found")
    return {"id": str(org.id), "name": org.name, "status": org.status}
