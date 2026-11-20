"""Role-aware navigation and workspace record CRUD endpoints."""
from datetime import datetime, timezone
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.authorization import authorize_patient_read
from app.db import get_db
from app.models import AuthUser, AuditEvent, Membership, Organization, Patient, WorkspaceEntry, WorkspaceMenuItem
from app.security import Principal, get_current_principal, DEMO_ORGANIZATION_ID

router = APIRouter(prefix="/api/v1/workspace", tags=["workspace-management"])
VALID_ROLES = {"patient", "doctor", "admin", "receptionist"}
ROLE_TYPES = {
    "patient": {"appointment_request", "profile_note"},
    "doctor": {"clinical_note", "care_plan", "follow_up"},
    "receptionist": {"appointment", "patient_intake", "check_in"},
    "admin": {"appointment", "patient_intake", "check_in", "department", "clinic_notice"},
}
ROLE_READ_TYPES = {
    "patient": {"appointment_request", "profile_note", "appointment", "clinical_note", "care_plan", "follow_up"},
    "doctor": {"clinical_note", "care_plan", "follow_up"},
    "receptionist": {"appointment", "patient_intake", "check_in", "department"},
    "admin": ROLE_TYPES["admin"],
}
ARCHIVABLE_TYPES = {"appointment", "appointment_request", "patient_intake", "check_in", "department", "clinic_notice"}


def _role(principal: Principal) -> str:
    for role in ("admin", "receptionist", "doctor", "patient"):
        if role in principal.roles or (role == "doctor" and "clinician" in principal.roles):
            return role
    raise HTTPException(status_code=403, detail="A supported workspace role is required")


def _audit(db: Session, principal: Principal, action: str, kind: str, resource_id: str) -> None:
    db.add(AuditEvent(actor_sub=principal.subject, actor_role=",".join(sorted(principal.roles)),
        action=action, resource_type=kind, resource_id=resource_id, outcome="allowed"))


def _staff_org(db: Session, principal: Principal, role: str) -> UUID:
    if principal.is_demo:
        return UUID(principal.organization_id or DEMO_ORGANIZATION_ID)
    membership_role = "clinician" if role == "doctor" else role
    membership = db.scalar(select(Membership).where(
        Membership.user_sub == principal.subject,
        Membership.role == membership_role,
        Membership.status == "active",
    ).order_by(Membership.created_at))
    if membership is None:
        raise HTTPException(status_code=403, detail="An active clinic membership is required")
    if principal.organization_id and str(membership.organization_id) != principal.organization_id:
        raise HTTPException(status_code=403, detail="Active clinic membership is required")
    return membership.organization_id


def _entry_json(row: WorkspaceEntry) -> dict:
    return {"id": str(row.id), "resource_type": row.resource_type,
        "patient_id": str(row.patient_id) if row.patient_id else None,
        "data": row.data, "status": row.status, "created_at": row.created_at.isoformat(),
        "updated_at": row.updated_at.isoformat()}


class MenuCreate(BaseModel):
    key: str = Field(min_length=2, max_length=80, pattern=r"^[a-z0-9][a-z0-9-]*$")
    label: str = Field(min_length=1, max_length=100)
    path: str = Field(min_length=1, max_length=180)
    icon: str = Field(default="layout-dashboard", max_length=60)
    parent_id: UUID | None = None
    roles: list[str] = Field(min_length=1)
    sort_order: int = Field(default=0, ge=0, le=10000)


class MenuUpdate(BaseModel):
    label: str | None = Field(default=None, min_length=1, max_length=100)
    path: str | None = Field(default=None, min_length=1, max_length=180)
    icon: str | None = Field(default=None, max_length=60)
    parent_id: UUID | None = None
    roles: list[str] | None = None
    sort_order: int | None = Field(default=None, ge=0, le=10000)
    is_active: bool | None = None


class EntryCreate(BaseModel):
    resource_type: str = Field(min_length=2, max_length=50, pattern=r"^[a-z][a-z0-9_]*$")
    patient_id: UUID | None = None
    data: dict = Field(default_factory=dict)
    status: str = Field(default="active", min_length=1, max_length=40)


class EntryUpdate(BaseModel):
    data: dict | None = None
    status: str | None = Field(default=None, min_length=1, max_length=40)


@router.get("/menus")
def list_menus(principal: Principal = Depends(get_current_principal),
    db: Session = Depends(get_db)) -> list[dict]:
    role = _role(principal)
    rows = db.scalars(select(WorkspaceMenuItem).where(WorkspaceMenuItem.is_active.is_(True))
        .order_by(WorkspaceMenuItem.sort_order, WorkspaceMenuItem.label)).all()
    return [{"id": str(row.id), "key": row.key, "label": row.label, "path": row.path,
        "icon": row.icon, "parent_id": str(row.parent_id) if row.parent_id else None,
        "roles": row.roles, "sort_order": row.sort_order}
        for row in rows if role in row.roles or "admin" in principal.roles]


@router.post("/menus", status_code=201)
def create_menu(payload: MenuCreate, principal: Principal = Depends(get_current_principal),
    db: Session = Depends(get_db)) -> dict:
    if "admin" not in principal.roles:
        raise HTTPException(status_code=403, detail="Administrator role required")
    if not payload.path.startswith("/") or payload.path.startswith("//"):
        raise HTTPException(status_code=422, detail="Menu path must be an internal application path")
    if any(role not in VALID_ROLES for role in payload.roles):
        raise HTTPException(status_code=422, detail="Menu contains an unsupported role")
    if db.scalar(select(WorkspaceMenuItem).where(WorkspaceMenuItem.key == payload.key)):
        raise HTTPException(status_code=409, detail="Menu key already exists")
    if payload.parent_id and db.get(WorkspaceMenuItem, payload.parent_id) is None:
        raise HTTPException(status_code=404, detail="Parent menu not found")
    row = WorkspaceMenuItem(**payload.model_dump())
    db.add(row)
    db.flush()
    _audit(db, principal, "menu.create", "workspace_menu", str(row.id))
    db.commit()
    return {"id": str(row.id), "key": row.key, "label": row.label}


@router.patch("/menus/{menu_id}")
def update_menu(menu_id: UUID, payload: MenuUpdate,
    principal: Principal = Depends(get_current_principal), db: Session = Depends(get_db)) -> dict:
    if "admin" not in principal.roles:
        raise HTTPException(status_code=403, detail="Administrator role required")
    row = db.get(WorkspaceMenuItem, menu_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Menu item not found")
    changes = payload.model_dump(exclude_unset=True)
    if "path" in changes and (not changes["path"].startswith("/") or changes["path"].startswith("//")):
        raise HTTPException(status_code=422, detail="Menu path must be an internal application path")
    if "roles" in changes and (not changes["roles"] or any(role not in VALID_ROLES for role in changes["roles"])):
        raise HTTPException(status_code=422, detail="Menu contains an unsupported role")
    if changes.get("parent_id") == menu_id:
        raise HTTPException(status_code=422, detail="A menu cannot be its own parent")
    if changes.get("parent_id") and db.get(WorkspaceMenuItem, changes["parent_id"]) is None:
        raise HTTPException(status_code=404, detail="Parent menu not found")
    for key, value in changes.items():
        setattr(row, key, value)
    row.updated_at = datetime.now(timezone.utc)
    _audit(db, principal, "menu.update", "workspace_menu", str(row.id))
    db.commit()
    return {"id": str(row.id), "key": row.key, "label": row.label, "is_active": row.is_active}


@router.delete("/menus/{menu_id}", status_code=204)
def delete_menu(menu_id: UUID, principal: Principal = Depends(get_current_principal),
    db: Session = Depends(get_db)) -> None:
    if "admin" not in principal.roles:
        raise HTTPException(status_code=403, detail="Administrator role required")
    row = db.get(WorkspaceMenuItem, menu_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Menu item not found")
    row.is_active = False
    for child in db.scalars(select(WorkspaceMenuItem).where(WorkspaceMenuItem.parent_id == menu_id)).all():
        child.is_active = False
    _audit(db, principal, "menu.archive", "workspace_menu", str(row.id))
    db.commit()


def _authorize_entry_scope(db: Session, principal: Principal, role: str,
    resource_type: str, patient_id: UUID | None, organization_id: UUID | None = None,
    write: bool = True) -> tuple[UUID | None, str | None]:
    allowed_types = ROLE_TYPES[role] if write else ROLE_READ_TYPES[role]
    if resource_type not in allowed_types:
        raise HTTPException(status_code=403, detail="This role cannot manage this workspace resource")
    if role == "patient":
        patient = db.scalar(select(Patient).where(Patient.owner_sub == principal.subject))
        if patient is None:
            raise HTTPException(status_code=409, detail="Create your patient workspace before adding records")
        if patient_id and patient_id != patient.id:
            raise HTTPException(status_code=404, detail="Patient not found")
        return patient.id, principal.subject
    if role in {"admin", "receptionist"}:
        org_id = _staff_org(db, principal, role)
        if patient_id is None:
            if resource_type in {"patient_intake", "department", "clinic_notice"}:
                return None, None
            raise HTTPException(status_code=422, detail="A patient must be selected for this resource")
        patient = db.get(Patient, patient_id)
        if patient is None or patient.organization_id != org_id:
            raise HTTPException(status_code=404, detail="Patient not found")
        return patient.id, None
    if patient_id is None:
        raise HTTPException(status_code=422, detail="A patient must be selected for this resource")
    patient = authorize_patient_read(db, principal, patient_id)
    return patient.id, None


@router.get("/entries")
def list_entries(resource_type: str = Query(min_length=2, max_length=50),
    patient_id: UUID | None = None, include_archived: bool = False,
    principal: Principal = Depends(get_current_principal), db: Session = Depends(get_db)) -> list[dict]:
    role = _role(principal)
    if role == "patient":
        patient, owner = _authorize_entry_scope(db, principal, role, resource_type, patient_id, write=False)
        query = select(WorkspaceEntry).where(WorkspaceEntry.patient_id == patient,
            WorkspaceEntry.resource_type == resource_type)
    elif role == "doctor":
        patient, _ = _authorize_entry_scope(db, principal, role, resource_type, patient_id, write=False)
        query = select(WorkspaceEntry).where(WorkspaceEntry.patient_id == patient,
            WorkspaceEntry.resource_type == resource_type)
    else:
        org_id = _staff_org(db, principal, role)
        if resource_type not in ROLE_READ_TYPES[role]:
            raise HTTPException(status_code=403, detail="This role cannot view this workspace resource")
        query = select(WorkspaceEntry).where(WorkspaceEntry.organization_id == org_id,
            WorkspaceEntry.resource_type == resource_type)
        if patient_id:
            query = query.where(WorkspaceEntry.patient_id == patient_id)
    if not include_archived:
        query = query.where(WorkspaceEntry.is_archived.is_(False))
    rows = db.scalars(query.order_by(WorkspaceEntry.created_at.desc())).all()
    return [_entry_json(row) for row in rows]


@router.post("/entries", status_code=201)
def create_entry(payload: EntryCreate, principal: Principal = Depends(get_current_principal),
    db: Session = Depends(get_db)) -> dict:
    role = _role(principal)
    patient_id, owner_sub = _authorize_entry_scope(db, principal, role,
        payload.resource_type, payload.patient_id)
    org_id = None
    if role == "patient":
        patient = db.get(Patient, patient_id)
        org_id = patient.organization_id
    elif role == "doctor":
        org_id = db.get(Patient, patient_id).organization_id
    else:
        org_id = _staff_org(db, principal, role)
    row = WorkspaceEntry(resource_type=payload.resource_type, organization_id=org_id,
        patient_id=patient_id, owner_sub=owner_sub, data=payload.data, status=payload.status,
        created_by=principal.subject, updated_by=principal.subject)
    db.add(row)
    db.flush()
    _audit(db, principal, f"{payload.resource_type}.create", payload.resource_type, str(row.id))
    db.commit()
    db.refresh(row)
    return _entry_json(row)


@router.patch("/entries/{entry_id}")
def update_entry(entry_id: UUID, payload: EntryUpdate,
    principal: Principal = Depends(get_current_principal), db: Session = Depends(get_db)) -> dict:
    role = _role(principal)
    row = db.get(WorkspaceEntry, entry_id)
    if row is None or row.is_archived:
        raise HTTPException(status_code=404, detail="Workspace record not found")
    patient_id, owner_sub = _authorize_entry_scope(db, principal, role, row.resource_type, row.patient_id)
    if role == "patient" and row.owner_sub != owner_sub:
        raise HTTPException(status_code=404, detail="Workspace record not found")
    if role in {"admin", "receptionist"} and row.organization_id != _staff_org(db, principal, role):
        raise HTTPException(status_code=404, detail="Workspace record not found")
    changes = payload.model_dump(exclude_unset=True)
    for key, value in changes.items():
        setattr(row, key, value)
    row.updated_by = principal.subject
    row.updated_at = datetime.now(timezone.utc)
    _audit(db, principal, f"{row.resource_type}.update", row.resource_type, str(row.id))
    db.commit()
    db.refresh(row)
    return _entry_json(row)


@router.delete("/entries/{entry_id}", status_code=204)
def archive_entry(entry_id: UUID, principal: Principal = Depends(get_current_principal),
    db: Session = Depends(get_db)) -> None:
    role = _role(principal)
    row = db.get(WorkspaceEntry, entry_id)
    if row is None or row.is_archived:
        raise HTTPException(status_code=404, detail="Workspace record not found")
    if row.resource_type not in ARCHIVABLE_TYPES:
        raise HTTPException(status_code=409, detail="Clinical and legal records cannot be deleted; use an amendment workflow")
    _authorize_entry_scope(db, principal, role, row.resource_type, row.patient_id)
    if role == "patient" and row.owner_sub != principal.subject:
        raise HTTPException(status_code=404, detail="Workspace record not found")
    if role in {"admin", "receptionist"} and row.organization_id != _staff_org(db, principal, role):
        raise HTTPException(status_code=404, detail="Workspace record not found")
    row.is_archived = True
    row.status = "archived"
    row.updated_by = principal.subject
    _audit(db, principal, f"{row.resource_type}.archive", row.resource_type, str(row.id))
    db.commit()


class OrganizationBootstrap(BaseModel):
    name: str = Field(min_length=2, max_length=200)


class MembershipCreate(BaseModel):
    user_id: UUID
    role: str = Field(pattern=r"^(admin|doctor|receptionist)$")


class MembershipUpdate(BaseModel):
    role: str | None = Field(default=None, pattern=r"^(admin|doctor|receptionist)$")
    status: str | None = Field(default=None, pattern=r"^(active|suspended|revoked)$")


@router.post("/organization/bootstrap", status_code=201)
def bootstrap_organization(payload: OrganizationBootstrap,
    principal: Principal = Depends(get_current_principal), db: Session = Depends(get_db)) -> dict:
    if "admin" not in principal.roles:
        raise HTTPException(status_code=403, detail="Administrator role required")
    existing = db.scalar(select(Membership).where(
        Membership.user_sub == principal.subject, Membership.role == "admin",
        Membership.status == "active"))
    if existing:
        organization = db.get(Organization, existing.organization_id)
        return {"organization_id": str(existing.organization_id),
            "organization_name": organization.name if organization else payload.name}
    organization = Organization(name=payload.name.strip(), status="active")
    db.add(organization)
    db.flush()
    db.add(Membership(user_sub=principal.subject, organization_id=organization.id,
        role="admin", status="active"))
    _audit(db, principal, "organization.bootstrap", "organization", str(organization.id))
    db.commit()
    return {"organization_id": str(organization.id), "organization_name": organization.name}


@router.get("/memberships")
def list_memberships(principal: Principal = Depends(get_current_principal),
    db: Session = Depends(get_db)) -> list[dict]:
    if "admin" not in principal.roles:
        raise HTTPException(status_code=403, detail="Administrator role required")
    org_id = _staff_org(db, principal, "admin")
    rows = db.scalars(select(Membership).where(
        Membership.organization_id == org_id).order_by(Membership.created_at.desc())).all()
    result = []
    for row in rows:
        try:
            user = db.get(AuthUser, UUID(row.user_sub))
        except ValueError:
            user = None
        result.append({"id": str(row.id), "user_id": row.user_sub,
            "display_name": user.display_name if user else row.user_sub,
            "email": user.email if user else None, "role": row.role,
            "status": row.status, "created_at": row.created_at.isoformat()})
    return result


@router.post("/memberships", status_code=201)
def create_membership(payload: MembershipCreate,
    principal: Principal = Depends(get_current_principal), db: Session = Depends(get_db)) -> dict:
    if "admin" not in principal.roles:
        raise HTTPException(status_code=403, detail="Administrator role required")
    org_id = _staff_org(db, principal, "admin")
    user = db.get(AuthUser, payload.user_id)
    if user is None or not user.is_verified or not user.is_active:
        raise HTTPException(status_code=404, detail="Active verified user account not found")
    expected_user_role = "doctor" if payload.role == "doctor" else payload.role
    if user.role != expected_user_role:
        raise HTTPException(status_code=409, detail=f"Set the account role to {expected_user_role} before assigning clinic access")
    membership_role = "clinician" if payload.role == "doctor" else payload.role
    row = db.scalar(select(Membership).where(Membership.user_sub == str(user.id),
        Membership.organization_id == org_id))
    if row is None:
        row = Membership(user_sub=str(user.id), organization_id=org_id,
            role=membership_role, status="active")
        db.add(row)
    else:
        row.role = membership_role
        row.status = "active"
    db.flush()
    _audit(db, principal, "membership.assign", "membership", str(row.id))
    db.commit()
    return {"id": str(row.id), "user_id": str(user.id), "role": row.role, "status": row.status}


@router.patch("/memberships/{membership_id}")
def update_membership(membership_id: UUID, payload: MembershipUpdate,
    principal: Principal = Depends(get_current_principal), db: Session = Depends(get_db)) -> dict:
    if "admin" not in principal.roles:
        raise HTTPException(status_code=403, detail="Administrator role required")
    org_id = _staff_org(db, principal, "admin")
    row = db.get(Membership, membership_id)
    if row is None or row.organization_id != org_id:
        raise HTTPException(status_code=404, detail="Membership not found")
    changes = payload.model_dump(exclude_unset=True)
    if changes.get("role") == "doctor":
        changes["role"] = "clinician"
    for key, value in changes.items():
        setattr(row, key, value)
    _audit(db, principal, "membership.update", "membership", str(row.id))
    db.commit()
    return {"id": str(row.id), "role": row.role, "status": row.status}


@router.delete("/memberships/{membership_id}", status_code=204)
def revoke_membership(membership_id: UUID,
    principal: Principal = Depends(get_current_principal), db: Session = Depends(get_db)) -> None:
    if "admin" not in principal.roles:
        raise HTTPException(status_code=403, detail="Administrator role required")
    org_id = _staff_org(db, principal, "admin")
    row = db.get(Membership, membership_id)
    if row is None or row.organization_id != org_id:
        raise HTTPException(status_code=404, detail="Membership not found")
    if row.user_sub == principal.subject and row.role == "admin":
        raise HTTPException(status_code=409, detail="You cannot revoke your own administrator membership")
    row.status = "revoked"
    _audit(db, principal, "membership.revoke", "membership", str(row.id))
    db.commit()
